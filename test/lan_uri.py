"""Exercise text-derived redirects through the public driver."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = """mu Bytes : Type 0 :=
| bytesNil : Bytes
| bytesCons (head : Nat) (tail : Bytes) : Bytes
def parse : Bytes -> Uri := Uri.from_text Bytes
"""


def literal(values):
    result = "bytesNil"
    for value in reversed(values):
        result = f"(bytesCons {value} {result})"
    return result


def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT,
                          capture_output=True, timeout=120)


class UriConversion(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="lanyard-uri-")
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "program.lan"

    def source(self, body):
        self.path.write_text(BASE + body)
        return self.path

    def test_home_redirect(self):
        result = run(DRIVER, "run", "--request", "/todos", "test/fixtures/uri.lan")
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, b"HTTP/1.1 303 See Other\r\nLocation: /\r\nContent-Length: 0\r\n\r\n", b""))

    def test_redirect_preserves_bytes(self):
        for path in [b"/", b"/a??b", b"/%c3%a9?q=one&x=%20", b"/%00%0d%0A"]:
            with self.subTest(path=path):
                source = self.source("def main : Cx -> Uri -> SeeOther := "
                    f"fun (cx : Cx) (request : Uri) => topcoat.see_other (parse {literal(path)})")
                result = run(DRIVER, "run", "--request", "/incoming", source)
                self.assertEqual((result.returncode, result.stderr), (0, b""))
                self.assertEqual(result.stdout, b"HTTP/1.1 303 See Other\r\nLocation: "
                                 + path + b"\r\nContent-Length: 0\r\n\r\n")

    def test_invalid_conversion_is_observable(self):
        for values, error in [(b"//host", b"request URI"), (b"/%x0", b"request URI"),
                              (b"/\r\nLocation: /evil", b"request URI"),
                              ([256], b"outside 0..255"), ([255], b"invalid UTF-8")]:
            with self.subTest(values=values):
                source = self.source(f"def main : Nat := let unused : Uri := parse {literal(values)} in 1")
                self.assertEqual(run(DRIVER, "check", source).returncode, 0)
                result = run(DRIVER, "run", source)
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertIn(error, result.stderr)

    def test_unsupported_layout(self):
        source = self.source("def main : Uri := Uri.from_text Nat 1")
        for command in [("run",), ("emit", "--target")]:
            with self.subTest(command=command):
                result = run(DRIVER, *command, source)
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertIn(b"byte list", result.stderr)

    def test_target_schema_disclosure(self):
        source = self.source('def main : Uri := parse b"/"')
        report = run(DRIVER, "axioms", source)
        self.assertEqual(report.returncode, 0, report.stderr)
        self.assertIn(b"Foreign Uri_from_text", report.stdout)
        self.assertIn(b"[schema=Uri.from_text]", report.stdout)
        emitted = run(DRIVER, "emit", "--target", source)
        self.assertEqual(emitted.returncode, 0, emitted.stderr)
        self.assertIn(b"parse::<topcoat::router::Uri>()", emitted.stdout)
        self.assertIn(b"lan_uri_validate(&__lan_text)?;", emitted.stdout)
        self.assertNotIn(b".await", emitted.stdout)


if __name__ == "__main__":
    unittest.main()
