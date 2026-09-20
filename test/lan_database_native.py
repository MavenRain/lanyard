"""Exercise persisted HTTP state through real offline Cargo and server restarts."""
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
seed = Path(os.environ["LANYARD_DATABASE_SEED"])
for emitted, original in (("Cargo.toml", "Cargo.git.toml"), ("src/main.rs", "src/main.rs")):
    if Path(emitted).read_bytes() != (seed / original).read_bytes():
        sys.exit("database serve emission differs from the checked seed")
for name in ("Cargo.toml", "Cargo.lock"):
    Path(name).write_bytes((seed / name).read_bytes())
cargo = os.environ["LANYARD_DATABASE_CARGO"]
os.execv(cargo, [cargo, *sys.argv[1:], "--locked", "--jobs", "2"])
'''


class NativeDatabase(unittest.TestCase):
    config = None
    restarts = 0
    signal_kinds = set()
    startup_failures = 0
    mutants = 0

    def run_ok(self, *args, timeout=900):
        result = subprocess.run(list(map(str, args)), cwd=ROOT, env=self.env,
                                capture_output=True, timeout=timeout)
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-8000:].decode(errors="replace"))
        return result

    def setUp(self):
        NativeDatabase.restarts = 0
        NativeDatabase.signal_kinds = set()
        NativeDatabase.startup_failures = 0
        temporary = tempfile.TemporaryDirectory(prefix="lanyard-database-native-")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name).resolve()
        self.env = dict(os.environ)
        self.data = self.work / "data"
        self.data.mkdir()
        self.database = self.data / 'store #?% "雪\\\n.sqlite3'
        self.seed = self.work / "seed"
        self.run_ok(sys.executable, "-P", ROOT / "dev/prepare-crate.py", "--output", self.seed,
                    "--source", FIXTURE, "--listen", "127.0.0.1:0", "--database", self.database,
                    "--toasty", self.config.toasty, "--topcoat", self.config.topcoat,
                    "--lock", ROOT / "dev/validation/stage-m1-http/Cargo.lock", timeout=300)
        self.assertFalse(self.database.exists(), "emission opened the database")
        self.build(self.seed)
        self.binary = self.work / "server"
        shutil.copy2(self.config.target / "debug/lanyard-program", self.binary)
        tools = self.work / "tools"
        tools.mkdir()
        shim = tools / "cargo"
        shim.write_text(f"#!{sys.executable}\n" + CARGO)
        shim.chmod(0o755)
        cargo = shutil.which("cargo")
        self.assertIsNotNone(cargo)
        self.serve_env = dict(self.env, PATH=str(tools) + os.pathsep + self.env.get("PATH", ""),
                              CARGO_TARGET_DIR=str(self.config.target), LANYARD_DATABASE_SEED=str(self.seed),
                              LANYARD_DATABASE_CARGO=cargo)

    def build(self, crate):
        self.run_ok("cargocho", "build", "--", "--offline", "--manifest-path", crate / "Cargo.toml",
                    "--target-dir", self.config.target, "--jobs", "2")

    def stop(self, process):
        if process.poll() is None:
            process.kill()
        process.wait(timeout=15)

    def start(self, name, command, cwd, env):
        diagnostics = self.work / f"{name}.stderr"
        output = self.work / f"{name}.stdout"
        err = diagnostics.open("wb")
        out = output.open("wb")
        self.addCleanup(err.close)
        self.addCleanup(out.close)
        process = subprocess.Popen(list(map(str, command)), cwd=cwd, env=env, stdout=out, stderr=err)
        self.addCleanup(self.stop, process)
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            data = diagnostics.read_bytes()
            ready = READY.search(data)
            if ready is not None:
                return process, int(ready[1])
            self.assertIsNone(process.poll(), data[-8000:].decode(errors="replace"))
            time.sleep(0.05)
        self.fail("server readiness timed out: " + diagnostics.read_bytes()[-8000:].decode(errors="replace"))

    def serve(self, name, database, cwd):
        return self.start(name, [CLI, "serve", "--out", self.work / name, "--offline",
                                "--database", database, "--listen", "127.0.0.1:0", FIXTURE],
                          cwd, self.serve_env)

    def request(self, port, method, uri, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        self.addCleanup(connection.close)
        headers = {"content-type": "application/x-www-form-urlencoded"} if body is not None else {}
        connection.request(method, uri, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, response.read()

    def shutdown(self, process, sig=signal.SIGTERM):
        NativeDatabase.signal_kinds.add(sig)
        process.send_signal(sig)
        self.assertEqual(process.wait(timeout=15), 0)

    def test_restart_crud_paths_failures_and_memory_control(self):
        process, port = self.serve("first", self.database.relative_to(self.work), self.work)
        self.assertEqual(self.request(port, "GET", "/init"), (200, b"ready"))
        self.assertEqual(self.request(port, "POST", "/todos/create", "id=3&title=hello"),
                         (200, b"<ul><li>3: hello</li></ul>"))
        self.shutdown(process)
        self.assertTrue(self.database.read_bytes().startswith(b"SQLite format 3\x00"))
        self.assertEqual(list(self.data.iterdir()), [self.database])

        elsewhere = self.work / "elsewhere"
        elsewhere.mkdir()
        NativeDatabase.restarts += 1
        process, port = self.serve("second", self.database, elsewhere)
        self.assertEqual(self.request(port, "GET", "/todos"), (200, b"<ul><li>3: hello</li></ul>"))
        self.assertEqual(self.request(port, "POST", "/todos/update", "id=3&title=kept&completed=true"),
                         (200, b"<ul><li>3: kept (done)</li></ul>"))
        self.shutdown(process, signal.SIGINT)

        NativeDatabase.restarts += 1
        process, port = self.start("direct", [self.binary], elsewhere, self.env)
        self.assertEqual(self.request(port, "GET", "/todos"), (200, b"<ul><li>3: kept (done)</li></ul>"))
        self.assertEqual(self.request(port, "POST", "/todos/delete", "id=3"), (200, b"<ul></ul>"))
        self.shutdown(process)
        NativeDatabase.restarts += 1
        process, port = self.start("deleted", [self.binary], elsewhere, self.env)
        self.assertEqual(self.request(port, "GET", "/todos"), (200, b"<ul></ul>"))
        self.shutdown(process)

        saved = self.database.read_bytes()
        backup = self.work / "backup"
        self.data.rename(backup)
        failed = subprocess.run([self.binary], cwd=elsewhere, env=self.env, capture_output=True, timeout=15)
        self.assertEqual(failed.returncode, 1, failed.stderr)
        self.assertIn(b"server database:", failed.stderr)
        self.assertNotIn(b"LANYARD-LISTEN", failed.stderr)
        NativeDatabase.startup_failures += 1
        self.assertEqual((backup / self.database.name).read_bytes(), saved)
        backup.rename(self.data)

        original = self.seed / "src/main.rs"
        source = original.read_text()
        mutant, count = re.subn(r'\.build\(toasty_driver_sqlite::Sqlite::open\([^\n]*\)\)',
                               '.connect("sqlite::memory:")', source)
        self.assertEqual(count, 1, "persistent driver mutation site drifted")
        NativeDatabase.mutants = count
        original.write_text(mutant)
        self.build(self.seed)
        memory = self.work / "memory-control"
        shutil.copy2(self.config.target / "debug/lanyard-program", memory)
        process, port = self.start("control", [memory], elsewhere, self.env)
        self.assertEqual(self.request(port, "GET", "/todos")[0], 500,
                         "in-memory control unexpectedly retained the existing schema")
        self.assertEqual(self.request(port, "GET", "/init"), (200, b"ready"))
        self.shutdown(process)
        self.assertEqual(self.database.read_bytes(), saved, "memory control changed the database file")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--toasty", type=Path, required=True)
    parser.add_argument("--topcoat", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    config = parser.parse_args()
    config.target = config.target.resolve()
    NativeDatabase.config = config
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeDatabase))
    if not result.wasSuccessful():
        sys.exit(1)
    print(f"LAN-DATABASE NATIVE OK restarts={NativeDatabase.restarts} "
          f"signals={len(NativeDatabase.signal_kinds)} "
          f"startup-failures={NativeDatabase.startup_failures} mutants={NativeDatabase.mutants}")
