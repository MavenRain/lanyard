"""Check composed HTML pages, input failures and native concat emission."""
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


class ConcatCli(unittest.TestCase):
    def test_composed_stored_titles(self):
        cases = [("title=++write+tests++", b"write tests"),
                 ("title=caf%C3%A9", "café".encode()), ("title=", b""),
                 ("title=%3Cscript%3E%26", b"&lt;script&gt;&amp;"),
                 ("title=%26lt%3B", b"&amp;lt;"),
                 ("title=a%00b", b"a\0b"),
                 ("title=a%0D%0A%0D%0AX-Header%3Ayes", b"a\r\n\r\nX-Header:yes")]
        for form, expected in cases:
            with self.subTest(form=form):
                result = run("run", "--request", "/todos", "--form", form, "test/fixtures/concat-form.lan")
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (0, response(b"<h1>" + expected + b"</h1>"), b""))

    def test_no_partial_output(self):
        for form, status, message in [("", 1, b"missing field"), ("title=%", 64, b"usage:"),
                                      ("title=x&title=y", 64, b"usage:")]:
            with self.subTest(form=form):
                result = run("run", "--request", "/", "--form", form, "test/fixtures/concat-form.lan")
                self.assertEqual((result.returncode, result.stdout), (status, b""))
                self.assertIn(message, result.stderr)

    def test_each_input_checked(self):
        with tempfile.TemporaryDirectory(prefix="lanyard-concat-") as directory:
            source = Path(directory) / "invalid.lan"
            pairs = [("(bytesCons 256 bytesNil)", 'b""', b"0..255"),
                     ('b""', "(bytesCons 256 bytesNil)", b"0..255"),
                     ("(bytesCons 255 bytesNil)", 'b"ok"', b"UTF-8"),
                     ('b"ok"', "(bytesCons 255 bytesNil)", b"UTF-8"),
                     ("(bytesCons 195 bytesNil)", "(bytesCons 169 bytesNil)", b"UTF-8")]
            for left, right, message in pairs:
                for unused in (False, True):
                    with self.subTest(left=left, right=right, unused=unused):
                        value = f"Text.concat Bytes {left} {right}"
                        expression = (f'let ignored : Bytes := {value} in Response.html Bytes b"ok"'
                                      if unused else f"Response.html Bytes ({value})")
                        source.write_text(BASE + "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => "
                                          + expression + "\n")
                        result = run("run", "--request", "/", source)
                        self.assertEqual((result.returncode, result.stdout), (1, b""))
                        self.assertIn(message, result.stderr)

    def test_alias_capture_and_alternate_family(self):
        with tempfile.TemporaryDirectory(prefix="lanyard-concat-alias-") as directory:
            source = Path(directory) / "alias.lan"
            for family in ("Bytes", "TextList"):
                with self.subTest(family=family):
                    source.write_text((BASE + 'def join : Bytes -> Bytes -> Bytes := Text.concat Bytes\n'
                        'def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => '
                        'let prefix : Bytes := b"<p>" in '
                        'let append : Bytes -> Bytes := fun (value : Bytes) => join prefix value in '
                        'Response.html Bytes (append b"hello</p>")\n').replace("Bytes", family))
                    result = run("run", "--request", "/", source)
                    self.assertEqual((result.returncode, result.stdout, result.stderr),
                                     (0, response(b"<p>hello</p>"), b""))
                    emitted = run("emit", "--target", source)
                    self.assertEqual((emitted.returncode, emitted.stderr), (0, b""))

    def test_emission(self):
        result = run("emit", "--target", "test/fixtures/concat-form.lan")
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        self.assertIn(b"text/html; charset=utf-8", result.stdout)
        with tempfile.TemporaryDirectory(prefix="lanyard-concat-crate-") as directory:
            source = Path(directory) / "main.lan"
            source.write_text(BASE + 'def main : Bytes := Text.concat Bytes b"left" b"right"\n')
            destination = Path(directory) / "crate"
            emitted = run("emit", "--crate", destination, source)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, b""))
            self.assertTrue((destination / "src/main.rs").is_file())
            emitted_source = (destination / "src/main.rs").read_text()
            self.assertIn("__lan_left + &__lan_right", emitted_source)
            self.assertNotIn("__lan_right + &__lan_left", emitted_source)

    def test_effectful_arguments(self):
        with tempfile.TemporaryDirectory(prefix="lanyard-concat-order-") as directory:
            source = Path(directory) / "request.lan"
            fixture = (ROOT / "test/fixtures/concat-order.lan").read_text()
            source.write_text(fixture.replace("def main : Response :=", "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) =>"))
            result = run("run", "--request", "/", source)
            expected = (b"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n"
                        b"Content-Length: 9\r\n\r\nleftright")
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected, b""))

    def test_refusal_before_output(self):
        with tempfile.TemporaryDirectory(prefix="lanyard-concat-refusal-") as directory:
            source = Path(directory) / "bad.lan"
            source.write_text("def main : Nat := Text.concat Nat 1 2\n")
            destination = Path(directory) / "crate"
            result = run("emit", "--crate", destination, source)
            self.assertEqual((result.returncode, result.stdout), (1, b""))
            self.assertIn(b"byte list", result.stderr)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
