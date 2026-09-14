"""Check the build command's process boundary and preflight guarantees."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "_build/default/bin/lanyard.exe"
FIXTURE = ROOT / "test/fixtures/crate.lan"
REPORT = re.compile(r"^LANYARD-BUILD REPORTED cargo_exit=(\d+) cargo_ms=(-?\d+\.\d{3})$",
                    re.MULTILINE)
CARGO = '''import hashlib
import json
import os
from pathlib import Path
import signal
import sys

root = Path.cwd()
record = {"cwd": str(root), "argv": sys.argv[1:], "files": {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in ("Cargo.toml", "src/main.rs")}}
with open(os.environ["LANYARD_BUILD_LOG"], "a") as output:
    output.write(json.dumps(record) + "\\n")
binary = root / "target/debug/lanyard-program"
binary.parent.mkdir(parents=True)
binary.write_text("#!" + sys.executable + "\\nfrom pathlib import Path\\n"
                  + "Path(" + repr(os.environ["LANYARD_RUN_MARKER"]) + ").touch()\\n")
binary.chmod(0o755)
print("cargo output", flush=True)
print("cargo diagnostic", file=sys.stderr, flush=True)
if os.environ.get("LANYARD_CARGO_SIGNAL"):
    os.kill(os.getpid(), signal.SIGTERM)
sys.exit(int(os.environ.get("LANYARD_CARGO_EXIT", "0")))
'''


class Build(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="lanyard-build-")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name).resolve()
        self.tools = self.work / "tools"
        self.tools.mkdir()
        cargo = self.tools / "cargo"
        cargo.write_text(f"#!{sys.executable}\n" + CARGO)
        cargo.chmod(0o755)
        self.log = self.work / "cargo.jsonl"
        self.ran = self.work / "program-ran"
        self.destination = self.work / "output"
        self.env = dict(os.environ, PATH=str(self.tools), LANYARD_BUILD_LOG=str(self.log),
                        LANYARD_RUN_MARKER=str(self.ran))

    def cli(self, *args):
        return subprocess.run([str(CLI), *map(str, args)], cwd=self.work,
                              env=self.env, capture_output=True, text=True, timeout=30)

    def build(self, *flags, source=FIXTURE):
        return self.cli("build", "--out", self.destination, *flags, source)

    def record(self):
        rows = self.log.read_text().splitlines()
        self.assertEqual(len(rows), 1, "Cargo must be invoked exactly once")
        return json.loads(rows[0])

    def report(self, result, code):
        rows = REPORT.findall(result.stderr)
        self.assertEqual(len(rows), 1, result.stderr)
        self.assertEqual(int(rows[0][0]), code)
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertFalse(self.ran.exists(), "build executed the emitted program")

    def refused(self, result, code):
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse(self.log.exists(), "preflight failure invoked Cargo")
        self.assertNotIn("LANYARD-BUILD REPORTED", result.stderr)

    def test_debug_build_compiles_the_exact_emitted_crate(self):
        result = self.build()
        self.report(result, 0)
        self.assertEqual(result.stdout, "cargo output\n")
        self.assertTrue(result.stderr.startswith("cargo diagnostic\n"), result.stderr)
        record = self.record()
        self.assertEqual(record["cwd"], str(self.destination))
        self.assertEqual(record["argv"], ["build"])
        self.assertEqual(record["files"], {
            name: hashlib.sha256((ROOT / "test/goldens/crate" / name).read_bytes()).hexdigest()
            for name in ("Cargo.toml", "src/main.rs")})

    def test_release_and_offline_reach_cargo(self):
        for flags in (("--release",), ("--offline",), ("--offline", "--release")):
            with self.subTest(flags=flags):
                self.destination = self.work / "-".join(flags)
                self.log.unlink(missing_ok=True)
                result = self.build(*flags)
                self.report(result, 0)
                self.assertEqual(set(self.record()["argv"]), {"build", *flags})

    def test_options_can_precede_out(self):
        result = self.cli("build", "--offline", "--out", self.destination,
                          "--release", FIXTURE)
        self.report(result, 0)
        self.assertEqual(self.record()["argv"], ["build", "--release", "--offline"])

    def test_print_model_uses_the_m0_golden(self):
        result = self.build("--print-model", "Todo", source=ROOT / "corpus/m0/todo.lan")
        self.report(result, 0)
        self.assertEqual(self.record()["files"], {
            name: hashlib.sha256((ROOT / "corpus/m0/golden" / name).read_bytes()).hexdigest()
            for name in ("Cargo.toml", "src/main.rs")})

    def test_relative_paths_and_shell_metacharacters_stay_literal(self):
        source = self.work / "source ' $() ; `literal` .lan"
        source.write_bytes(FIXTURE.read_bytes())
        name = "output ' ; touch injected ; $() `literal`"
        result = self.cli("build", "--out", name, source.name)
        self.report(result, 0)
        self.assertEqual(self.record()["cwd"], str(self.work / name))
        self.assertFalse((self.work / "injected").exists())

    def test_cargo_failure_preserves_diagnostics_status_and_crate(self):
        for code in (1, 64, 101, 127):
            with self.subTest(code=code):
                self.destination = self.work / f"exit-{code}"
                self.log.unlink(missing_ok=True)
                self.env["LANYARD_CARGO_EXIT"] = str(code)
                result = self.build()
                self.report(result, code)
                self.assertEqual(result.stdout, "cargo output\n")
                self.assertIn("cargo diagnostic", result.stderr)
                self.record()
                self.assertTrue((self.destination / "Cargo.toml").is_file())
                self.assertTrue((self.destination / "src/main.rs").is_file())

    def test_signalled_cargo_is_unsuccessful(self):
        self.env["LANYARD_CARGO_SIGNAL"] = "1"
        result = self.build()
        # Sys.command uses 255 if the shell is itself terminated. Shells that
        # keep a waiting parent report 128 plus the terminating signal.
        self.assertIn(result.returncode, (255, 128 + signal.SIGTERM))
        self.report(result, 255 if result.returncode == 255 else 128 + signal.SIGTERM)
        self.record()

    def test_missing_cargo_is_reported_and_keeps_the_crate(self):
        (self.tools / "cargo").unlink()
        result = self.build()
        self.report(result, 127)
        # The driver's own report row names cargo, so read the shell
        # diagnostic in what remains after that row is removed.
        self.assertIn("not found", REPORT.sub("", result.stderr))
        self.assertTrue((self.destination / "Cargo.toml").is_file())
        self.assertFalse(self.log.exists())

    def test_usage_errors_never_emit_or_launch(self):
        bad = [(), (FIXTURE,), ("--out",), ("--out", self.destination),
               ("--out", "", FIXTURE), ("--out", "--offline", FIXTURE),
               ("--out", self.destination, "--print-model", FIXTURE),
               ("--out", self.destination, "--print-model", "", FIXTURE),
               ("--out", self.destination, "--print-model", "Todo", "--print-model", "Todo", FIXTURE),
               ("--out", self.destination, "--out", self.destination, FIXTURE),
               ("--out", self.destination, "--release", "--release", FIXTURE),
               ("--out", self.destination, "--offline", "--offline", FIXTURE),
               ("--out", self.destination, "--unknown", FIXTURE),
               ("--out", self.destination, FIXTURE, "--offline"),
               ("--out", self.destination, FIXTURE, FIXTURE),
               ("--out", self.destination, "file.kan"),
               ("--out", self.destination, ".lan")]
        for args in bad:
            with self.subTest(args=args):
                result = self.cli("build", *args)
                self.refused(result, 64)
                self.assertIn("usage: lanyard", result.stderr)
                self.assertFalse(self.destination.exists())
                self.assertFalse(Path(str(self.destination) + ".partial").exists())

    def test_missing_source_does_not_create_output(self):
        result = self.build(source=self.work / "missing.lan")
        self.refused(result, 64)
        self.assertIn("cannot read", result.stderr)
        self.assertFalse(self.destination.exists())

    def test_invalid_source_does_not_create_output(self):
        source = self.work / "invalid.lan"
        source.write_text("def main : Nat := Type 0\n")
        result = self.build(source=source)
        self.refused(result, 1)
        self.assertFalse(self.destination.exists())

    def test_invalid_entry_and_output_model_do_not_create_output(self):
        source = self.work / "no-main.lan"
        source.write_text("def answer : Nat := 42\n")
        checked = self.cli("check", source)
        self.assertEqual((checked.returncode, checked.stdout, checked.stderr), (0, "", ""))
        for flags, fixture in (((), source), (("--print-model", "Missing"), FIXTURE)):
            with self.subTest(flags=flags):
                result = self.build(*flags, source=fixture)
                self.refused(result, 1)
                self.assertFalse(self.destination.exists())

    def test_existing_output_and_partial_are_untouched(self):
        for name in ("output", "output.partial"):
            with self.subTest(name=name):
                occupied = self.work / name
                occupied.mkdir()
                sentinel = occupied / "keep"
                sentinel.write_text("unchanged\n")
                result = self.build()
                self.refused(result, 64)
                self.assertIn("output path exists", result.stderr)
                self.assertEqual(sentinel.read_text(), "unchanged\n")
                self.assertEqual(list(occupied.iterdir()), [sentinel])
                sentinel.unlink()
                occupied.rmdir()

    def test_file_and_dangling_symlink_outputs_are_untouched(self):
        self.destination.write_text("keep\n")
        self.refused(self.build(), 64)
        self.assertEqual(self.destination.read_text(), "keep\n")
        self.destination.unlink()
        self.destination.symlink_to(self.work / "missing")
        self.refused(self.build(), 64)
        self.assertTrue(self.destination.is_symlink())
        self.assertFalse((self.work / "missing").exists())

    def test_missing_parent_refuses_before_cargo(self):
        self.destination = self.work / "missing" / "output"
        result = self.build()
        self.refused(result, 64)
        self.assertIn("output parent is not a directory", result.stderr)
        self.assertFalse(self.destination.parent.exists())

    def test_emit_keeps_its_no_cargo_contract(self):
        result = self.cli("emit", "--crate", self.destination, FIXTURE)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertFalse(self.log.exists())
        self.assertTrue((self.destination / "src/main.rs").is_file())


if __name__ == "__main__":
    unittest.main()
