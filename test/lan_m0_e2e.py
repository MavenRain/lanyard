"""Reject false E2E success from failed producers, stale binaries and output drift."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("m0_e2e", ROOT / "dev/m0-e2e.py")
E2E = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E2E)
HOST = "aarch64-apple-darwin"
EXPECTED = b'Todo { id: 1, title: "hi", completed: false }\n'


class EndToEnd(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="lanyard-e2e-unit-")
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)
        self.root = self.work / "root"
        for name in E2E.INPUTS:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        self.target = self.work / "target"
        self.binary = self.target / HOST / "debug/lanyard-program"
        self.calls = []
        self.runs = 0
        self.redirect = contextlib.redirect_stdout(io.StringIO())
        self.redirect.__enter__()
        self.addCleanup(self.redirect.__exit__, None, None, None)

    def pin(self, name):
        return json.loads((self.root / "target/PIN.json").read_text())["libraries"][name]["commit"]

    def invoke(self, check, root):
        self.calls.append(check)
        if check.name.endswith("-HEAD"):
            return 0, self.pin(check.name.split("-")[0].lower()).encode() + b"\n", b"", ""
        if check.name.endswith("-STATUS"):
            return 0, b"", b"", ""
        if check.name == "BUILD":
            return 0, b"OK build: 0 errors, 0 warnings\n", b"", ""
        if check.name == "PREPARE":
            crate = Path(check.argv[-1])
            shutil.copytree(self.root / "corpus/m0/golden", crate)
            shutil.copyfile(crate / "Cargo.toml", crate / "Cargo.git.toml")
            shutil.copyfile(self.root / E2E.LOCK, crate / "Cargo.lock")
            return 0, f"CRATE-PREPARE OK manifest={crate / 'Cargo.toml'}\n".encode(), b"", ""
        if check.name == "RUSTC":
            return 0, f"rustc test\nhost: {HOST}\n".encode(), b"", ""
        if check.name == "CARGO-BUILD":
            self.binary.parent.mkdir(parents=True, exist_ok=True)
            self.binary.write_bytes(b"fresh executable")
        return 0, EXPECTED if check.name == "RUN" else b"", b"", ""

    def gate(self, invoke=None):
        self.runs += 1
        output = self.work / f"run-{self.runs}"
        output.mkdir()
        self.calls.clear()
        with patch.object(E2E.CHECKS, "invoke", side_effect=invoke or self.invoke):
            code = E2E.run(self.root, output, self.work / "toasty", self.work / "topcoat",
                           self.target, "1.98", 2)
        return code, json.loads((output / "report.json").read_text()), output

    def test_complete_run_preserves_inputs_and_output_bytes(self):
        code, report, output = self.gate()
        self.assertEqual(code, 0)
        self.assertEqual(report["summary"]["status"], "PASS")
        self.assertEqual(report["m0_exit"], "not-stamped")
        self.assertEqual((output / "program.expected").read_bytes(), EXPECTED)
        self.assertEqual((output / "RUN.stdout").read_bytes(), EXPECTED)
        for name in ("toasty", "topcoat"):
            self.assertEqual(report["libraries"][name]["commit"], self.pin(name))
        for row in report["checks"]:
            for stream in row["streams"].values():
                self.assertEqual(hashlib.sha256((output / stream["path"]).read_bytes()).hexdigest(),
                                 stream["sha256"])

    def test_failed_producer_never_runs_a_stale_executable(self):
        self.binary.parent.mkdir(parents=True)
        self.binary.write_bytes(b"old executable")
        for name in ("BUILD", "PREPARE", "CRATE-INIT", "CRATE-INDEX", "RUSTC", "CARGO-BUILD"):
            def fail(check, root):
                result = self.invoke(check, root)
                return (7, result[1], b"failed\n", "") if check.name == name else result
            with self.subTest(name=name):
                code, report, output = self.gate(fail)
                self.assertEqual(code, 1)
                self.assertEqual(report["checks"][-1]["exit_code"], 7)
                self.assertNotIn("RUN", [check.name for check in self.calls])
                self.assertFalse((output / "RUN.stdout").exists())

    def test_empty_build_success_fails_before_preparation(self):
        def silent(check, root):
            result = self.invoke(check, root)
            return (0, b"", b"", "") if check.name == "BUILD" else result
        code, report, _ = self.gate(silent)
        self.assertEqual(code, 1)
        self.assertEqual(len(report["checks"]), 1)

    def test_wrong_stdout_stderr_and_exit_are_failures(self):
        for result in ((0, b"", b"", ""), (0, EXPECTED + EXPECTED, b"", ""),
                       (0, EXPECTED.rstrip(), b"", ""), (0, EXPECTED, b"error\n", ""),
                       (9, EXPECTED, b"", ""), (124, EXPECTED, b"", "deadline exceeded")):
            def altered(check, root):
                original = self.invoke(check, root)
                return result if check.name == "RUN" else original
            with self.subTest(result=result):
                code, report, _ = self.gate(altered)
                self.assertEqual(code, 1)
                self.assertEqual(report["checks"][-1]["status"], "FAIL")

    def test_missing_binary_after_successful_build_fails(self):
        def absent(check, root):
            result = self.invoke(check, root)
            if check.name == "CARGO-BUILD":
                self.binary.unlink()
            return result
        code, report, _ = self.gate(absent)
        self.assertEqual(code, 1)
        self.assertIn("lanyard-program", report["summary"]["error"])
        self.assertNotIn("RUN", [check.name for check in self.calls])

    def test_prepared_drift_stops_before_cargo(self):
        for name in ("src/main.rs", "Cargo.git.toml", "Cargo.lock", "extra.txt"):
            def drift(check, root):
                result = self.invoke(check, root)
                if check.name == "PREPARE":
                    with (Path(check.argv[-1]) / name).open("ab") as source:
                        source.write(b"\n")
                return result
            with self.subTest(name=name):
                code, report, _ = self.gate(drift)
                self.assertEqual(code, 1)
                self.assertIn("differs", report["summary"]["error"])
                self.assertNotIn("CARGO-BUILD", [check.name for check in self.calls])
                if name == "extra.txt":
                    self.assertIn("extra.txt", report["summary"]["error"])

    def test_unexpected_golden_file_stops_the_run(self):
        (self.root / "corpus/m0/golden/.DS_Store").write_bytes(b"\x00")
        code, report, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn(".DS_Store", report["summary"]["error"])
        self.assertNotIn("CARGO-BUILD", [check.name for check in self.calls])

    def test_build_cannot_rewrite_the_prepared_source(self):
        def rewrite(check, root):
            result = self.invoke(check, root)
            if check.name == "CARGO-BUILD":
                manifest = Path(check.argv[check.argv.index("--manifest-path") + 1])
                (manifest.parent / "src/main.rs").write_text("changed")
            return result
        code, report, _ = self.gate(rewrite)
        self.assertEqual(code, 1)
        self.assertIn("changed during its build", report["summary"]["error"])

    def test_inputs_cannot_change_during_validation(self):
        def rewrite(check, root):
            result = self.invoke(check, root)
            if check.name == "RUN":
                (root / "corpus/m0/todo.lan").write_text("changed")
            return result
        code, report, _ = self.gate(rewrite)
        self.assertEqual(code, 1)
        self.assertIn("inputs changed", report["summary"]["error"])

    def test_invalid_host_never_starts_cargo(self):
        for stdout in (b"", b"host: ../../escape\n", b"host: ..\n",
                       f"host: {HOST}\nhost: {HOST}\n".encode()):
            def invalid(check, root):
                result = self.invoke(check, root)
                return (0, stdout, b"", "") if check.name == "RUSTC" else result
            with self.subTest(stdout=stdout):
                code, report, _ = self.gate(invalid)
                self.assertEqual(code, 1)
                self.assertIn("one host target", report["summary"]["error"])
                self.assertNotIn("CARGO-BUILD", [check.name for check in self.calls])

    def test_real_preparer_rejects_wrong_pin_before_emission(self):
        destination = self.work / "wrong-pin"
        result = subprocess.run([sys.executable, "-P", str(ROOT / "dev/prepare-crate.py"),
                                 "--toasty", str(ROOT), "--topcoat", str(ROOT),
                                 "--output", str(destination)], capture_output=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"toasty pin differs", result.stderr)
        self.assertFalse(destination.exists())

    def test_cli_rejects_reused_output_and_invalid_arguments(self):
        command = ["zsh", str(ROOT / "dev/gates.sh"), "M0-E2E"]
        cases = (([], 2, b""),
                 (["--toasty", str(ROOT), "--topcoat", str(ROOT), "--jobs", "0"], 2, b""),
                 (["--toasty", str(ROOT), "--topcoat", str(ROOT), "--output", str(self.work)],
                  1, b"M0-E2E ERROR"))
        for args, code, marker in cases:
            with self.subTest(args=args):
                result = subprocess.run(command + args, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, code)
                self.assertIn(marker, result.stderr)
                self.assertNotIn(b"M0-E2E PASS", result.stdout)
                self.assertFalse((self.work / "report.json").exists())

    def test_relative_paths_resolve_against_the_repository_root(self):
        recorded = {}

        def record(root, output, toasty, topcoat, target, toolchain, jobs):
            recorded.update(root=root, output=output, target=target)
            return 0

        elsewhere = self.work / "elsewhere"
        elsewhere.mkdir()
        (self.root / "rel").mkdir()
        argv = ["m0-e2e", "--toasty", str(self.work), "--topcoat", str(self.work),
                "--output", "rel/out", "--target-dir", "rel/cache"]
        self.addCleanup(os.chdir, Path.cwd())
        with patch.object(E2E, "ROOT", self.root), patch.object(E2E, "run", record), \
                patch.object(sys, "argv", argv):
            os.chdir(elsewhere)
            code = E2E.main()
        self.assertEqual(code, 0)
        self.assertEqual(recorded["output"], (self.root / "rel/out").resolve())
        self.assertEqual(recorded["target"], (self.root / "rel/cache").resolve())
        self.assertTrue((self.root / "rel/out").is_dir())

    def test_pin_file_without_a_library_commit_stops_the_run(self):
        pins = json.loads((self.root / "target/PIN.json").read_text())
        pins["libraries"].pop("topcoat")
        (self.root / "target/PIN.json").write_text(json.dumps(pins))
        code, report, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("PIN.json", report["summary"]["error"])
        self.assertIn("topcoat", report["summary"]["error"])
        self.assertEqual(self.calls, [])

    def test_library_head_must_match_its_pin(self):
        def wrong(check, root):
            if check.name == "TOPCOAT-HEAD":
                self.calls.append(check)
                return 0, b"f" * 40 + b"\n", b"", ""
            return self.invoke(check, root)
        code, report, _ = self.gate(wrong)
        self.assertEqual(code, 1)
        self.assertIn("differs from its pin", report["summary"]["error"])
        self.assertNotIn("BUILD", [check.name for check in self.calls])

    def test_moved_library_during_the_build_never_runs_the_program(self):
        heads = []

        def moved(check, root):
            result = self.invoke(check, root)
            heads.append(check.name)
            if check.name == "TOASTY-HEAD" and heads.count("TOASTY-HEAD") > 1:
                return 0, b"0" * 40 + b"\n", b"", ""
            return result
        code, report, _ = self.gate(moved)
        self.assertEqual(code, 1)
        self.assertIn("toasty changed during its build", report["summary"]["error"])
        self.assertNotIn("RUN", [check.name for check in self.calls])

    def test_dirty_library_after_the_build_never_runs_the_program(self):
        states = []

        def dirtied(check, root):
            result = self.invoke(check, root)
            states.append(check.name)
            if check.name == "TOPCOAT-STATUS" and states.count("TOPCOAT-STATUS") > 1:
                return 0, b" M src/lib.rs\n", b"", ""
            return result
        code, report, _ = self.gate(dirtied)
        self.assertEqual(code, 1)
        self.assertIn("topcoat changed during its build", report["summary"]["error"])
        self.assertNotIn("RUN", [check.name for check in self.calls])

    def test_git_steps_ignore_the_operator_configuration(self):
        _, _, output = self.gate()
        argv = {check.name: [str(part) for part in check.argv] for check in self.calls}
        crate = output / "crate"
        home = self.work / "hostile"
        home.mkdir()
        (home / "ignore").write_text("Cargo.lock\n")
        (home / "gitconfig").write_text(f"[core]\n\texcludesFile = {home / 'ignore'}\n")
        environment = {"PATH": os.environ.get("PATH", ""), "HOME": str(home),
                       "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(home / "gitconfig")}
        for name in ("CRATE-INIT", "CRATE-INDEX"):
            with self.subTest(name=name):
                result = subprocess.run(argv[name], capture_output=True, env=environment, timeout=60)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(result.stderr, b"")
        listed = subprocess.run(["git", "-C", str(crate), "ls-files"], capture_output=True,
                                env=environment, timeout=60)
        self.assertEqual(listed.returncode, 0)
        self.assertEqual(sorted(listed.stdout.decode().split()), sorted(E2E.CRATE_FILES))

    def test_real_child_stderr_is_checked_without_normalization(self):
        check = E2E.CHECKS.Check("CHILD", (sys.executable, "-c", "import sys; sys.stderr.write('x')"),
                                 expected=b"", expected_stderr=b"")
        row = E2E.CHECKS.run_check(check, self.work, self.work)
        self.assertEqual(row["status"], "FAIL")
        self.assertEqual((self.work / "CHILD.stderr").read_bytes(), b"x")


if __name__ == "__main__":
    unittest.main()
