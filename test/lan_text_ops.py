"""Compare checked text operations in the interpreter and emitted Rust."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = """mu Bytes : Type 0 :=
| nil : Bytes
| cons (head : Nat) (tail : Bytes) : Bytes
def Bool : Type 0 := sum ((prod () : Type 0), (prod () : Type 0))
def truth : Bool -> Nat := fun (b : Bool) => case b with
| 0 (u : prod ()) => 0
| 1 (u : prod ()) => 1
def trim : Bytes -> Bytes := Text.trim Bytes
def empty : Bytes -> Bool := Text.is_empty Bytes
"""
WHITESPACE = [*range(9, 14), 0x20, 0x85, 0xA0, 0x1680, *range(0x2000, 0x200B),
              0x2028, 0x2029, 0x202F, 0x205F, 0x3000]
CASES = [("", ""), (" \t\r\n", ""), ("  hello  world  ", "hello  world"),
         ("\u00a0\u3000café\u2028", "café"), (" 🦀\0 ", "🦀\0"),
         (" \u180e\u200b\ufeff ", "\u180e\u200b\ufeff"),
         (" \x1c\x1d\x1e\x1f ", "\x1c\x1d\x1e\x1f"), ("a\nb", "a\nb")]
CASES += [(chr(point) + "x" + chr(point), "x") for point in WHITESPACE]
BAD = [("range", [256], "ModelByteRange"), ("invalid_utf8", [255], "ModelUtf8"),
       ("truncated", [226, 128], "ModelUtf8"), ("overlong", [192, 128], "ModelUtf8"),
       ("surrogate", [237, 160, 128], "ModelUtf8"),
       ("above_unicode", [244, 144, 128, 128], "ModelUtf8")]


def literal(values):
    result = "nil"
    for value in reversed(values):
        result = f"(cons {value} {result})"
    return result


def function(name):
    return "f_" + name.encode().hex()


def run(*arguments):
    return subprocess.run([str(arg) for arg in arguments], cwd=ROOT,
                          text=True, capture_output=True, timeout=600)


class TextOperations(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="lanyard-text-ops-")
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)

    def source(self, body):
        path = self.work / "program.lan"
        path.write_text(BASE + body)
        return path

    def test_fixture(self):
        result = run(DRIVER, "run", "--print-model", "Title", "test/fixtures/text-ops.lan")
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, 'Title { id: 1, text: "write tests", blank: true }\n', ""))

    def test_invalid_encodings(self):
        for name, values, _error in BAD:
            for operation, result_type in [("trim", "Bytes"), ("empty", "Bool")]:
                with self.subTest(name=name, operation=operation):
                    path = self.source(f"def main : {result_type} := {operation} {literal(values)}\n")
                    checked = run(DRIVER, "check", path)
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    result = run(DRIVER, "run", path)
                    self.assertEqual(result.returncode, 1, result)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("outside 0..255" if name == "range" else "invalid UTF-8", result.stderr)

    def test_bad_layouts_fail_in_both_backends(self):
        for operation in ["trim", "is_empty"]:
            with self.subTest(operation=operation):
                result_type = "Nat" if operation == "trim" else "Bool"
                path = self.source(f"def main : {result_type} := Text.{operation} Nat 1\n")
                for command in [("run",), ("emit", "--target")]:
                    result = run(DRIVER, *command, path)
                    self.assertEqual(result.returncode, 1, result)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("byte list", result.stderr)

    def test_native_roundtrip(self):
        declarations, checks, expected = [], [], []
        text_to = "lan_model_text_to_" + b"Bytes".hex()
        for index, (text, trimmed) in enumerate(CASES):
            data = literal(list(text.encode()))
            for name, ty, expression in [
                (f"trim{index}", "Bytes", f"trim {data}"),
                (f"empty{index}", "Nat", f"truth (empty {data})"),
                (f"blank{index}", "Nat", f"truth (empty (Text.trim Bytes {data}))"),
            ]:
                declarations.append(f"def {name} : {ty} := {expression}\n")
                if ty == "Bytes":
                    checks.append(f'    let value = {function(name)}()?;\n'
                                  f'    let value = {text_to}(&value)?;\n'
                                  f'    println!("{name}={{}}", value.as_bytes().iter().map(u8::to_string)'
                                  '.collect::<Vec<_>>().join(","));\n')
                    expected.append(name + "=" + ",".join(str(byte) for byte in trimmed.encode()))
                else:
                    checks.append(f'    println!("{name}={{}}", lan_model_to_i64(&{function(name)}()?)?);\n')
                    empty = text == "" if name.startswith("empty") else trimmed == ""
                    expected.append(f"{name}={int(empty)}")
        for label, values, error in BAD:
            for operation, ty in [("trim", "Bytes"), ("empty", "Bool")]:
                name = operation + label
                declarations.append(f"def {name} : {ty} := {operation} {literal(values)}\n")
                checks.append(f'    println!("{name}={{}}", {function(name)}().map_or_else('
                              '|error| format!("{error:?}"), |_value| "accepted".to_owned()));\n')
                expected.append(f"{name}={error}")
        path = self.source("".join(declarations))
        emitted = run(DRIVER, "emit", "--target", path)
        self.assertEqual(emitted.returncode, 0, emitted.stderr)
        self.assertEqual(emitted.stderr, "")
        native = self.work / "text.rs"
        native.write_text(emitted.stdout + '\nfn main() -> Result<(), Error> {\n'
                          + "".join(checks) + '    Ok(())\n}\n')
        binary = self.work / "text"
        initialized = run("git", "init", "--quiet", self.work)
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        compiled = run("gateledger", "run", "--ledger", ROOT / ".gatework/gateledger",
                       "--dir", self.work, "--scope", "text.rs", "--toolchain", "1.98", "--",
                       "rustup", "run", "1.98", "rustc", "--edition", "2024", native, "-o", binary)
        self.assertEqual(compiled.returncode, 0, compiled.stderr)
        result = run(binary)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.splitlines(), expected)
        print(f"LAN-TEXT-NATIVE OK observations={len(expected)}")


if __name__ == "__main__":
    unittest.main()
