"""Run serve through real Cargo with verified local copies of the target pins."""
import argparse
import http.client
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "_build/default/bin/lanyard.exe"
FIXTURE = ROOT / "test/fixtures/todo-session.lan"
READY = re.compile(rb"^LANYARD-LISTEN http://127\.0\.0\.1:([0-9]+)\n", re.MULTILINE)
CARGO = '''import os
from pathlib import Path
import sys

seed = Path(os.environ["LANYARD_SERVE_SEED"])
for emitted, prepared in (("Cargo.toml", "Cargo.git.toml"), ("src/main.rs", "src/main.rs")):
    if Path(emitted).read_bytes() != (seed / prepared).read_bytes():
        sys.exit("LAN-SERVE FAIL emitted crate differs from the checked native seed")
for name in ("Cargo.toml", "Cargo.lock"):
    Path(name).write_bytes((seed / name).read_bytes())
cargo = os.environ["LANYARD_SERVE_CARGO"]
os.execv(cargo, [cargo, *sys.argv[1:], "--locked", "--jobs", "2"])
'''


class NativeServe(unittest.TestCase):
    seed = None
    target = None

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="lanyard-serve-native-")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name).resolve()
        tools = self.work / "tools"
        tools.mkdir()
        shim = tools / "cargo"
        shim.write_text(f"#!{sys.executable}\n" + CARGO)
        shim.chmod(0o755)
        cargo = shutil.which("cargo")
        self.assertIsNotNone(cargo, "Cargo is required for the native serve test")
        self.env = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ.get("PATH", ""),
                        CARGO_TARGET_DIR=str(self.target), LANYARD_SERVE_SEED=str(self.seed),
                        LANYARD_SERVE_CARGO=cargo, PYTHONSAFEPATH="1")

    def stop(self, process):
        if process.poll() is None:
            process.kill()
        process.wait(timeout=15)

    def start(self, name):
        diagnostics = self.work / f"{name}.stderr"
        output = self.work / f"{name}.stdout"
        err = diagnostics.open("wb")
        out = output.open("wb")
        self.addCleanup(err.close)
        self.addCleanup(out.close)
        process = subprocess.Popen([str(CLI), "serve", "--out", str(self.work / name),
                                    "--offline", "--listen", "127.0.0.1:0", str(FIXTURE)],
                                   env=self.env, cwd=self.work, stdout=out, stderr=err)
        self.addCleanup(self.stop, process)
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            data = diagnostics.read_bytes()
            ready = READY.search(data)
            if ready is not None:
                return process, int(ready[1]), output, diagnostics
            self.assertIsNone(process.poll(), data[-8000:].decode(errors="replace"))
            time.sleep(0.05)
        self.fail("serve did not start within 300 seconds: "
                  + diagnostics.read_bytes()[-8000:].decode(errors="replace"))

    def request(self, port, method, uri, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        self.addCleanup(connection.close)
        headers = {"content-type": "application/x-www-form-urlencoded"} if body is not None else {}
        connection.request(method, uri, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, response.read()

    def test_todo_requests_shutdown_and_fresh_restart(self):
        for sig in (signal.SIGTERM, signal.SIGINT):
            with self.subTest(signal=sig):
                process, port, output, diagnostics = self.start(f"server-{sig}")
                self.assertEqual(self.request(port, "GET", "/init"), (200, b"ready"))
                self.assertEqual(self.request(port, "GET", "/todos"), (200, b"<ul></ul>"))
                self.assertEqual(self.request(port, "POST", "/todos/create", "id=3&title=hello"),
                                 (200, b"<ul><li>3: hello</li></ul>"))
                self.assertEqual(self.request(port, "GET", "/todos"),
                                 (200, b"<ul><li>3: hello</li></ul>"))
                process.send_signal(sig)
                process.wait(timeout=15)
                self.assertEqual(process.returncode, 0, diagnostics.read_text()[-8000:])
                self.assertEqual(output.read_bytes(), b"")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    NativeServe.seed = args.seed.resolve()
    NativeServe.target = args.target.resolve()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeServe))
    if not result.wasSuccessful():
        sys.exit(1)
    print("LAN-SERVE NATIVE OK lifecycle=2 signals=2")
