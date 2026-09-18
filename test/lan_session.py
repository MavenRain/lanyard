"""Exercise complete request sessions through the public driver."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "_build/default/bin/lanyard.exe"
FIXTURE = ROOT / "test/fixtures/todo-session.lan"
SCRIPT = ROOT / "test/fixtures/todo-session.requests"
REDIRECT = "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => topcoat.see_other uri"


def response(body, kind="html"):
    body = body.encode("utf-8")
    return (f"HTTP/1.1 200 OK\r\nContent-Type: text/{kind}; charset=utf-8\r\n"
            f"Content-Length: {len(body)}\r\n\r\n").encode() + body


def redirect(uri):
    return f"HTTP/1.1 303 See Other\r\nLocation: {uri}\r\nContent-Length: 0\r\n\r\n".encode()


class Session(unittest.TestCase):
    def invoke(self, arguments):
        return subprocess.run([str(EXE), "run", *map(str, arguments)], cwd=ROOT,
                              capture_output=True, timeout=60)

    def session(self, script, source=None, options=()):
        with tempfile.TemporaryDirectory(prefix="lan-session-") as directory:
            script_path = Path(directory) / "requests.txt"
            script_path.write_bytes(script.encode() if isinstance(script, str) else script)
            path = FIXTURE
            if source is not None:
                path = Path(directory) / "handler.lan"
                path.write_text(source)
            return self.invoke([*options, "--requests", script_path, path])

    def success(self, result, expected):
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(result.stderr, b"")
        self.assertEqual(result.stdout, expected)

    def failure(self, result, code, message):
        self.assertEqual(result.returncode, code, result.stderr.decode())
        self.assertEqual(result.stdout, b"")
        self.assertIn(message.encode(), result.stderr)

    def test_todo_lifecycle(self):
        first = "<ul><li>20: café</li></ul>"
        both = "<ul><li>3: &lt;write&gt; &amp; test</li><li>20: café</li></ul>"
        updated = "<ul><li>3: updated (done)</li><li>20: café</li></ul>"
        final = "<ul><li>3: updated (done)</li></ul>"
        expected = response("ready", "plain") + b"".join(map(response, [first, both, updated, final, final, final]))
        self.success(self.invoke(["--requests", SCRIPT, FIXTURE]), expected)

    def test_session_isolation(self):
        script = "/init\t\n/todos/create\tid=1&title=one\n"
        expected = response("ready", "plain") + response("<ul><li>1: one</li></ul>")
        self.success(self.session(script), expected)
        self.success(self.session(script), expected)
        self.failure(self.session("/todos\t"), 1, "schema")

    def test_blank_title_does_not_create(self):
        self.success(self.session("/init\t\n/todos/create\tid=1&title=+++\n/todos\t"),
                     response("ready", "plain") + response("title required", "plain") + response("<ul></ul>"))

    def test_unknown_path_preserves_uri(self):
        self.success(self.session("/init\t\n/todos?filter=done\t"),
                     response("ready", "plain") + response("unmatched: /todos?filter=done", "plain"))

    def test_order_and_redirects(self):
        self.success(self.session("/first\r\n/second%2Fthird\r\n", REDIRECT),
                     redirect("/first") + redirect("/second%2Fthird"))

    def test_empty_body_and_no_body_differ(self):
        self.success(self.session("/only", REDIRECT), redirect("/only"))
        self.failure(self.session("/only\t", REDIRECT), 1, "form request entry point")
        self.failure(self.session("/init"), 1, "request entry point")

    def test_failure_discards_transcript(self):
        self.failure(self.session("/init\t\n/todos/update\tid=42&title=missing&completed=true"),
                     1, "request 2:")
        self.failure(self.session("/init\t\n/todos/create\tid=1&title=ok\n/todos/create\tid=1&title=again"),
                     1, "request 3:")
        self.failure(self.session("/first\n/second\t", REDIRECT), 1, "request 2:")

    def test_whole_session_step_budget(self):
        self.success(self.session("/", REDIRECT, ("--steps", "32")), redirect("/"))
        self.failure(self.session("/\n" * 128, REDIRECT, ("--steps", "32")), 1, "step limit exhausted")

    def test_invalid_scripts_precede_source_io(self):
        for script, message in [(b"", "at least one"), (b"/\n/%GG", "line 2"),
                                (b"/\tx=%FF", "UTF-8"), (b"/\tx=y\tz=w", "URI<TAB>FORM"),
                                (b"/\n" * 129, "128 requests"), (b"x" * 1048577, "1048576")]:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "requests"
                path.write_bytes(script)
                self.failure(self.invoke(["--requests", path, "missing-source.lan"]), 64, message)

    def test_option_conflicts(self):
        choices = [("--request", "/"), ("--form", "x=y"), ("--print-model", "Todo"),
                   ("--requests", "another.requests")]
        for other in choices:
            for arguments in (["--requests", SCRIPT, *other, FIXTURE],
                              [*other, "--requests", SCRIPT, FIXTURE]):
                with self.subTest(arguments=arguments):
                    self.failure(self.invoke(arguments), 64, "usage:")
        for arguments in (["--requests"], ["--requests", "--steps", "3", FIXTURE],
                          ["--requests", SCRIPT, "--steps", "0", FIXTURE]):
            self.failure(self.invoke(arguments), 64, "usage:")

    def test_missing_script(self):
        self.failure(self.invoke(["--requests", "missing.requests", FIXTURE]), 64, "cannot read")

    def test_single_request_regression(self):
        self.success(self.invoke(["--request", "/init", "--form", "", FIXTURE]), response("ready", "plain"))


if __name__ == "__main__":
    unittest.main()
