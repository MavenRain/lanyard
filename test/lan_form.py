"""Exercise form input, option validation and complete target emission."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
FIXTURE = ROOT / "test/fixtures/form-request.lan"
RESPONSE = b"HTTP/1.1 303 See Other\r\nLocation: /\r\nContent-Length: 0\r\n\r\n"


def run(*args):
    return subprocess.run([str(DRIVER), *map(str, args)], cwd=ROOT, capture_output=True, timeout=60)


class FormCli(unittest.TestCase):
    def test_request(self):
        for options in (("--request", "/todos", "--form", "title=write+tests"),
                        ("--form", "title=caf%C3%A9", "--steps", "10000", "--request", "/todos")):
            with self.subTest(options=options):
                result = run("run", *options, FIXTURE)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, RESPONSE, b""))

    def test_title(self):
        result = run("run", "--print-model", "Title", "test/fixtures/form.lan")
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, b'Title { id: 1, text: "write tests", blank: false }\n', b""))

    def test_usage_before_source_io(self):
        bad = [("--form", "title=x"), ("--request", "/", "--form"),
               ("--request", "/", "--form", "title=%"),
               ("--request", "/", "--form", "title=x&title=y"),
               ("--request", "/", "--form", "title=" + "x" * 8187),
               ("--request", "/", "--form", "title=x", "--form", "title=y"),
               ("--print-model", "Title", "--request", "/", "--form", "title=x"),
               ("--form", "title=x", "--print-model", "Title", "--request", "/")]
        for options in bad:
            with self.subTest(options=options[:4]):
                result = run("run", *options, "does-not-exist.lan")
                self.assertEqual(result.returncode, 64)
                self.assertEqual(result.stdout, b"")
                self.assertNotIn(b"I/O", result.stderr)
                self.assertIn(b"usage:", result.stderr.lower())

    def test_execution_errors(self):
        for body in ("", "other=x"):
            result = run("run", "--request", "/", "--form", body, FIXTURE)
            self.assertEqual((result.returncode, result.stdout), (1, b""))
            self.assertIn(b"missing field", result.stderr)
        result = run("run", "--request", "/", "--form", "title=x", "--steps", "1", FIXTURE)
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"step limit", result.stderr)

    def test_entry_shapes(self):
        for options, fixture in [(("--request", "/"), FIXTURE),
                                 (("--request", "/", "--form", "title=x"), "test/fixtures/uri.lan")]:
            result = run("run", *options, fixture)
            self.assertEqual((result.returncode, result.stdout), (1, b""))
            self.assertIn(b"entry point", result.stderr)

    def test_emission(self):
        with tempfile.TemporaryDirectory(prefix="lanyard-form-") as directory:
            out = Path(directory) / "crate"
            result = run("emit", "--crate", out, "--print-model", "Title", "test/fixtures/form.lan")
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            source = (out / "src/main.rs").read_text()
            self.assertIn("Form::<Vec<(String, String)>>::from_bytes", source)
            self.assertIn("InvalidForm", source)
            self.assertIn("lan_form_validate_component(value)?", source)
        result = run("emit", "--target", FIXTURE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"async fn", result.stdout)


if __name__ == "__main__":
    unittest.main()
