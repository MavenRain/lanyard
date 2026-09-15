"""Exercise model updates through checked programs and crate emission."""
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
UPDATE = "Counter.update (tuple (7, 23)) db"
EXPECTED = b'Task { title: "updated", id: 7, completed: true, value: 23 }\n'


class Update(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="lanyard-update-")
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

    def test_all_scalars_and_nonleading_key(self):
        self.success((ROOT / "test/fixtures/update.lan").read_text(), EXPECTED,
                     "run", "--print-model", "Task")

    def test_returned_row(self):
        self.success(BASE + "def main : Counter := " + OPEN + CREATE + UPDATE,
                     b"Counter { id: 7, value: 23 }\n", "run", "--print-model", "Counter")

    def test_unused_result_still_updates(self):
        text = BASE + "def main : Counter := " + OPEN + CREATE
        text += "let ignored : Counter := " + UPDATE + " in Counter.get_by_id 7 db"
        self.success(text, b"Counter { id: 7, value: 23 }\n", "run", "--print-model", "Counter")

    def test_missing_key(self):
        result = self.invoke(BASE + "def main : Counter := " + OPEN + UPDATE, "run")
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"model row not found: Counter", result.stderr)

    def test_invalid_field(self):
        for value, diagnostic in [("9223372036854775808", b"range"), ("()", b"mismatch")]:
            with self.subTest(value=value):
                text = BASE + "def main : Counter := " + OPEN + CREATE
                result = self.invoke(text + f"Counter.update (tuple (7, {value})) db", "run")
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertIn(diagnostic, result.stderr)

    def test_invalid_text(self):
        text = (ROOT / "test/fixtures/update.lan").read_text()
        for value, diagnostic in [("bytesCons 256 bytesNil", b"outside 0..255"),
                                  ("bytesCons 255 bytesNil", b"UTF-8")]:
            with self.subTest(value=value):
                result = self.invoke(text.replace('b"updated"', value), "run")
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertIn(diagnostic, result.stderr)

    def test_key_only_model(self):
        text = BASE.replace("| value : Nat ", "")
        text += "def main : Counter := " + OPEN
        text += "let created : Counter := Counter.create (tuple (7)) db in Counter.update (tuple (7)) db"
        self.success(text, b"Counter { id: 7 }\n", "run", "--print-model", "Counter")

    def test_closure(self):
        definitions = """def change : Nat -> Db -> Counter := fun (value : Nat) (db : Db) =>
  Counter.update (tuple (7, value)) db
def capture : Nat -> prod (Db -> Counter) := fun (value : Nat) => tuple (fun (db : Db) => change value db)
"""
        self.success(BASE + definitions + "def main : Counter := " + OPEN + CREATE
                     + "let update_row : Db -> Counter := (capture 23).0 in update_row db",
                     b"Counter { id: 7, value: 23 }\n", "run", "--print-model", "Counter")

    def test_request_shared_context(self):
        text = BASE + "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => "
        text += "let db : Db := topcoat.db cx in let ready : prod () := Db.push_schema db in " + CREATE
        text += "let shared : Db := topcoat.db cx in "
        text += "let updated : Counter := Counter.update (tuple (7, 23)) shared in topcoat.see_other uri"
        self.success(text, b"HTTP/1.1 303 See Other\r\nLocation: /updated\r\nContent-Length: 0\r\n\r\n",
                     "run", "--request", "/updated")

    def test_request_update_only(self):
        text = BASE + "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => "
        text += "let db : Db := topcoat.db cx in let ready : prod () := Db.push_schema db in "
        text += "let changed : Counter := " + UPDATE + " in topcoat.see_other uri"
        result = self.invoke(text, "run", "--request", "/empty")
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"model row not found: Counter", result.stderr)
        self.assertNotIn(b"not registered", result.stderr)

    def test_crate(self):
        output = self.work / "crate"
        result = self.invoke((ROOT / "test/fixtures/update.lan").read_text(),
                             "emit", "--crate", str(output), "--print-model", "Task")
        self.assertEqual(result.returncode, 0, result.stderr)
        emitted = (output / "src/main.rs").read_text()
        self.assertIn("toasty::update!(__lan_row {", emitted)
        self.assertIn("&__lan_fields.id).await?", emitted)
        self.assertIn("lan_require_send(f_6d61696e()).await?", emitted)


if __name__ == "__main__":
    unittest.main()
