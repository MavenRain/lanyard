"""Exercise serve preflight and process replacement without compiling Rust."""
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "_build/default/bin/lanyard.exe"
FIXTURE = ROOT / "test/fixtures/todo-session.lan"
ADDRESS = "127.0.0.1:0"
CARGO = '''import hashlib
import json
import os
from pathlib import Path
import signal
import sys

def stop(signum, frame):
    print("server stopped", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
record = {"pid": os.getpid(), "cwd": str(Path.cwd()), "argv": sys.argv[1:],
          "target": os.environ.get("CARGO_TARGET_DIR"), "files": {
              name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
              for name in ("Cargo.toml", "src/main.rs")}}
Path(os.environ["LANYARD_SERVE_LOG"]).write_text(json.dumps(record))
print("cargo output", flush=True)
print("cargo diagnostic", file=sys.stderr, flush=True)
if os.environ.get("LANYARD_SERVE_WAIT"):
    signal.pause()
if os.environ.get("LANYARD_SERVE_STDIN"):
    print(sys.stdin.read(), end="", flush=True)
sys.exit(int(os.environ.get("LANYARD_SERVE_EXIT", "0")))
'''


class Serve(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="lanyard-serve-")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name).resolve()
        self.tools = self.work / "tools"
        self.tools.mkdir()
        self.cargo = self.tools / "cargo"
        self.cargo.write_text(f"#!{sys.executable}\n" + CARGO)
        self.cargo.chmod(0o755)
        self.log = self.work / "cargo.json"
        self.destination = self.work / "output"
        self.env = dict(os.environ, PATH=str(self.tools),
                        PYTHONSAFEPATH="1", LANYARD_SERVE_LOG=str(self.log))

    def args(self, *flags, source=FIXTURE):
        return [str(CLI), "serve", "--out", str(self.destination),
                "--listen", ADDRESS, *map(str, flags), str(source)]

    def run_cli(self, args, **kwargs):
        return subprocess.run(args, cwd=self.work, env=self.env,
                              capture_output=True, text=True, timeout=30, **kwargs)

    def refused(self, args, code=64):
        result = self.run_cli(args)
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse(self.log.exists(), "refused command invoked Cargo")
        self.assertFalse(self.destination.exists(), "refused command published a crate")
        self.assertFalse(Path(str(self.destination) + ".partial").exists())

    def test_emits_the_same_http_crate_and_executes_cargo_run(self):
        target = self.work / "custom target"
        self.env["CARGO_TARGET_DIR"] = str(target)
        result = self.run_cli(self.args("--offline", "--release"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "cargo output\n")
        self.assertEqual(result.stderr, "cargo diagnostic\n")
        record = json.loads(self.log.read_text())
        self.assertEqual(record["cwd"], str(self.destination))
        self.assertEqual(record["argv"], ["run", "--release", "--offline"])
        self.assertEqual(record["target"], str(target))
        emitted = self.work / "emitted"
        plain = self.run_cli([str(CLI), "emit", "--crate", str(emitted),
                              "--listen", ADDRESS, str(FIXTURE)])
        self.assertEqual(plain.returncode, 0, plain.stderr)
        for name, digest in record["files"].items():
            self.assertEqual(hashlib.sha256((emitted / name).read_bytes()).hexdigest(), digest)

    def test_option_order_and_shell_metacharacters_in_paths(self):
        self.destination = self.work / "output ' $(touch INJECTED); space"
        source = self.work / "source ' $(touch INJECTED); space.lan"
        source.write_bytes(FIXTURE.read_bytes())
        result = self.run_cli([str(CLI), "serve", "--offline", "--listen", ADDRESS,
                               "--out", str(self.destination), str(source)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.log.read_text())["cwd"], str(self.destination))
        self.assertFalse((self.work / "INJECTED").exists())
        self.assertFalse((self.destination / "INJECTED").exists())

    def test_inherits_stdin_and_exit_status(self):
        self.env["LANYARD_SERVE_STDIN"] = "1"
        self.env["LANYARD_SERVE_EXIT"] = "101"
        result = self.run_cli(self.args(), input="input reaches Cargo\n")
        self.assertEqual(result.returncode, 101, result.stderr)
        self.assertEqual(result.stdout, "cargo output\ninput reaches Cargo\n")
        self.assertEqual(result.stderr, "cargo diagnostic\n")
        self.assertTrue((self.destination / "src/main.rs").is_file())

    def test_process_replacement_delivers_shutdown_signals(self):
        self.env["LANYARD_SERVE_WAIT"] = "1"
        for sig in (signal.SIGTERM, signal.SIGINT):
            with self.subTest(signal=sig):
                self.destination = self.work / f"signal-{sig}"
                process = subprocess.Popen(self.args(), cwd=self.work, env=self.env,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           text=True)
                self.addCleanup(self.stop, process)
                with selectors.DefaultSelector() as ready:
                    ready.register(process.stdout, selectors.EVENT_READ)
                    self.assertTrue(ready.select(10), "Cargo did not start")
                self.assertEqual(process.stdout.readline(), "cargo output\n")
                self.assertEqual(json.loads(self.log.read_text())["pid"], process.pid)
                process.send_signal(sig)
                out, err = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 0, err)
                self.assertEqual(out, "server stopped\n")

    def stop(self, process):
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)

    def test_missing_or_unexecutable_cargo(self):
        for mode, code in ((None, 127), (0o644, 126)):
            with self.subTest(mode=mode):
                self.destination = self.work / f"cargo-{code}"
                if mode is None:
                    self.cargo.unlink()
                else:
                    self.cargo.write_text("#!/bin/sh\nexit 0\n")
                    self.cargo.chmod(mode)
                result = self.run_cli(self.args())
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertIn("cargo", result.stderr)
                self.assertTrue((self.destination / "Cargo.toml").is_file())
                self.assertFalse(self.log.exists())

    def test_invalid_options_precede_source_io(self):
        absent = str(self.work / "absent.lan")
        prefix = [str(CLI), "serve", "--out", str(self.destination)]
        invalid = [[], ["--listen", "0.0.0.0:3000"], ["--listen", "127.0.0.1:65536"],
                   ["--listen", "127.0.0.1:999999999999999999999999999999"],
                   ["--listen", ADDRESS, "--listen", ADDRESS],
                   ["--listen", ADDRESS, "--requests", "absent.requests"],
                   ["--requests", "absent.requests", "--listen", ADDRESS],
                   ["--listen", ADDRESS, "--print-model", "Todo"],
                   ["--print-model", "Todo", "--listen", ADDRESS],
                   ["--listen", ADDRESS, "--steps", "10"],
                   ["--listen", ADDRESS, "--offline", "--offline"],
                   ["--listen", ADDRESS, "--release", "--release"],
                   ["--listen", ADDRESS, "--out", str(self.destination)],
                   ["--listen", ADDRESS, "--unknown"], ["--listen", ""]]
        for flags in invalid:
            with self.subTest(flags=flags):
                result = self.run_cli([*prefix, *flags, absent])
                self.assertEqual(result.returncode, 64, result.stderr)
                self.assertTrue(result.stderr.startswith("usage:"), result.stderr)
                self.assertFalse(self.destination.exists())
                self.assertFalse(self.log.exists())
        self.refused([str(CLI), "serve", "--listen", ADDRESS, absent])
        self.refused(prefix + ["--listen", ADDRESS])
        self.refused(self.args("extra.lan"))

    def test_source_and_output_preflight(self):
        self.refused(self.args(source=self.work / "missing.lan"))
        self.refused(self.args(source=self.work / "wrong.txt"))
        bad = self.work / "bad.lan"
        bad.write_text("def main : Nat = false\n")
        self.refused(self.args(source=bad), 1)
        self.refused(self.args(source=ROOT / "test/fixtures/crate.lan"), 1)
        self.destination = self.work / "missing" / "output"
        self.refused(self.args())

    def test_existing_outputs_and_partial_paths_are_preserved(self):
        self.destination.mkdir()
        sentinel = self.destination / "keep"
        sentinel.write_text("untouched")
        result = self.run_cli(self.args())
        self.assertEqual(result.returncode, 64, result.stderr)
        self.assertEqual(sentinel.read_text(), "untouched")
        self.assertFalse(self.log.exists())
        self.destination = self.work / "symlink"
        self.destination.symlink_to(self.work / "absent")
        result = self.run_cli(self.args())
        self.assertEqual(result.returncode, 64, result.stderr)
        self.assertTrue(self.destination.is_symlink())
        self.assertFalse(self.log.exists())
        self.destination = self.work / "with-partial"
        partial = Path(str(self.destination) + ".partial")
        partial.mkdir()
        result = self.run_cli(self.args())
        self.assertEqual(result.returncode, 64, result.stderr)
        self.assertTrue(partial.is_dir())
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
