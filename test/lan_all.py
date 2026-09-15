"""Exercise ordered model lists through checked programs and crate emission."""
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
CHOOSE = """let rows : Counter.rows := Counter.all db in
match rows as self in Counter.rows return Counter with
| Counter.nil => tuple (0, 0)
| Counter.cons head tail => head
"""
EXPECTED = b'Task { title: "updated", id: 3, completed: true, value: 122 }\n'


class All(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="lanyard-all-")
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)

    def invoke(self, text, *arguments):
        source = self.work / "program.lan"
        source.write_text(text)
        return subprocess.run([str(DRIVER), *arguments, str(source)], cwd=ROOT,
                              capture_output=True, timeout=120)

    def success(self, text, output, model="Counter"):
        result = self.invoke(text, "run", "--print-model", model)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, output, b""))

    def test_all_scalars_and_nonleading_key(self):
        self.success((ROOT / "test/fixtures/all.lan").read_text(), EXPECTED, "Task")

    def test_empty(self):
        self.success(BASE + "def main : Counter := " + OPEN + CHOOSE,
                     b"Counter { id: 0, value: 0 }\n")

    def test_numeric_order_and_key_limits(self):
        for keys in [(20, 3, 7), (9223372036854775807, 1, 0)]:
            with self.subTest(keys=keys):
                creates = "".join(f"let row{index} : Counter := Counter.create (tuple ({key}, 42)) db in\n"
                                  for index, key in enumerate(keys))
                self.success(BASE + "def main : Counter := " + OPEN + creates + CHOOSE,
                             f"Counter {{ id: {min(keys)}, value: 42 }}\n".encode())

    def test_complete_list_and_alias(self):
        definitions = """def fetch : Db -> Counter.rows := Counter.all
def rec digits : Counter.rows -> Nat -> Nat := fun (rows : Counter.rows) (acc : Nat) =>
  match rows as self in Counter.rows return Nat with
  | Counter.nil => acc
  | Counter.cons head tail => digits tail (natAdd (natMul acc 100) head.0)
"""
        creates = "".join(f"let row{key} : Counter := Counter.create (tuple ({key}, 42)) db in\n"
                          for key in (20, 3, 7))
        self.success(BASE + definitions + "def main : Counter := " + OPEN + creates
                     + "tuple (0, digits (fetch db) 0)", b"Counter { id: 0, value: 30720 }\n")

    def test_model_and_connection_isolation(self):
        text = BASE + "model Other with | id : Nat | value : Nat end\n"
        text += "def main : Counter := " + OPEN.replace("Db.connect Counter", "Db.connect (prod (Counter, Other))")
        text += "let other : Other := Other.create (tuple (0, 999)) db in\n"
        text += "let mine : Counter := Counter.create (tuple (7, 42)) db in\n"
        text += 'let db2 : Db := Db.connect Counter Bytes b"sqlite::memory:" in\n'
        text += "let ready2 : prod () := Db.push_schema db2 in\n"
        text += "let foreign : Counter := Counter.create (tuple (1, 888)) db2 in\n" + CHOOSE
        self.success(text, b"Counter { id: 7, value: 42 }\n")

    def test_key_only_model(self):
        text = BASE.replace("| value : Nat ", "") + "def main : Counter := " + OPEN
        text += "let created : Counter := Counter.create (tuple (7)) db in\n"
        self.success(text + CHOOSE.replace("tuple (0, 0)", "tuple (0)"), b"Counter { id: 7 }\n")

    def test_closure(self):
        definitions = """def capture : Db -> prod (Nat -> Counter.rows) := fun (db : Db) =>
tuple (fun (ignored : Nat) => Counter.all db)
"""
        text = BASE + definitions + "def main : Counter := " + OPEN
        text += "let created : Counter := Counter.create (tuple (7, 42)) db in\n"
        text += "let fetch : Nat -> Counter.rows := (capture db).0 in\n"
        self.success(text + CHOOSE.replace("Counter.all db", "fetch 0"), b"Counter { id: 7, value: 42 }\n")

    def test_schema_required_even_when_result_is_unused(self):
        text = BASE + "def main : Counter := " + OPEN.replace("let ready : prod () := Db.push_schema db in\n", "")
        text += "let ignored : Counter.rows := Counter.all db in tuple (0, 0)"
        result = self.invoke(text, "run")
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"schema has not been initialized", result.stderr)

    def test_request_shared_context(self):
        text = BASE + "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => "
        text += "let db : Db := topcoat.db cx in let ready : prod () := Db.push_schema db in "
        text += "let created : Counter := Counter.create (tuple (7, 42)) db in "
        text += "let rows : Counter.rows := Counter.all (topcoat.db cx) in "
        text += "match rows as self in Counter.rows return SeeOther with "
        text += "| Counter.nil => let missing : Counter := Counter.get_by_id 99 db in topcoat.see_other uri "
        text += "| Counter.cons head tail => topcoat.see_other uri"
        result = self.invoke(text, "run", "--request", "/listed")
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, b"HTTP/1.1 303 See Other\r\nLocation: /listed\r\nContent-Length: 0\r\n\r\n", b""))

    def test_generated_name_collisions_are_rejected(self):
        for name in ("rows", "nil", "cons", "all"):
            for source in (f"def Counter_{name} : Nat := 0\n" + BASE,
                           BASE + f"def Counter_{name} : Nat := 0\n"):
                with self.subTest(name=name, source=source):
                    result = self.invoke(source, "check")
                    self.assertEqual((result.returncode, result.stdout), (1, b""))
                    self.assertIn(b"duplicate declaration", result.stderr)

    def test_wrong_list_type_is_rejected(self):
        text = BASE + "model Other with | id : Nat | value : Nat end\n"
        text += "def main : Db -> Other.rows := fun (db : Db) => Counter.all db"
        result = self.invoke(text, "check")
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"mismatch", result.stderr)

    def test_crate_retains_ordering_and_checked_conversion(self):
        destination = self.work / "crate"
        result = self.invoke((ROOT / "test/fixtures/all.lan").read_text(), "emit", "--crate",
                             str(destination), "--print-model", "Task")
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        source = (destination / "src/main.rs").read_text()
        self.assertIn("::all().order_by(", source)
        self.assertIn(".id().asc()).exec(&mut __lan_db).await?", source)
        self.assertIn("__lan_rows.into_iter().rev().try_fold(", source)
        self.assertIn("lan_model_from_i64(__lan_row.id)?", source)


if __name__ == "__main__":
    unittest.main()
