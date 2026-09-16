"""Check HTML wire output, escaped model fields and checked native emission."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = "mu Bytes : Type 0 := | bytesNil : Bytes | bytesCons (head : Nat) (tail : Bytes) : Bytes\n"


def run(*args):
    return subprocess.run([str(DRIVER), *map(str, args)], cwd=ROOT, capture_output=True, timeout=60)


def response(body):
    return (b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: "
            + str(len(body)).encode() + b"\r\n\r\n" + body)


class HtmlCli(unittest.TestCase):
    def test_markup_request(self):
        result = run("run", "--request", "/hello", "test/fixtures/html.lan")
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, response(b"<h1>Hello from Lanyard!</h1>"), b""))

    def test_escaped_stored_titles(self):
        cases = [
            ("title=++write+tests++", b"write tests"),
            ("title=caf%C3%A9", "café".encode()),
            ("title=", b""),
            ("title=%3Cscript%3Ealert%281%29%3C%2Fscript%3E", b"&lt;script&gt;alert(1)&lt;/script&gt;"),
            ("title=%26lt%3B%26", b"&amp;lt;&amp;"),
            ("title=%22%27", b"\"'"),
            ("title=a%00b", b"a\0b"),
            ("title=a%0D%0A%0D%0AX-Header%3Ayes", b"a\r\n\r\nX-Header:yes"),
        ]
        for form, expected in cases:
            with self.subTest(form=form):
                result = run("run", "--form", form, "--request", "/todos", "test/fixtures/html-form.lan")
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, response(expected), b""))

    def test_no_partial_output(self):
        for form, status, message in [("", 1, b"missing field"), ("title=%", 64, b"usage:"),
                                      ("title=x&title=y", 64, b"usage:"), ("other=x", 1, b"missing field")]:
            with self.subTest(form=form):
                result = run("run", "--request", "/", "--form", form, "test/fixtures/html-form.lan")
                self.assertEqual((result.returncode, result.stdout), (status, b""))
                self.assertIn(message, result.stderr)
        result = run("run", "--steps", "1", "--request", "/", "test/fixtures/html.lan")
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"step limit", result.stderr)

    def test_invalid_bodies(self):
        with tempfile.TemporaryDirectory(prefix="lanyard-html-") as directory:
            source = Path(directory) / "invalid.lan"
            for escaped in (False, True):
                for byte, message in [(256, b"0..255"), (255, b"UTF-8")]:
                    with self.subTest(escaped=escaped, byte=byte):
                        argument = f"(bytesCons {byte} bytesNil)"
                        if escaped:
                            argument = f"(Html.text Bytes {argument})"
                        source.write_text(BASE + "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => "
                                          f"Response.html Bytes {argument}\n")
                        result = run("run", "--request", "/", source)
                        self.assertEqual((result.returncode, result.stdout), (1, b""))
                        self.assertIn(message, result.stderr)

    def test_emission(self):
        for name in ("html", "html-form"):
            result = run("emit", "--target", f"test/fixtures/{name}.lan")
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            self.assertIn(b"topcoat::router::Body::from", result.stdout)
            self.assertIn(b"text/html; charset=utf-8", result.stdout)
        with tempfile.TemporaryDirectory(prefix="lanyard-html-crate-") as directory:
            source = Path(directory) / "main.lan"
            source.write_text(BASE + 'def main : Response := Response.html Bytes (Html.text Bytes b"<hello>")\n')
            destination = Path(directory) / "crate"
            result = run("emit", "--crate", destination, source)
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            emitted = (destination / "src/main.rs").read_text()
            self.assertIn("text/html; charset=utf-8", emitted)
            self.assertIn(".replace('&', \"&amp;\")", emitted)

    def test_foreign_ownership_limits(self):
        cases = [
            ('def main : Response := let value : Response := Response.html Bytes b"x" in value',
             b"owned copy of a shared foreign value"),
            ('def main : prod (Response, Response) := let value : Response := Response.html Bytes b"x" in tuple (value, value)',
             b"foreign aggregate layout"),
        ]
        with tempfile.TemporaryDirectory(prefix="lanyard-html-layout-") as directory:
            source = Path(directory) / "main.lan"
            for declaration, message in cases:
                with self.subTest(declaration=declaration):
                    source.write_text(BASE + declaration + "\n")
                    result = run("emit", "--target", source)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stdout, b"")
                    self.assertIn(message, result.stderr)


if __name__ == "__main__":
    unittest.main()
