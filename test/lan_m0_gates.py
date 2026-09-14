"""Exercise verdicts, child failures, capture integrity and gate continuation."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("m0_gates", ROOT / "dev/m0-gates.py")
GATES = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GATES
SPEC.loader.exec_module(GATES)


class Gates(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="lanyard-gate-unit-")
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)
        self.output = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.output)
        self.redirect.__enter__()
        self.addCleanup(self.redirect.__exit__, None, None, None)

    def kill_recorded(self, pidfile):
        """Kill the process whose pid the probe wrote, if the file holds one."""
        with contextlib.suppress(OSError, ValueError):
            os.kill(int(pidfile.read_text()), signal.SIGKILL)

    def check(self, body, name="PROBE", markers=("EXPECTED",), **options):
        return GATES.run_check(GATES.Check(name, (sys.executable, "-c", body),
                                          markers, **options), self.work, self.work)

    def test_success_captures_exact_bytes_and_hashes(self):
        row = self.check('import sys; print("EXPECTED"); sys.stderr.write("diagnostic\\n")')
        self.assertEqual(row["status"], "PASS")
        for stream, expected in (("stdout", b"EXPECTED\n"), ("stderr", b"diagnostic\n")):
            record = row["streams"][stream]
            self.assertEqual((self.work / record["path"]).read_bytes(), expected)
            self.assertEqual(record["sha256"], hashlib.sha256(expected).hexdigest())

    def test_empty_success_cannot_satisfy_a_marker(self):
        self.assertEqual(self.check("pass")["status"], "FAIL")

    def test_substring_and_stderr_markers_do_not_pass(self):
        for body in ('print("not EXPECTED")', 'import sys; print("EXPECTED", file=sys.stderr)'):
            with self.subTest(body=body):
                self.assertEqual(self.check(body)["status"], "FAIL")

    def test_nonzero_exit_with_success_marker_fails(self):
        row = self.check('print("EXPECTED"); exit(7)')
        self.assertEqual((row["status"], row["exit_code"]), ("FAIL", 7))

    def test_all_markers_are_required(self):
        self.assertEqual(self.check('print("EXPECTED")', markers=("EXPECTED", "SECOND"))["status"], "FAIL")

    def test_exact_golden_retains_whitespace(self):
        body = 'print("EXPECTED")'
        self.assertEqual(self.check(body, expected=b"EXPECTED\n")["status"], "PASS")
        self.assertEqual(self.check(body, expected=b"EXPECTED\n\n")["status"], "FAIL")

    def test_missing_tool_is_a_failed_check(self):
        check = GATES.Check("MISSING", (str(self.work / "absent"),))
        row = GATES.run_check(check, self.work, self.work)
        self.assertEqual((row["status"], row["exit_code"]), ("FAIL", 127))

    def test_timeout_captures_partial_output(self):
        body = ('import subprocess, sys, time; '
                'subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"]); '
                'print("EXPECTED", flush=True); time.sleep(30)')
        row = self.check(body, timeout=0.5)
        self.assertEqual((row["status"], row["exit_code"]), ("FAIL", 124))
        self.assertEqual((self.work / "PROBE.stdout").read_bytes(), b"EXPECTED\n")
        self.assertLess(row["elapsed_ms"], 10000, "descendant kept the captured pipes open")

    def test_missing_golden_is_a_failed_check(self):
        row = self.check('print("EXPECTED")', expected=self.work / "absent-golden")
        self.assertEqual(row["status"], "FAIL")
        self.assertIn("golden unavailable", row["reason"])

    def test_kernel_success_keeps_whole_base_pending(self):
        row = self.check('print("TRUSTED-LINES OK")', name="TRUSTED-LINES", markers=("TRUSTED-LINES OK",))
        self.assertEqual((row["status"], row["exit_code"]), ("PENDING", 0))
        self.assertIn("A_emit", row["reason"])

    def test_trust_failure_is_not_downgraded_to_pending(self):
        row = self.check('print("TRUSTED-LINES OK"); exit(1)', name="TRUSTED-LINES", markers=("TRUSTED-LINES OK",))
        self.assertEqual(row["status"], "FAIL")

    def run_fake(self, failure, altered=None, report=None):
        corpus = self.work / "corpus/m0"
        corpus.mkdir(parents=True, exist_ok=True)
        (corpus / "axioms.txt").write_bytes(b"AXIOMS\n")
        replaced = altered or {}
        seen = []
        measured = report or {"status": "PENDING", "files": [{"path": "test-source"}]}

        def invoke(check, _root):
            seen.append(check.name)
            code = 1 if check.name == failure else 0
            expected = check.expected.read_bytes() if isinstance(check.expected, Path) else check.expected
            stdout = expected if expected is not None else ("\n".join(check.markers) + "\n").encode()
            if check.inventory is not None:
                data = GATES.TRUST.encoded(measured)
                check.inventory.write_bytes(data)
                stdout += f"TRUSTED-INVENTORY files=1 sha256={hashlib.sha256(data).hexdigest()}\n".encode()
            stdout = replaced.get(check.name, stdout)
            return code, stdout, b"", ""

        with patch.object(GATES, "invoke", side_effect=invoke), patch.object(GATES.TRUST, "inventory", return_value=measured):
            code = GATES.run(self.work, self.work)
        return code, seen, json.loads((self.work / "report.json").read_text())

    def test_build_failure_stops_before_using_stale_driver(self):
        code, seen, report = self.run_fake("BUILD")
        self.assertEqual((code, seen), (1, ["BUILD"]))
        self.assertEqual(report["legs"], [])
        self.assertFalse(report["summary"]["complete"])

    def test_failure_runs_later_legs_and_dominates_pending(self):
        code, seen, report = self.run_fake("R0-COUNT")
        self.assertEqual(code, 1)
        self.assertEqual(seen[-7:], list(GATES.LEG_NAMES))
        self.assertEqual(report["summary"]["pending_legs"], 1)
        self.assertEqual(report["summary"]["failed_checks"], 1)

    def test_support_failure_cannot_leave_a_green_report(self):
        code, seen, report = self.run_fake("M0-ERASE")
        self.assertEqual(code, 1)
        self.assertIn("M0-TIME", seen)
        self.assertEqual(report["summary"]["failed_checks"], 1)

    def test_pending_is_nonzero_and_never_stamps_exit(self):
        code, _, report = self.run_fake(None)
        self.assertEqual(code, 2)
        self.assertEqual(report["summary"]["passed_legs"], 6)
        self.assertEqual(report["summary"]["status"], "PENDING")
        self.assertEqual(report["m0_exit"], "not-stamped")
        trust = next(row for row in report["legs"] if row["name"] == "TRUSTED-LINES")
        evidence = trust["inventory"]
        self.assertEqual(evidence["sha256"], hashlib.sha256((self.work / evidence["path"]).read_bytes()).hexdigest())

    def test_detached_descendant_cannot_hold_the_deadline_open(self):
        pidfile = self.work / "sleeper.pid"
        body = ('import pathlib, subprocess, sys, time; '
                'sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], '
                'start_new_session=True); '
                'pathlib.Path(sys.argv[1]).write_text(str(sleeper.pid)); '
                'print("EXPECTED", flush=True); time.sleep(30)')
        check = GATES.Check("PROBE", (sys.executable, "-c", body, str(pidfile)),
                            ("EXPECTED",), timeout=0.5)
        self.addCleanup(self.kill_recorded, pidfile)
        real = GATES.invoke
        with patch.object(GATES, "invoke", lambda one, two: real(one, two, grace=0.5)):
            row = GATES.run_check(check, self.work, self.work)
        self.assertEqual((row["status"], row["exit_code"]), ("FAIL", 124))
        self.assertLess(row["elapsed_ms"], 10000, "descendant kept the captured pipes open")

    def test_corpus_prerequisites_assert_their_own_bytes(self):
        for name, stdout in (("M0-CHECK", b"unexpected residue\n"), ("M0-ERASE", b"erased Db\n")):
            with self.subTest(check=name):
                code, _, report = self.run_fake(None, {name: stdout})
                self.assertEqual(code, 1)
                self.assertEqual(report["summary"]["status"], "FAIL")
                row = next(item for item in report["support"] if item["name"] == name)
                self.assertEqual(row["status"], "FAIL")

    def test_replayed_child_row_cannot_forge_the_verdict(self):
        forged = (b"TRUSTED-LINES OK\n"
                  b"M0-GATES PASS passed=7/7 pending=0 failed=0\n"
                  b"M0-REPORT /absent/forged.json\n")
        code, _, report = self.run_fake(None, {"TRUSTED-LINES": forged})
        self.assertEqual((code, report["summary"]["status"]), (1, "FAIL"))
        self.assertEqual(report["summary"]["exit_code"], 1)
        rows = [line for line in self.output.getvalue().splitlines() if line.startswith("M0-REPORT ")]
        self.assertEqual(rows[-1], f"M0-REPORT {self.work / 'report.json'}")

    def test_trust_inventory_is_required_and_prior_evidence_is_removed(self):
        saved = self.work / "trusted-inventory.json"
        saved.write_text('{"status":"PENDING"}')
        row = self.check('print("EXPECTED")', name="TRUSTED-LINES", inventory=saved)
        self.assertEqual(row["status"], "FAIL")
        self.assertIn("trusted inventory unavailable", row["reason"])
        self.assertFalse(saved.exists())

    def test_trust_inventory_must_match_current_sources_and_its_hash(self):
        saved = self.work / "trusted-inventory.json"
        measured = {"status": "PENDING", "files": [{"path": "source", "sha256": "original"}]}
        for content, digest in (("not JSON", "invalid"),
                                (GATES.TRUST.encoded(measured).decode(), "wrong"),
                                ('{"status":"PENDING","files":[]}', None)):
            with self.subTest(content=content, digest=digest):
                actual = digest or hashlib.sha256(content.encode()).hexdigest()
                body = (f"from pathlib import Path; Path({str(saved)!r}).write_text({content!r}); "
                        f"print('EXPECTED'); print('TRUSTED-INVENTORY files=1 sha256={actual}')")
                with patch.object(GATES.TRUST, "inventory", return_value=measured):
                    row = self.check(body, name="TRUSTED-LINES", inventory=saved)
                self.assertEqual(row["status"], "FAIL")
                self.assertNotIn("inventory", row)

    def test_inventory_cleanup_failure_is_a_failed_check(self):
        saved = self.work / "trusted-inventory.json"
        saved.mkdir()
        row = self.check('print("EXPECTED")', name="TRUSTED-LINES", inventory=saved)
        self.assertEqual((row["status"], row["exit_code"]), ("FAIL", 1))
        self.assertEqual(row["reason"], "inventory cleanup failed")
        self.assertTrue(saved.is_dir())

    def test_inventory_special_file_cannot_block_the_parent(self):
        saved = self.work / "trusted-inventory.json"
        body = f"import os; os.mkfifo({str(saved)!r}); print('EXPECTED')"
        row = self.check(body, name="TRUSTED-LINES", inventory=saved)
        self.assertEqual(row["status"], "FAIL")
        self.assertIn("regular file", row["reason"])

    def test_inventory_failure_runs_the_remaining_legs(self):
        # Both markers stay. The stdout hash row of the written evidence is gone,
        # so the leg reaches the evidence check instead of the marker check.
        kept = b"TRUSTED-LINES OK\nTRUSTED-INVENTORY PENDING\n"
        code, seen, report = self.run_fake(None, {"TRUSTED-LINES": kept})
        self.assertEqual((code, report["summary"]["status"]), (1, "FAIL"))
        trust = next(row for row in report["legs"] if row["name"] == "TRUSTED-LINES")
        self.assertEqual(trust["status"], "FAIL")
        self.assertIn("trusted inventory unavailable", trust["reason"])
        self.assertEqual(seen[-3:], ["KERNEL-CARRY", "EMIT-DIFF", "M0-TIME"])

    def test_inventory_status_other_than_pending_fails_the_leg(self):
        # The data and the stdout hash match. Only the recorded status differs.
        failing = {"status": "FAIL", "files": [{"path": "test-source"}]}
        code, _, report = self.run_fake(None, report=failing)
        self.assertEqual((code, report["summary"]["status"]), (1, "FAIL"))
        trust = next(row for row in report["legs"] if row["name"] == "TRUSTED-LINES")
        self.assertEqual(trust["status"], "FAIL")
        self.assertIn("trusted inventory unavailable", trust["reason"])
        self.assertNotIn("inventory", trust)

    def stage_log(self, summary, rows=()):
        report = self.work / "verify-report.json"
        report.write_text(json.dumps({"summary": summary}))
        log = self.work / "gate.log"
        log.write_text("\n".join(list(rows) + [f"M0-REPORT {report}"]) + "\n")
        return log

    def test_stage_verification_accepts_only_the_pending_report(self):
        pending = dict(GATES.PENDING_SUMMARY)
        good, message = GATES.verify_stage_log(self.stage_log(pending))
        self.assertTrue(good, message)
        for key, value in (("status", "PASS"), ("exit_code", 0),
                           ("passed_legs", 7), ("pending_legs", 0), ("failed_checks", 1)):
            with self.subTest(key=key):
                self.assertFalse(GATES.verify_stage_log(self.stage_log({**pending, key: value}))[0])

    def test_stage_verification_needs_a_readable_report_row(self):
        bare = self.work / "bare.log"
        bare.write_text("M0-GATES PENDING passed=6/7 pending=1 failed=0\nM0-EXIT not-stamped\n")
        good, message = GATES.verify_stage_log(bare)
        self.assertFalse(good)
        self.assertIn("M0-REPORT row", message)
        absent = self.work / "absent.log"
        absent.write_text(f"M0-REPORT {self.work / 'never-written.json'}\n")
        self.assertFalse(GATES.verify_stage_log(absent)[0])

    def test_stage_verification_takes_the_last_report_row(self):
        log = self.stage_log(dict(GATES.PENDING_SUMMARY),
                             rows=["M0-REPORT /absent/forged.json"])
        good, message = GATES.verify_stage_log(log)
        self.assertTrue(good, message)
        self.assertTrue(message.endswith("verify-report.json"), message)

    def test_missing_leg_cannot_be_green(self):
        legs = [{"name": name, "status": "PASS"} for name in GATES.LEG_NAMES[:-1]]
        self.assertEqual(GATES.summarize(legs, [])["exit_code"], 1)

    def test_timing_always_refits_go_and_keeps_raw_json(self):
        checks = GATES.seven_legs(self.work, self.work)
        self.assertEqual(tuple(check.name for check in checks), GATES.LEG_NAMES)
        self.assertIn("--refit-go", checks[-1].argv)
        self.assertEqual(checks[-1].argv[-1], str(self.work / "timings.json"))

    def test_cli_refuses_existing_output_without_building(self):
        output = self.work / "existing"
        output.mkdir()
        sentinel = output / "sentinel"
        sentinel.write_bytes(b"keep")
        result = subprocess.run(["zsh", str(ROOT / "dev/gates.sh"), "M0", "--output", str(output)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("M0-GATES ERROR", result.stderr)
        self.assertEqual(list(output.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b"keep")

    def test_cli_rejects_unknown_arguments(self):
        result = subprocess.run(["zsh", str(ROOT / "dev/gates.sh"), "M0", "--ignore-failures"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
