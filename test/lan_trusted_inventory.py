"""Exercise complete source measurement and the boundary of unruled allowances."""
from contextlib import ExitStack
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("trusted_inventory", ROOT / "dev/trusted-inventory.py")
TRUST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRUST)


class Inventory(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="lanyard-trust-unit-")
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name) / "compiler with spaces"
        for names in TRUST.GROUPS.values():
            for name in names:
                path = self.work / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"(* fixture *)\n")
        (self.work / "dev").mkdir()
        (self.work / "target").mkdir()
        for name in ("trusted-lines.sh", "trusted-inventory.py", "trusted-policy.py", "trusted-policy.json"):
            shutil.copyfile(ROOT / "dev" / name, self.work / "dev" / name)

    def group(self, report, name):
        return next(row for row in report["groups"] if row["name"] == name)

    def shell(self, *arguments):
        return subprocess.run(["zsh", str(self.work / "dev/trusted-lines.sh"),
                               str(self.work), *map(str, arguments)],
                              capture_output=True, timeout=30)

    def cli(self, *arguments):
        return subprocess.run([sys.executable, "-P", str(ROOT / "dev/trusted-inventory.py"),
                               str(self.work), *map(str, arguments)],
                              capture_output=True, timeout=30)

    def test_census_is_disjoint_and_keeps_every_decision_open(self):
        report = TRUST.inventory(self.work)
        names = [row["path"] for row in report["files"]]
        self.assertEqual(names, sorted(set(names)))
        self.assertEqual(len(names), 47)
        grouped = [name for row in report["groups"] for name in row["files"]]
        self.assertEqual(sorted(grouped), names)
        self.assertEqual(report["kernel"], {"lines": 12, "limit": 4000, "passed": True})
        self.assertEqual(report["status"], "PENDING")
        self.assertEqual(report["m0_exit"], "not-stamped")
        for key in ("total", "A_rir", "A_emit", "A_sig"):
            self.assertIsNone(report["ceiling"][key])
        self.assertIn("base growth", report["pending_rulings"])
        for name in ("carried-eraser", "target-bridge", "kernel-support", "frontend", "driver"):
            self.assertEqual(self.group(report, name)["scope"], "pending")

    def test_fusion_bytes_and_lines_join_the_bridge_inventory(self):
        content = b"(* fusion *)\n\nlet first = 1\nlet last = 2"
        (self.work / "surface/fuse.ml").write_bytes(content)
        report = TRUST.inventory(self.work)
        fusion = next(row for row in report["files"] if row["path"] == "surface/fuse.ml")
        self.assertEqual((fusion["lines"], fusion["bytes"]), (3, len(content)))
        self.assertEqual(fusion["sha256"], hashlib.sha256(content).hexdigest())
        self.assertEqual(self.group(report, "target-bridge")["lines"], 5)
        result = self.shell()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"TRUSTED-LINES fusion=3 ", result.stdout)
        self.assertIn(b"TRUSTED-LINES target-bridge-total=5 ", result.stdout)

    def test_new_sources_are_measured_with_unassigned_scope(self):
        for name in ("rust/new_backend.ml", "surface/nested/helper.mli"):
            path = self.work / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b"(* new source *)\n\n")
        report = TRUST.inventory(self.work)
        group = self.group(report, "unassigned")
        self.assertEqual(group["files"], ["rust/new_backend.ml", "surface/nested/helper.mli"])
        self.assertEqual((group["lines"], group["scope"]), (4, "pending"))
        self.assertEqual(len(report["files"]), 49)

    def test_removing_each_required_source_fails(self):
        for names in TRUST.GROUPS.values():
            for name in names:
                with self.subTest(name=name):
                    path = self.work / name
                    original = path.read_bytes()
                    with ExitStack() as restore:
                        restore.callback(path.write_bytes, original)
                        path.unlink()
                        with self.assertRaises((OSError, ValueError)):
                            TRUST.inventory(self.work)

    def test_removing_an_optional_legacy_block_cannot_skip_validation(self):
        for name in ("lib/rir.ml", "rust", "target", "surface/fuse.ml"):
            with self.subTest(name=name):
                path = self.work / name
                saved = self.work / "saved"
                with ExitStack() as restore:
                    path.rename(saved)
                    restore.callback(saved.rename, path)
                    result = self.shell()
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertNotIn(b"TRUSTED-LINES OK", result.stdout.splitlines())

    def test_missing_generated_module_fails(self):
        (self.work / TRUST.GENERATED).unlink()
        result = self.shell()
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(b"TRUSTED-LINES OK", result.stdout.splitlines())

    def test_kernel_bound_passes_at_limit_and_fails_above_it(self):
        path = self.work / "lib/check.ml"
        path.write_bytes(b"\n" * 3989)
        self.assertEqual(TRUST.inventory(self.work)["kernel"]["lines"], 4000)
        self.assertEqual(self.shell().returncode, 0)
        path.write_bytes(b"\n" * 3990)
        output = self.work / "failed.json"
        result = self.shell("--output", output)
        self.assertEqual(result.returncode, 1)
        report = json.loads(output.read_bytes())
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["kernel"]["passed"])

    def test_fifty_printer_lines_change_evidence_without_inventing_a_limit(self):
        before = TRUST.inventory(self.work)
        path = self.work / "rust/emit.ml"
        path.write_bytes(path.read_bytes() + b"(* added *)\n" * 50)
        after = TRUST.inventory(self.work)
        self.assertEqual(self.group(after, "printer")["lines"] - self.group(before, "printer")["lines"], 50)
        self.assertNotEqual(TRUST.encoded(before), TRUST.encoded(after))
        self.assertEqual((after["status"], after["ceiling"]["A_emit"]), ("PENDING", None))

    def test_shell_kernel_roster_must_match_the_inventory(self):
        script = self.work / "dev/trusted-lines.sh"
        script.write_text(script.read_text().replace("$root/lib/check.ml", "$root/lib/shape.ml"))
        with self.assertRaisesRegex(ValueError, "kernel bucket differs"):
            TRUST.inventory(self.work)

    def test_symlinked_sources_directories_and_generated_parents_fail(self):
        for name in ("lib/check.ml", "rust", "_build/default/target"):
            with self.subTest(name=name):
                path = self.work / name
                saved = self.work / "saved"
                with ExitStack() as restore:
                    path.rename(saved)
                    restore.callback(saved.rename, path)
                    path.symlink_to(saved, target_is_directory=saved.is_dir())
                    restore.callback(path.unlink)
                    with self.assertRaisesRegex(ValueError, "symlink|source directory"):
                        TRUST.inventory(self.work)

    def test_nonregular_source_is_rejected_before_reading(self):
        path = self.work / "rust/emit.ml"
        path.unlink()
        os.mkfifo(path)
        with self.assertRaisesRegex(ValueError, "regular file"):
            TRUST.inventory(self.work)
        result = self.shell()
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"regular file", result.stderr)

    def test_output_is_deterministic_and_its_stdout_hash_matches(self):
        first = self.work / "first.json"
        second = self.work / "second.json"
        for path in (first, second):
            result = self.cli("--output", path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest().encode(), result.stdout)
            self.assertIn(b"TRUSTED-INVENTORY PENDING", result.stdout.splitlines())
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_existing_output_and_invalid_options_fail_without_overwriting(self):
        output = self.work / "existing.json"
        output.write_bytes(b"preserve")
        result = self.cli("--output", output)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(output.read_bytes(), b"preserve")
        self.assertEqual(result.stdout, b"")
        self.assertEqual(self.cli("--approve").returncode, 2)

    def test_an_option_in_the_root_slot_is_rejected_before_any_write(self):
        output = self.work / "root-slot.json"
        result = subprocess.run(["zsh", str(self.work / "dev/trusted-lines.sh"),
                                 "--output", str(output)], capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"usage: trusted-lines.sh [ROOT] [--output NEW_JSON]",
                      result.stderr.splitlines())
        self.assertIn(b"TRUSTED-LINES FAIL", result.stdout.splitlines())
        self.assertFalse(output.exists())
        corrected = self.shell("--output", output)
        self.assertEqual(corrected.returncode, 0, corrected.stderr)
        self.assertEqual(json.loads(output.read_bytes())["status"], "PENDING")

    def test_an_unknown_option_fails_the_shell_leg_without_a_write(self):
        before = sorted(path.name for path in self.work.iterdir())
        result = self.shell("--bogus")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"TRUSTED-LINES FAIL", result.stdout.splitlines())
        self.assertEqual(sorted(path.name for path in self.work.iterdir()), before)

    def test_an_absent_output_parent_fails_the_shell_leg_without_a_write(self):
        absent = self.work / "absent"
        result = self.shell("--output", absent / "new.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"TRUSTED-LINES FAIL", result.stdout.splitlines())
        self.assertFalse(absent.exists())

    def script_copy(self):
        """Copy the inventory script into a root that holds no policy code.
        The script loads the policy module from its OWN root, so the copy
        exercises a missing or linked dev/trusted-policy.py."""
        directory = tempfile.TemporaryDirectory(prefix="lanyard-trust-policy-")
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "dev").mkdir()
        shutil.copyfile(ROOT / "dev/trusted-inventory.py", root / "dev/trusted-inventory.py")
        return root

    def test_an_unusable_policy_module_fails_the_report_without_a_traceback(self):
        absent = self.script_copy()
        linked = self.script_copy()
        (linked / "dev/trusted-policy.py").symlink_to(ROOT / "dev/trusted-policy.py")
        for root, fault in ((absent, "missing"), (linked, "symlink")):
            with self.subTest(fault=fault):
                result = subprocess.run(
                    [sys.executable, "-P", str(root / "dev/trusted-inventory.py"), str(self.work)],
                    capture_output=True, timeout=60)
                self.assertEqual(result.returncode, 1)
                self.assertIn(b"TRUSTED-INVENTORY FAIL:", result.stderr)
                self.assertIn(b"dev/trusted-policy.py", result.stderr)
                self.assertNotIn(b"Traceback", result.stderr)
                self.assertEqual(result.stdout, b"")

    @unittest.skipIf(os.geteuid() == 0, "root ignores directory modes")
    def test_an_unreadable_source_directory_fails_the_census(self):
        locked = self.work / "lib/locked"
        locked.mkdir()
        (locked / "extra.ml").write_bytes(b"(* undeclared *)\n")
        output = self.work / "locked.json"
        locked.chmod(0o000)
        self.addCleanup(locked.chmod, 0o755)
        for call in (TRUST.sources, TRUST.inventory):
            with self.subTest(call=call.__name__):
                with self.assertRaises(OSError):
                    call(self.work)
        result = self.cli("--output", output)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"TRUSTED-INVENTORY FAIL:", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
