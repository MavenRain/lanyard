"""Check database option preflight and propagation without running Cargo."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "_build/default/bin/lanyard.exe"
FIXTURE = ROOT / "test/fixtures/todo-session.lan"
ADDRESS = "127.0.0.1:0"


class DatabaseCli(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="lanyard-database-cli-")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name).resolve()
        tools = self.work / "tools"
        tools.mkdir()
        cargo = tools / "cargo"
        cargo.write_text(f"#!{sys.executable}\nfrom pathlib import Path\n"
                         "Path('cargo-called').write_text('called')\n")
        cargo.chmod(0o755)
        self.env = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ.get("PATH", ""))

    def run_cli(self, *args):
        return subprocess.run([str(CLI), *map(os.fspath, args)], cwd=self.work,
                              env=self.env, capture_output=True, timeout=30)

    def test_invalid_options_precede_source_and_output_io(self):
        for command, output in (("emit", "--crate"), ("build", "--out"), ("serve", "--out")):
            for flags in (["--database", "db"],
                          ["--listen", ADDRESS, "--database", ""],
                          ["--listen", ADDRESS, "--database", "-db"],
                          ["--listen", ADDRESS, "--database"],
                          ["--listen", ADDRESS, "--database", "db", "--database", "db"],
                          ["--database", "db", "--requests", "missing.json"],
                          ["--database", "db", "--print-model", "Todo"],
                          ["--listen", "0.0.0.0:80", "--database", "db"]):
                with self.subTest(command=command, flags=flags):
                    result = self.run_cli(command, output, "out", *flags, "missing.lan")
                    self.assertEqual(result.returncode, 64, result.stderr)
                    self.assertEqual(result.stdout, b"")
                    self.assertNotIn(b"No such file", result.stderr)
                    self.assertFalse((self.work / "out").exists())
                    self.assertFalse((self.work / "out.partial").exists())
                    self.assertFalse((self.work / "db").exists())

    def test_non_utf8_path_is_a_usage_error(self):
        for command, output in (("emit", "--crate"), ("build", "--out"), ("serve", "--out")):
            with self.subTest(command=command):
                result = self.run_cli(command, output, "out", "--listen", ADDRESS,
                                      "--database", b"bad-\xff.sqlite3", "missing.lan")
                self.assertEqual(result.returncode, 64, result.stderr)
                self.assertFalse((self.work / "out").exists())

    def test_emit_build_and_serve_embed_the_same_invocation_path(self):
        database = self.work / 'store #?% "雪\\\n.sqlite3'
        database.write_bytes(b"existing database is untouched during emission")
        reference = None
        for index, (command, output, flags) in enumerate((
                ("emit", "--crate", ["--listen", ADDRESS, "--database", database.name]),
                ("emit", "--crate", ["--database", database, "--listen", ADDRESS]),
                ("build", "--out", ["--database", database.name, "--offline", "--listen", ADDRESS]),
                ("serve", "--out", ["--listen", ADDRESS, "--database", database, "--offline"]))):
            with self.subTest(command=command, flags=flags):
                destination = self.work / f"out-{index}"
                result = self.run_cli(command, output, destination, *flags, FIXTURE)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, b"")
                files = tuple((destination / name).read_bytes() for name in ("Cargo.toml", "src/main.rs"))
                if reference is None:
                    reference = files
                self.assertEqual(files, reference)
                self.assertEqual((destination / "cargo-called").exists(), command != "emit")
                self.assertEqual(database.read_bytes(), b"existing database is untouched during emission")
        dependencies = tomllib.loads(reference[0].decode())["dependencies"]
        self.assertEqual(dependencies["toasty-driver-sqlite"]["rev"], dependencies["toasty"]["rev"])

    def test_source_failure_preserves_database_and_existing_output(self):
        database = self.work / "db"
        database.write_bytes(b"preserve")
        source = self.work / "bad.lan"
        source.write_text("def main : Nat := 1\n")
        for command, output in (("emit", "--crate"), ("build", "--out"), ("serve", "--out")):
            result = self.run_cli(command, output, "out", "--listen", ADDRESS,
                                  "--database", database, source)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertFalse((self.work / "out").exists())
            self.assertEqual(database.read_bytes(), b"preserve")
        destination = self.work / "out"
        destination.mkdir()
        (destination / "sentinel").write_bytes(b"keep")
        result = self.run_cli("serve", "--out", destination, "--listen", ADDRESS,
                              "--database", database, FIXTURE)
        self.assertEqual(result.returncode, 64, result.stderr)
        self.assertEqual((destination / "sentinel").read_bytes(), b"keep")
        self.assertFalse((destination / "cargo-called").exists())

    def test_in_memory_default_has_no_file_driver_dependency(self):
        result = self.run_cli("emit", "--crate", "out", "--listen", ADDRESS, FIXTURE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("toasty-driver-sqlite", tomllib.loads((self.work / "out/Cargo.toml").read_text())["dependencies"])
        self.assertIn('.connect("sqlite::memory:")', (self.work / "out/src/main.rs").read_text())


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DatabaseCli))
    if not result.wasSuccessful():
        sys.exit(1)
    print(f"LAN-DATABASE CLI OK groups={result.testsRun}")
