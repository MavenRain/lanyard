"""Exercise approval, exact source scope, budget boundaries and gate evidence."""
from contextlib import ExitStack, redirect_stdout
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


FIXTURE = module("inventory_fixture", "test/lan_trusted_inventory.py")
GATES = module("policy_gates", "dev/m0-gates.py")
TRUST = FIXTURE.TRUST
POLICY_PATH = TRUST.load_policy().PATH


class Policy(unittest.TestCase):
    setUp = FIXTURE.Inventory.setUp
    shell = FIXTURE.Inventory.shell
    cli = FIXTURE.Inventory.cli

    def save(self, policy):
        (self.work / POLICY_PATH).write_bytes(TRUST.encoded(policy))

    def approved(self):
        report = TRUST.inventory(self.work)
        policy = json.loads((self.work / POLICY_PATH).read_bytes())
        policy["status"], policy["ruling"] = "APPROVED", "test fixture user ruling"
        sizes = {row["name"]: row["lines"] for row in report["groups"]}
        for group in policy["groups"]:
            group["limit"] = sizes[group["name"]]
        self.save(policy)
        return policy

    def gate(self):
        output = self.work / "evidence"
        output.mkdir(exist_ok=True)
        check = next(row for row in GATES.seven_legs(self.work, output) if row.name == "TRUSTED-LINES")
        with redirect_stdout(io.StringIO()):
            return GATES.run_check(check, self.work, output)

    def test_checked_in_proposal_cannot_approve_or_stamp_m0(self):
        proposal = json.loads((ROOT / POLICY_PATH).read_bytes())
        self.assertEqual((proposal["status"], proposal["ruling"]), ("PROPOSED", None))
        report = TRUST.inventory(self.work)
        self.assertEqual(report["status"], "PENDING")
        self.assertEqual(self.gate()["status"], "PENDING")
        self.assertEqual(report["m0_exit"], "not-stamped")
        self.assertIsNone(report["ceiling"]["total"])

    def test_exact_approved_budgets_pass_shell_and_real_gate(self):
        self.approved()
        report = TRUST.inventory(self.work)
        self.assertEqual((report["status"], report["policy"]["lines"], report["policy"]["limit"]),
                         ("PASS", 46, 46))
        self.assertEqual(report["pending_rulings"], [])
        self.assertEqual(report["m0_exit"], "not-stamped")
        self.assertEqual(report["ceiling"]["total"], 46)
        self.assertEqual(report["ceiling"]["A_emit"], 8)
        self.assertEqual(self.gate()["status"], "PASS")

    def test_growth_in_every_group_fails_approved_budget(self):
        self.approved()
        for name, names in TRUST.GROUPS.items():
            with self.subTest(group=name), ExitStack() as restore:
                path = self.work / names[0]
                original = path.read_bytes()
                restore.callback(path.write_bytes, original)
                path.write_bytes(original + b"\n")
                report = TRUST.inventory(self.work)
                failed = [row["name"] for row in report["policy"]["checks"] if not row["passed"]]
                self.assertEqual((report["status"], failed), ("FAIL", [name]))
                result = self.shell()
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertNotIn(b"TRUSTED-LINES OK", result.stdout.splitlines())

    def test_group_growth_cannot_borrow_another_groups_headroom(self):
        policy = self.approved()
        next(row for row in policy["groups"] if row["name"] == "rir")["limit"] += 100
        self.save(policy)
        (self.work / "rust/model.ml").write_bytes(b"\n" * 51)
        report = TRUST.inventory(self.work)
        self.assertLess(report["policy"]["lines"], report["policy"]["limit"])
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(self.gate()["status"], "FAIL")

    def test_new_empty_source_fails_approved_scope(self):
        self.approved()
        (self.work / "rust/new_helper.ml").touch()
        report = TRUST.inventory(self.work)
        self.assertEqual(report["status"], "FAIL")
        unassigned = next(row for row in report["policy"]["checks"] if row["name"] == "unassigned")
        self.assertTrue(unassigned["within_limit"])
        self.assertFalse(unassigned["paths_match"])
        self.assertEqual(self.gate()["status"], "FAIL")

    def test_proposal_overrun_stays_pending_with_failed_candidate(self):
        policy = self.approved()
        policy["status"], policy["ruling"] = "PROPOSED", None
        self.save(policy)
        (self.work / "rust/emit.ml").write_bytes(b"\n" * 51)
        report = TRUST.inventory(self.work)
        self.assertEqual(report["status"], "PENDING")
        self.assertFalse(report["policy"]["passed"])
        self.assertEqual(self.gate()["status"], "PENDING")

    def test_excluded_group_stays_in_inventory_with_explicit_reason(self):
        policy = self.approved()
        frontend = next(row for row in policy["groups"] if row["name"] == "frontend")
        frontend.update(scope="excluded", limit=None, reason="fixture output is rechecked")
        self.save(policy)
        (self.work / "surface/elab.ml").write_bytes(b"\n" * 100)
        report = TRUST.inventory(self.work)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["files"]), 46)
        self.assertEqual(report["ceiling"]["total"], 39)
        self.assertTrue(any(row["path"] == "surface/elab.ml" for row in report["files"]))

    def test_kernel_cannot_be_excluded_or_budgeted_above_ratified_bound(self):
        policy = self.approved()
        # A dropped kernel and a relaxed kernel budget report separate reasons.
        faults = (({"scope": "excluded", "limit": None, "reason": "fixture"},
                   "established trusted base"), ({"limit": 4001}, "ratified"))
        for change, expected in faults:
            with self.subTest(change=change):
                changed = copy.deepcopy(policy)
                next(row for row in changed["groups"] if row["name"] == "kernel").update(change)
                self.save(changed)
                with self.assertRaisesRegex(ValueError, expected):
                    TRUST.inventory(self.work)

    def test_excluded_kernel_reports_the_scope_fault_to_the_operator(self):
        policy = self.approved()
        next(row for row in policy["groups"] if row["name"] == "kernel").update(
            scope="excluded", limit=None, reason="fixture")
        self.save(policy)
        result = self.cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"TRUSTED-INVENTORY FAIL: kernel: the established trusted base "
                      b"cannot be excluded", result.stderr)
        self.assertNotIn(b"ratified", result.stderr)

    def test_kernel_limit_still_applies_to_proposals(self):
        (self.work / "lib/check.ml").write_bytes(b"\n" * 4000)
        self.assertEqual(TRUST.inventory(self.work)["status"], "FAIL")

    def test_established_trusted_groups_cannot_be_excluded(self):
        original = self.approved()
        for name in ("erase", "rir", "printer", "signatures"):
            with self.subTest(group=name):
                policy = copy.deepcopy(original)
                group = next(row for row in policy["groups"] if row["name"] == name)
                group.update(scope="excluded", limit=None, reason="fixture")
                self.save(policy)
                with self.assertRaisesRegex(ValueError, "established trusted base"):
                    TRUST.inventory(self.work)

    def test_invalid_policy_fields_fail_before_output_is_written(self):
        original = self.approved()
        cases = [{"format": True}, {"format": 2}, {"status": "PASS"}, {"status": []},
                 {"ruling": None}, {"ruling": " "}, {"groups": {}}, {"extra": 1}]
        for change in cases:
            with self.subTest(change=change):
                self.save(dict(original, **change))
                output = self.work / "rejected.json"
                result = self.shell("--output", output)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertFalse(output.exists())

    def test_invalid_group_fields_are_rejected(self):
        original = self.approved()
        for change in ({"limit": True}, {"limit": -1}, {"limit": 1.5}, {"limit": "8"},
                       {"scope": "automatic"}, {"scope": "excluded", "limit": None},
                       {"files": [False]}, {"name": []}, {"extra": 1}):
            with self.subTest(change=change):
                policy = copy.deepcopy(original)
                policy["groups"][3].update(change)
                self.save(policy)
                with self.assertRaises(ValueError):
                    TRUST.inventory(self.work)

    def test_missing_duplicate_and_unknown_groups_are_rejected(self):
        original = self.approved()
        for groups in (original["groups"][1:], original["groups"] + original["groups"][:1],
                       original["groups"] + [dict(original["groups"][0], name="other")]):
            with self.subTest(groups=len(groups)):
                self.save(dict(original, groups=groups))
                with self.assertRaises(ValueError):
                    TRUST.inventory(self.work)

    def test_policy_path_must_be_present_and_regular(self):
        path = self.work / POLICY_PATH
        path.unlink()
        self.assertEqual(self.shell().returncode, 1)
        path.symlink_to(ROOT / POLICY_PATH)
        self.assertEqual(self.shell().returncode, 1)

    def test_duplicate_keys_and_non_json_numbers_are_rejected(self):
        policy = self.approved()
        data = TRUST.encoded(policy).decode()
        for changed in (data.replace('"format": 1', '"format": 1, "format": 1'),
                        data.replace('"limit": 8', '"limit": NaN')):
            with self.subTest(data=changed[:50]):
                (self.work / POLICY_PATH).write_text(changed)
                with self.assertRaises(ValueError):
                    TRUST.inventory(self.work)

    def test_same_size_policy_change_invalidates_saved_evidence(self):
        self.approved()
        original = GATES.invoke

        def change_after_measurement(check, root):
            result = original(check, root)
            path = self.work / POLICY_PATH
            path.write_bytes(path.read_bytes().replace(b"test fixture user ruling", b"new! fixture user ruling"))
            return result

        with patch.object(GATES, "invoke", side_effect=change_after_measurement):
            row = self.gate()
        self.assertEqual(row["status"], "FAIL")
        self.assertIn("trusted inventory unavailable", row["reason"])


if __name__ == "__main__":
    unittest.main()
