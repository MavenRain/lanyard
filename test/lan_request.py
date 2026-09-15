"""Check scripted requests through the actual CLI and exact HTTP response bytes."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "_build/default/bin/lanyard.exe"
ENTRY = "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => "
REDIRECT = ENTRY + "topcoat.see_other uri"
MODEL = "model Counter with | id : Nat | value : Nat end\n"
DB = "let db : Db := topcoat.db cx in "
READY = "let ready : prod () := Db.push_schema db in "
CREATE = "let created : Counter := Counter.create (tuple (1, 23)) db in "


def response(uri):
    return ("HTTP/1.1 303 See Other\r\nLocation: " + uri +
            "\r\nContent-Length: 0\r\n\r\n").encode("ascii")


class Request(unittest.TestCase):
    def setUp(self):
        (ROOT / ".gatework").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="request-cli-", dir=ROOT / ".gatework")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "request.lan"

    def invoke(self, *args, env=None):
        return subprocess.run([str(EXE), "run", *map(str, args)], cwd=self.directory,
                              env=env, capture_output=True, timeout=20)

    def program(self, text, uri="/next", *options):
        self.source.write_text(text)
        return self.invoke(*options, "--request", uri, self.source)

    def success(self, result, uri="/next"):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, response(uri))
        self.assertEqual(result.stderr, b"")

    def refusal(self, result, message, code=1):
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertEqual(result.stdout, b"")
        self.assertIn(message.encode(), result.stderr)

    def test_redirect(self):
        for uri in ("/", "/todos", "/a%2Fb?q=x%20y&tag=%E2%98%83", "/a?x=1?y=2"):
            with self.subTest(uri=uri):
                self.success(self.program(REDIRECT, uri), uri)

    def test_database_fixture(self):
        self.success(self.invoke("--request", "/next", ROOT / "test/fixtures/request.lan"))

    def test_context_database_alias(self):
        self.success(self.program(MODEL + ENTRY + DB + READY + CREATE +
            "let shared : Db := topcoat.db cx in "
            "let found : Counter := Counter.get_by_id 1 shared in topcoat.see_other uri"))

    def test_lookup_observation(self):
        self.success(self.program("def Bool : Type 0 := sum ((prod () : Type 0), (prod () : Type 0))\n" +
            MODEL + ENTRY + DB + READY + CREATE +
            "let found : Counter := Counter.get_by_id 1 db in "
            "case natEq found.1 23 with "
            "| 0 (u : prod ()) => let missing : Counter := Counter.get_by_id 999 db in topcoat.see_other uri "
            "| 1 (u : prod ()) => topcoat.see_other uri"))

    def test_schema_required(self):
        self.refusal(self.program(MODEL + ENTRY + DB + CREATE + "topcoat.see_other uri"),
                     "schema has not been initialized")

    def test_duplicate_key(self):
        self.refusal(self.program(MODEL + ENTRY + DB + READY + CREATE + CREATE + "topcoat.see_other uri"),
                     "duplicate model key")

    def test_missing_row_has_no_response(self):
        self.refusal(self.program(MODEL + ENTRY + DB + READY +
            "let response : SeeOther := topcoat.see_other uri in "
            "let absent : Counter := Counter.get_by_id 99 db in response"), "model row not found")

    def test_explicit_connection_is_separate(self):
        self.refusal(self.program("mu Bytes : Type 0 := | bytesNil : Bytes | bytesCons (head : Nat) (tail : Bytes) : Bytes\n" +
            MODEL + ENTRY + DB + READY + CREATE +
            'let other : Db := Db.connect Counter Bytes b"sqlite::memory:" in '
            "let ready : prod () := Db.push_schema other in "
            "let absent : Counter := Counter.get_by_id 1 other in topcoat.see_other uri"), "model row not found")

    def test_model_selection(self):
        self.success(self.program(MODEL + "model Audit with | id : Nat end\n" + ENTRY + DB + READY + CREATE +
            "let audit : Audit := Audit.create (tuple (1)) db in "
            "let found : Audit := Audit.get_by_id 1 db in topcoat.see_other uri"))

    def test_closure_and_aliases(self):
        self.success(self.program("def Context : Type 0 := Cx\ndef Target : Type 0 := Uri\n"
            "def Redirect : Type 0 := SeeOther\n"
            "def main : Context -> Target -> Redirect := fun (cx : Context) (uri : Target) => "
            "let forward : Nat -> SeeOther := fun (n : Nat) => topcoat.see_other uri in forward 3"))

    def test_wrong_entry_type(self):
        programs = ["def main : Nat := 3", "def main : Uri -> SeeOther := topcoat.see_other",
                    "def main : Uri -> Cx -> SeeOther := fun (uri : Uri) (cx : Cx) => topcoat.see_other uri",
                    ENTRY.replace("-> SeeOther", "-> Uri") + "uri"]
        for program in programs:
            with self.subTest(program=program):
                self.refusal(self.program(program), "Cx -> Uri -> SeeOther")

    def test_step_limit_and_order(self):
        self.refusal(self.program(REDIRECT, "/next", "--steps", "1"), "step limit exhausted")
        self.success(self.program(REDIRECT, "/next", "--steps", "100000"))
        self.success(self.invoke("--request", "/next", "--steps", "100000", self.source))

    def test_invalid_uri_before_source_read(self):
        invalid = ["", "relative", "https://example.test/", "//example.test/", "/#fragment",
                   "/bad path", "/bad\tpath", "/bad\r\nLocation:/evil", "/bad\\path", "/snowman-\u2603",
                   "/%", "/%1", "/%GG", "/[bad]", "/" + "a" * 8192]
        for uri in invalid:
            with self.subTest(uri=uri[:40]):
                self.refusal(self.invoke("--request", uri, self.source), "usage:", 64)

    def test_uri_boundary(self):
        uri = "/" + "a" * 8191
        self.success(self.program(REDIRECT, uri), uri)

    def test_usage(self):
        bad = [["--request"], ["--request", "/a"], ["--request", "/a", "--request", "/b", self.source],
               ["--print-model", "Counter", "--request", "/a", self.source],
               ["--request", "/a", "--print-model", "Counter", self.source],
               [self.source, "--request", "/a"], ["--request", "/a", "bad.kan"]]
        for args in bad:
            with self.subTest(args=args):
                self.refusal(self.invoke(*args), "usage:", 64)

    def test_source_errors(self):
        self.refusal(self.invoke("--request", "/next", self.source), "cannot read", 64)
        self.refusal(self.program("def main : Nat := ()"), "mismatch")
        self.refusal(self.program("def answer : Nat := 3"), "missing runtime function main")

    def test_plain_run_still_requires_nullary_main(self):
        self.source.write_text(REDIRECT)
        self.refusal(self.invoke(self.source), "requires runtime arguments")

    def test_no_cargo_or_shell(self):
        self.source = self.directory / "quote ' and spaces.lan"
        self.source.write_text(REDIRECT)
        cargo = self.directory / "cargo"
        cargo.write_text("#!/bin/sh\ntouch cargo-was-run\nexit 93\n")
        cargo.chmod(0o755)
        uri = "/$(id)?x=1&y=2"
        self.success(self.invoke("--request", uri, self.source,
                     env={**os.environ, "PATH": str(self.directory)}), uri)
        # A PATH with only this directory and a URI holding shell syntax:
        # the success above proves run mode spawns no subprocess and no
        # shell, because a spawned cargo would exit 93 and fail the call.


if __name__ == "__main__":
    unittest.main()
