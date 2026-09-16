"""Check HTTP response bytes, model-backed forms and response failures."""
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
    return (b"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: "
            + str(len(body)).encode() + b"\r\n\r\n" + body)


class ResponseCli(unittest.TestCase):
    def test_plain_request(self):
        result = run("run", "--request", "/hello", "test/fixtures/response.lan")
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, response(b"Hello from Lanyard!"), b""))

    def test_stored_form_title(self):
        for form, title in [("title=++write+tests++", b"write tests"),
                            ("title=caf%C3%A9", "café".encode()), ("title=", b""),
                            ("title=%3Cb%3Ehello%3C%2Fb%3E", b"<b>hello</b>"),
                            ("title=a%0D%0A%0D%0AX-Header%3Ayes", b"a\r\n\r\nX-Header:yes"),
                            ("title=a%00b", b"a\0b")]:
            with self.subTest(form=form):
                result = run("run", "--form", form, "--request", "/todos", "test/fixtures/response-form.lan")
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, response(title), b""))

    def test_no_partial_output(self):
        cases = [("", 1, b"missing field"), ("title=%", 64, b"usage:"),
                 ("title=x&title=y", 64, b"usage:"), ("other=x", 1, b"missing field")]
        for form, status, message in cases:
            with self.subTest(form=form):
                result = run("run", "--request", "/", "--form", form, "test/fixtures/response-form.lan")
                self.assertEqual((result.returncode, result.stdout), (status, b""))
                self.assertIn(message, result.stderr)
        result = run("run", "--steps", "1", "--request", "/", "test/fixtures/response.lan")
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"step limit", result.stderr)

    def test_invalid_response_body(self):
        with tempfile.TemporaryDirectory(prefix="lanyard-response-") as directory:
            source = Path(directory) / "invalid.lan"
            for value, message in [("256", b"0..255"), ("255", b"UTF-8")]:
                source.write_text(BASE + "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => "
                                  f"Response.text Bytes (bytesCons {value} bytesNil)\n")
                result = run("run", "--request", "/", source)
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertIn(message, result.stderr)

    def test_emission(self):
        for name in ("response", "response-form"):
            result = run("emit", "--target", f"test/fixtures/{name}.lan")
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            self.assertIn(b"topcoat::router::Body::from", result.stdout)
            self.assertIn(b"text/plain; charset=utf-8", result.stdout)
        with tempfile.TemporaryDirectory(prefix="lanyard-response-crate-") as directory:
            source = Path(directory) / "main.lan"
            source.write_text(BASE + 'def main : Response := Response.text Bytes b"hello"\n')
            destination = Path(directory) / "crate"
            result = run("emit", "--crate", destination, source)
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            self.assertIn("text/plain; charset=utf-8", (destination / "src/main.rs").read_text())

    def test_foreign_ownership_limits(self):
        cases = [
            ('def main : Response := let value : Response := Response.text Bytes b"x" in value',
             b"owned copy of a shared foreign value"),
            ('def main : prod (Response, Response) := let value : Response := Response.text Bytes b"x" in tuple (value, value)',
             b"foreign aggregate layout"),
            ('def main : Response := let make : Bytes -> Response := fun (text : Bytes) => Response.text Bytes text in make b"x"',
             b"foreign aggregate layout"),
        ]
        with tempfile.TemporaryDirectory(prefix="lanyard-response-ownership-") as directory:
            source = Path(directory) / "main.lan"
            for program, message in cases:
                with self.subTest(message=message):
                    source.write_text(BASE + program + "\n")
                    result = run("emit", "--target", source)
                    self.assertEqual((result.returncode, result.stdout), (1, b""))
                    self.assertIn(message, result.stderr)


if __name__ == "__main__":
    unittest.main()
