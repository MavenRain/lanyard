"""Exercise the actual run command, model state, input checks and refusals."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "_build/default/bin/lanyard.exe"
BYTES = "mu Bytes : Type 0 := | bytesNil : Bytes | bytesCons (head : Nat) (tail : Bytes) : Bytes\n"
MODELS = BYTES + "model Counter with | id : Nat | value : Nat end\n"
CONNECT = 'let db : Db := Db.connect Counter Bytes b"sqlite::memory:" in '
READY = "let ready : prod () := Db.push_schema db in "
CREATE = "let created : Counter := Counter.create (tuple (1, 23)) db in "


class Run(unittest.TestCase):
    def setUp(self):
        (ROOT / ".gatework").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="run-cli-", dir=ROOT / ".gatework")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "program.lan"

    def invoke(self, *arguments, env=None):
        return subprocess.run([str(EXE), "run", *map(str, arguments)], cwd=self.directory,
                              env=env, capture_output=True, text=True, timeout=20)

    def program(self, text, *options):
        self.source.write_text(text)
        return self.invoke(*options, self.source)

    def success(self, result, output=""):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, output)
        self.assertEqual(result.stderr, "")

    def refusal(self, result, message, code=1):
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn(message, result.stderr)

    def counter(self, body, *options):
        return self.program(MODELS + "def main : Counter := " + body, *options)

    def test_todo(self):
        self.success(self.invoke("--print-model", "Todo", ROOT / "corpus/m0/todo.lan"),
                     'Todo { id: 1, title: "hi", completed: false }\n')

    def test_discard(self):
        self.success(self.invoke(ROOT / "corpus/m0/todo.lan"))

    def test_get_after_create_and_shared_alias(self):
        self.success(self.counter(CONNECT + READY + CREATE +
            "let alias : Db := db in Counter.get_by_id 1 alias", "--print-model", "Counter"),
            "Counter { id: 1, value: 23 }\n")

    def test_repeated_schema_keeps_rows(self):
        self.success(self.counter(CONNECT + READY + CREATE +
            "let again : prod () := Db.push_schema db in Counter.get_by_id 1 db",
            "--print-model", "Counter"),
            "Counter { id: 1, value: 23 }\n")

    def test_left_to_right_arguments(self):
        # The lookup in the second field observes the creation in the first.
        self.success(self.counter(CONNECT + READY +
            "let pair : prod (Counter, Counter) := tuple (Counter.create (tuple (1, 23)) db, "
            "Counter.get_by_id 1 db) in pair.1", "--print-model", "Counter"),
            "Counter { id: 1, value: 23 }\n")

    def test_function_effects(self):
        self.success(self.program(MODELS +
            "def save : Db -> Counter := fun (db : Db) => Counter.create (tuple (1, 23)) db\n"
            "def main : Counter := " + CONNECT + READY +
            "let saved : Counter := save db in Counter.get_by_id 1 db", "--print-model", "Counter"),
            "Counter { id: 1, value: 23 }\n")

    def test_duplicate_key(self):
        self.refusal(self.counter(CONNECT + READY + CREATE + "Counter.create (tuple (1, 99)) db"),
                     "duplicate model key")

    def test_distinct_keys(self):
        self.success(self.counter(CONNECT + READY + CREATE +
            "let second : Counter := Counter.create (tuple (2, 99)) db in Counter.get_by_id 1 db",
            "--print-model", "Counter"), "Counter { id: 1, value: 23 }\n")

    def test_missing_row(self):
        self.refusal(self.counter(CONNECT + READY + "Counter.get_by_id 1 db"), "model row not found")

    def test_schema_required(self):
        self.refusal(self.counter(CONNECT + "Counter.create (tuple (1, 23)) db"), "schema has not been initialized")

    def test_separate_connections(self):
        self.refusal(self.counter(CONNECT + READY + CREATE +
            'let other : Db := Db.connect Counter Bytes b"sqlite::memory:" in '
            "let initialized : prod () := Db.push_schema other in Counter.get_by_id 1 other"),
            "model row not found")

    def test_fresh_runs(self):
        for _iteration in range(2):
            self.success(self.counter(CONNECT + READY + "Counter.create (tuple (1, 23)) db"))

    def test_multiple_model_tables(self):
        source = MODELS + "model Other with | id : Nat | value : Nat end\n"
        self.success(self.program(source + "def main : Counter := "
            'let db : Db := Db.connect (prod (Counter, Other)) Bytes b"sqlite::memory:" in ' + READY + CREATE +
            "let other : Other := Other.create (tuple (1, 99)) db in Counter.get_by_id 1 db",
            "--print-model", "Counter"), "Counter { id: 1, value: 23 }\n")

    def test_unregistered_model(self):
        self.refusal(self.program(MODELS + "model Other with | id : Nat end\n"
            "def main : Other := " + CONNECT + READY + "Other.create (tuple (1)) db"), "model not registered")

    def test_url_has_no_external_effect(self):
        marker = self.directory / "must-not-exist.sqlite"
        self.refusal(self.counter(CONNECT.replace("sqlite::memory:", "sqlite:" + str(marker)) +
            READY + "Counter.create (tuple (1, 23)) db"), "requires sqlite::memory:")
        self.assertFalse(marker.exists())

    def test_model_range(self):
        for field in ("9223372036854775808, 1", "1, 9223372036854775808"):
            with self.subTest(field=field):
                self.refusal(self.counter(CONNECT + READY + "Counter.create (tuple (" + field + ")) db"),
                             "outside i64 range")
        self.success(self.counter(CONNECT + READY + "Counter.create (tuple (9223372036854775807, 0)) db",
            "--print-model", "Counter"), "Counter { id: 9223372036854775807, value: 0 }\n")

    def test_invalid_text(self):
        todo = (ROOT / "corpus/m0/todo.lan").read_text()
        for value, error in (("bytesCons 256 bytesNil", "byte outside"),
                             ("bytesCons 255 bytesNil", "invalid UTF-8")):
            with self.subTest(value=value):
                self.refusal(self.program(todo.replace('b"hi"', "(" + value + ")")), error)

    def test_boolean_and_text_output(self):
        todo = (ROOT / "corpus/m0/todo.lan").read_text()
        self.success(self.program(todo.replace("inj 0 of 2 ()", "inj 1 of 2 ()")
            .replace('b"hi"', 'b"a\\n\\\"b"'), "--print-model", "Todo"),
            'Todo { id: 1, title: "a\\n\\\"b", completed: true }\n')

    def test_finite_handler(self):
        self.success(self.invoke(ROOT / "test/fixtures/handlers.lan"))
        self.success(self.invoke("--print-model", "Row", ROOT / "test/fixtures/handlers-db.lan"),
                     'Row { id: 4, title: "fourth" }\n')

    def test_existing_native_fixtures(self):
        cases = [
            ("native-closures.lan", "captureOrder", 14),
            ("native-closures.lan", "nestedCapture", 28),
            ("native-closures.lan", "higherOrder", 41),
            ("native-closures.lan", "nullary", 29),
            ("native-closures.lan", "owned", 23),
            ("native-recursive.lan", "treeTotal", 59),
            ("native-recursive.lan", "orderedTree", 383),
            ("native-recursive.lan", "mutualTotal", 4),
            ("native-recursive.lan", "erasedTotal", 43),
            ("native-recursive.lan", "functionTotal", 12),
            ("native-recursive.lan", "wrappedTotal", 72),
        ]
        for fixture, entry, expected in cases:
            with self.subTest(fixture=fixture, entry=entry):
                text = (ROOT / "test/fixtures" / fixture).read_text()
                text += "\nmodel Probe with | id : Nat | value : Nat end\n"
                text += f"def main : Probe := tuple (1, {entry})\n"
                self.success(self.program(text, "--print-model", "Probe"),
                             f"Probe {{ id: 1, value: {expected} }}\n")

    def test_runtime_axiom(self):
        self.refusal(self.program("axiom cx : Cx\ndef main : Db := topcoat.db cx"), "Rust target metadata missing: cx")

    def test_entry_errors(self):
        self.refusal(self.program("def answer : Nat := 3"), "missing runtime function main")
        self.refusal(self.program("def main : Nat -> Nat := fun (x : Nat) => x"), "requires runtime arguments")
        self.refusal(self.program("axiom main : Nat"), "missing runtime function main")
        self.refusal(self.program("def main : Nat := 3", "--print-model", "Absent"), "printed model is unknown")
        self.refusal(self.counter(CONNECT + READY + "Counter.create (tuple (1, 23)) db",
                                  "--print-model", "Absent"), "printed model is unknown")

    def test_steps(self):
        self.refusal(self.invoke("--steps", "1", ROOT / "corpus/m0/todo.lan"), "step limit exhausted")
        self.success(self.invoke("--print-model", "Todo", "--steps", "100000", ROOT / "corpus/m0/todo.lan"),
                     'Todo { id: 1, title: "hi", completed: false }\n')
        self.success(self.invoke("--steps", "100000", "--print-model", "Todo", ROOT / "corpus/m0/todo.lan"),
                     'Todo { id: 1, title: "hi", completed: false }\n')

    def test_usage(self):
        path = str(self.source)
        bad = [[], ["--steps"], ["--print-model"], ["--unknown", path], ["file.kan"], [".lan"],
               [path, path], ["--steps", "2", "--steps", "3", path],
               ["--print-model", "A", "--print-model", "B", path], [path, "--steps", "1"]]
        bad += [["--steps", value, path] for value in ("0", "-1", "1000001", "999999999999999999999", "0x10", "1_0", "", "abc")]
        for arguments in bad:
            with self.subTest(arguments=arguments):
                self.refusal(self.invoke(*arguments), "usage:", 64)

    def test_missing_and_invalid_input(self):
        self.refusal(self.invoke(self.source), "cannot read", 64)
        self.refusal(self.program("def main : Nat := ()"), "mismatch")

    def test_literal_path_and_no_cargo(self):
        marker = self.directory / "must-not-run"
        started = self.directory / "cargo-was-run"
        cargo = self.directory / "cargo"
        cargo.write_text("#!/bin/sh\ntouch " + shlex.quote(str(started)) + "\nexit 93\n")
        cargo.chmod(0o755)
        path = self.directory / "space ' $(touch must-not-run).lan"
        path.write_text("def main : Nat := 1")
        self.success(self.invoke(path, env={**os.environ, "PATH": str(self.directory)}))
        self.assertFalse(marker.exists())
        self.assertFalse(started.exists())
        self.assertFalse((self.directory / "Cargo.toml").exists())


if __name__ == "__main__":
    unittest.main()
