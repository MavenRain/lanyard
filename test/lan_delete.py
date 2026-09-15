"""Check deletion through the public interpreter and crate commands."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = """mu Bytes : Type 0 := | bytesNil : Bytes | bytesCons (head : Nat) (tail : Bytes) : Bytes
model Counter with | id : Nat | value : Nat end
"""
OPEN = """let db : Db := Db.connect Counter Bytes b"sqlite::memory:" in
let ready : prod () := Db.push_schema db in
"""
CREATE = "let created : Counter := Counter.create (tuple (7, 42)) db in\n"


class Delete(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="lanyard-delete-")
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)

    def invoke(self, text, *arguments):
        source = self.work / "program.lan"
        source.write_text(text)
        return subprocess.run([str(DRIVER), *arguments, str(source)], cwd=ROOT,
                              capture_output=True, timeout=120)

    def success(self, text, output, *arguments):
        result = self.invoke(text, *arguments)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, output, b""))

    def test_recreate(self):
        self.success((ROOT / "test/fixtures/delete.lan").read_text(),
                     b"Counter { id: 7, value: 23 }\n", "run", "--print-model", "Counter")

    def test_unit_entrypoint(self):
        self.success(BASE + "def main : prod () := " + OPEN + CREATE + "Counter.delete_by_id 7 db",
                     b"", "run")

    def test_missing_key(self):
        self.success(BASE + "def main : prod () := " + OPEN + "Counter.delete_by_id 7 db",
                     b"", "run")

    def test_deleted_lookup(self):
        result = self.invoke(BASE + "def main : Counter := " + OPEN + CREATE
                             + "let gone : prod () := Counter.delete_by_id 7 db in Counter.get_by_id 7 db",
                             "run", "--print-model", "Counter")
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"model row not found: Counter", result.stderr)

    def test_key_range(self):
        result = self.invoke(BASE + "def main : prod () := " + OPEN
                             + "Counter.delete_by_id 9223372036854775808 db", "run")
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"range", result.stderr)

    def test_closure(self):
        definitions = """def remove : Nat -> Db -> prod () := fun (key : Nat) (db : Db) => Counter.delete_by_id key db
def replace : Nat -> Db -> Counter := fun (key : Nat) (db : Db) =>
  let gone : prod () := remove key db in Counter.create (tuple (key, 23)) db
def capture : Nat -> prod (Db -> Counter) := fun (key : Nat) => tuple (fun (db : Db) => replace key db)
"""
        self.success(BASE + definitions + "def main : Counter := " + OPEN + CREATE
                     + "let replace_row : Db -> Counter := (capture 7).0 in replace_row db",
                     b"Counter { id: 7, value: 23 }\n", "run", "--print-model", "Counter")

    def test_request_context(self):
        text = BASE + "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => "
        text += "let db : Db := topcoat.db cx in let ready : prod () := Db.push_schema db in " + CREATE
        text += "let shared : Db := topcoat.db cx in let gone : prod () := Counter.delete_by_id 7 shared in "
        text += "let replaced : Counter := Counter.create (tuple (7, 23)) db in topcoat.see_other uri"
        self.success(text, b"HTTP/1.1 303 See Other\r\nLocation: /deleted\r\nContent-Length: 0\r\n\r\n",
                     "run", "--request", "/deleted")

    def test_crate(self):
        output = self.work / "crate"
        result = self.invoke((ROOT / "test/fixtures/delete.lan").read_text(),
                             "emit", "--crate", str(output), "--print-model", "Counter")
        self.assertEqual(result.returncode, 0, result.stderr)
        emitted = (output / "src/main.rs").read_text()
        self.assertIn("::delete_by_id(&mut __lan_db, lan_model_to_i64(&__lan_value)?).await?", emitted)
        self.assertIn("lan_require_send(f_6d61696e()).await?", emitted)

    def test_request_delete_only(self):
        text = BASE + "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => "
        text += "let db : Db := topcoat.db cx in let ready : prod () := Db.push_schema db in "
        text += "let gone : prod () := Counter.delete_by_id 7 db in topcoat.see_other uri"
        self.success(text, b"HTTP/1.1 303 See Other\r\nLocation: /empty\r\nContent-Length: 0\r\n\r\n",
                     "run", "--request", "/empty")


if __name__ == "__main__":
    unittest.main()
