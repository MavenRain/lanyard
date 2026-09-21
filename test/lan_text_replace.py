"""Compare replacement semantics, validation and evaluation across both runtimes."""
import argparse
import itertools
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = """mu Bytes : Type 0 :=
| bytesNil : Bytes
| bytesCons (head : Nat) (tail : Bytes) : Bytes
def replace : Bytes -> Bytes -> Bytes -> Bytes := Text.replace Bytes
"""
HANDLER = "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => "
TEXTS = ["", "a", "A", " a ", "ababa", "aaaaa", "a\0b\0", "caféé", "e\u0301", "日本語", "a🦀b", "\r\n"]
NEEDLES = ["", "a", "aa", "aba", "z", "\0", "é", "🦀", "\n"]
CASES = list(itertools.product(TEXTS, NEEDLES, ["", "x", "aa", "é\0"]))
CASES += [("ababababac", "ababac", "X"), ("a" * 4096 + "b", "a" * 256 + "b", "X"),
          ("a" * 4096, "a" * 256 + "b", "X")]
COMPUTED = [
    ("captured", 'let r : Bytes := b"x" in let f : Bytes -> Bytes := '
     'fun (t : Bytes) => replace t b"a" r in f b"aba"', "xbx"),
    ("composed", 'replace (Text.trim Bytes b" aba ") (Text.concat Bytes b"a" b"b") b"x"', "xa"),
    ("shared", 'let t : Bytes := b"same" in replace t t t', "same"),
    ("unused", 'let ignored : Bytes := replace b"a" b"a" b"aa" in b"ok"', "ok"),
]
ERRORS = []
for position in range(3):
    for kind, expression, error in [("byte", "bytesCons 256 bytesNil", "ModelByteRange"),
                                    ("utf8", "bytesCons 255 bytesNil", "ModelUtf8")]:
        arguments = ['b"abc"', 'b"z"', 'b"x"']
        arguments[position] = f"({expression})"
        call = "replace " + " ".join(arguments)
        ERRORS += [(f"{kind}{position}", call, error),
                   (f"unused_{kind}{position}", f'let ignored : Bytes := {call} in b"ok"', error)]
ERRORS += [
    ("empty_needle", 'replace (bytesCons 255 bytesNil) b"" b""', "ModelUtf8"),
    ("empty_text", 'replace b"" (bytesCons 255 bytesNil) b""', "ModelUtf8"),
    ("empty_both", 'replace b"" b"" (bytesCons 255 bytesNil)', "ModelUtf8"),
    ("invalid_tail", 'replace (bytesCons 97 (bytesCons 255 bytesNil)) b"a" b"x"', "ModelUtf8"),
    ("first_error", 'replace (bytesCons 256 bytesNil) (bytesCons 255 bytesNil) b"x"', "ModelByteRange"),
    ("second_error", 'replace b"abc" (bytesCons 256 bytesNil) (bytesCons 255 bytesNil)', "ModelByteRange"),
]
ORDERED = """def first : Bytes := b"aba"
def second : Bytes := b"a"
def third : Bytes := b"x"
def badfirst : Bytes := bytesCons 255 bytesNil
def ordered : Bytes := replace first second third
def unused_ordered : Bytes := let ignored : Bytes := replace first second third in b"ok"
def ordered_bad : Bytes := replace badfirst second third
mu Other : Type 0 := | otherNil : Other | otherCons (head : Nat) (tail : Other) : Other
def alternate : Other := Text.replace Other
  (otherCons 97 (otherCons 98 (otherCons 97 otherNil)))
  (otherCons 97 otherNil) (otherCons 120 otherNil)
"""


CLI_BUDGET = 60  # one driver, git init or compiled-binary call
BUILD_BUDGET = 180  # one gateledger rustc compile


def run(*args, cwd=ROOT, budget=CLI_BUDGET):
    return subprocess.run([str(arg) for arg in args], cwd=cwd, capture_output=True, timeout=budget)


def require(result):
    if result.returncode != 0 or result.stderr:
        sys.exit(f"LAN-TEXT-REPLACE FAIL {result.returncode}: {result.stdout!r} {result.stderr!r}")
    return result.stdout.decode()


def response(body):
    encoded = body.encode()
    return (f"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(encoded)}\r\n\r\n").encode() + encoded


def rust_string(value):
    escapes = {'"': '\\"', '\\': '\\\\'}
    return '"' + ''.join(escapes.get(char, f"\\u{{{ord(char):x}}}" if ord(char) < 32
                                   or ord(char) == 127 else char) for char in value) + '"'


def source():
    return BASE + "".join(f"def {name} : Bytes := {expression}\n"
                          for name, expression, _expected in COMPUTED + ERRORS) + ORDERED


def native_harness():
    cases = ",\n".join("(" + ", ".join(map(rust_string, (text, needle, replacement,
                         text.replace(needle, replacement)))) + ")" for text, needle, replacement in CASES)
    checks = "".join(f'println!("COMPUTED {name} {{}}", observe(f_{name.encode().hex()}()'
                     '.and_then(|text| lan_model_text_to_4279746573(&text)), '
                     f'{rust_string(expected)}));\n' for name, _expression, expected in COMPUTED)
    checks += "".join(f'println!("ERROR {name} {{}}", matches!(f_{name.encode().hex()}(), '
                      f'Err(Error::{error})));\n' for name, _expression, error in ERRORS)
    for name, expected in [("ordered", "xbx"), ("unused_ordered", "ok")]:
        checks += f'let actual = f_{name.encode().hex()}();\n'
        checks += f'println!("ORDER {name} {{}}", observe(actual.and_then(|text| lan_model_text_to_4279746573(&text)), "{expected}"));\n'
    checks += 'let actual = f_6f7264657265645f626164();\nprintln!("ORDER bad {}", matches!(actual, Err(Error::ModelUtf8)));\n'
    checks += 'println!("ALTERNATE {}", observe(f_616c7465726e617465().and_then(|text| lan_model_text_to_4f74686572(&text)), "xbx"));\n'
    return """
fn observe(value: Result<String, Error>, expected: &str) -> bool {
    value.map(|text| text == expected).unwrap_or(false)
}
fn main() {
    let cases = [
""" + cases + """
    ];
    cases.iter().enumerate().for_each(|(index, (text, needle, replacement, expected))| {
        let actual = f_7265706c616365(
            Arc::new(lan_model_text_from_4279746573(text.to_string())),
            Arc::new(lan_model_text_from_4279746573(needle.to_string())),
            Arc::new(lan_model_text_from_4279746573(replacement.to_string())));
        println!("CASE{index} {}", observe(actual.and_then(|text| lan_model_text_to_4279746573(&text)), expected));
    });
""" + checks + "}\n"


def expected_native():
    return ([f"CASE{index} true" for index in range(len(CASES))]
            + [f"COMPUTED {name} true" for name, _expression, _expected in COMPUTED]
            + [f"ERROR {name} true" for name, _expression, _error in ERRORS]
            + ["FIRST SECOND THIRD ORDER ordered true", "FIRST SECOND THIRD ORDER unused_ordered true",
               "BADFIRST SECOND THIRD ORDER bad true", "ALTERNATE true"])


def emit(work):
    program = work / "native.lan"
    program.write_text(source())
    emitted = require(run(DRIVER, "emit", "--target", program))
    # Instrument argument producers to observe order and counts in compiled code.
    for name in ["first", "second", "third", "badfirst"]:
        pattern = rf"(fn f_{name.encode().hex()}\(\)[^\n]*\{{)"
        emitted, count = re.subn(pattern, lambda match: match[0] + f' print!("{name.upper()} ");', emitted)
        if count != 1:
            sys.exit(f"LAN-TEXT-REPLACE FAIL instrumentation target {name}: {count}")
    return emitted


def compile_native(work, emitted, name):
    program, binary = work / f"{name}.rs", work / name
    program.write_text(emitted + native_harness())
    require(run("git", "init", "--quiet", work))
    built = run("gateledger", "run", "--ledger", ROOT / ".gatework/gateledger", "--dir", work,
                "--scope", program.name, "--toolchain", "1.98", "--", "rustup", "run", "1.98",
                "rustc", "--edition", "2024", program, "-o", binary, budget=BUILD_BUDGET)
    if built.returncode != 0:
        sys.exit(f"LAN-TEXT-REPLACE FAIL native build: {built.stdout!r} {built.stderr!r}")
    return run(binary)


class TextReplace(unittest.TestCase):
    def setUp(self):
        (ROOT / ".gatework").mkdir(exist_ok=True)
        directory = tempfile.TemporaryDirectory(prefix="text-replace-", dir=ROOT / ".gatework")
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)

    def test_interpreter_cases(self):
        fixture = ROOT / "test/fixtures/text-replace.lan"
        for text, needle, replacement in CASES:
            with self.subTest(text=text, needle=needle, replacement=replacement):
                actual = run(DRIVER, "run", "--request", "/", "--form",
                             urlencode({"text": text, "needle": needle, "replacement": replacement}), fixture)
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (0, response(text.replace(needle, replacement)), b""))

    def test_computed_and_alternate_family(self):
        program = self.work / "computed.lan"
        for family in ["Bytes", "TextList"]:
            for name, _expression, expected in COMPUTED:
                with self.subTest(family=family, name=name):
                    program.write_text((source() + HANDLER + f"Response.text Bytes {name}\n")
                                       .replace("Bytes", family))
                    actual = run(DRIVER, "run", "--request", "/", program)
                    self.assertEqual((actual.returncode, actual.stdout, actual.stderr), (0, response(expected), b""))
                    require(run(DRIVER, "emit", "--target", program))

    def test_invalid_inputs_and_unused_results(self):
        program = self.work / "error.lan"
        for name, _expression, error in ERRORS:
            with self.subTest(name=name):
                program.write_text(source() + HANDLER + f"Response.text Bytes {name}\n")
                actual = run(DRIVER, "run", "--request", "/", program)
                self.assertEqual((actual.returncode, actual.stdout), (1, b""))
                self.assertIn(b"UTF-8" if error == "ModelUtf8" else b"0..255", actual.stderr)

    def test_effectful_arguments(self):
        fixture = (ROOT / "test/fixtures/text-replace-order.lan").read_text()
        program = self.work / "order.lan"
        for unused in [False, True]:
            with self.subTest(unused=unused):
                current = fixture.replace('Text.concat Bytes changed', 'Text.concat Bytes b"unused"') if unused else fixture
                program.write_text(current)
                actual = run(DRIVER, "run", "--request", "/", program)
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (0, response(("unused" if unused else "xbx") + ":onceeachx"), b""))
                require(run(DRIVER, "emit", "--target", program))
                omitted = current.replace("  let changed : Bytes := Text.replace Bytes (first db) (second db) (third db) in\n", "")
                if unused:
                    program.write_text(omitted)
                    control = run(DRIVER, "run", "--request", "/", program)
                    self.assertEqual((control.returncode, control.stdout), (1, b""))
                    self.assertIn(b"model row not found", control.stderr)

    def test_refusal_before_output(self):
        program, destination = self.work / "bad.lan", self.work / "crate"
        for declaration in ["def main : Nat := Text.replace Nat 1 2 3",
                            'def main : Bytes := Text.replace Bytes b"a" b"a" 1',
                            'def main : Bytes := let f : Bytes -> Bytes := Text.replace Bytes b"a" b"a" in f b"b"']:
            with self.subTest(declaration=declaration):
                program.write_text(BASE + declaration)
                actual = run(DRIVER, "emit", "--crate", destination, program)
                self.assertEqual((actual.returncode, actual.stdout), (1, b""))
                self.assertFalse(destination.exists())

    def test_native(self):
        actual = compile_native(self.work, emit(self.work), "clean")
        self.assertEqual((actual.returncode, actual.stderr), (0, b""))
        self.assertEqual(actual.stdout.decode().splitlines(), expected_native())
        print(f"LAN-TEXT-REPLACE NATIVE OK observations={len(expected_native())}")


def mutations():
    call = "__lan_text.replace(__lan_needle.as_str(), __lan_replacement.as_str())"
    changes = [
        ("first_only", call, "__lan_text.replacen(__lan_needle.as_str(), __lan_replacement.as_str(), 1)"),
        ("swapped", call, "__lan_text.replace(__lan_replacement.as_str(), __lan_needle.as_str())"),
        ("empty_noop", call, f"if __lan_needle.is_empty() {{ __lan_text }} else {{ {call} }}"),
    ]
    changes += [(f"unchecked_{name}", f"let __lan_{name} = lan_model_text_to_4279746573(&__lan_{name}_arg)?;",
                 f"let __lan_{name} = lan_model_text_to_4279746573(&__lan_{name}_arg).unwrap_or_default();")
                for name in ["text", "needle", "replacement"]]
    (ROOT / ".gatework").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="text-replace-mut-", dir=ROOT / ".gatework") as directory:
        work = Path(directory)
        emitted = emit(work)
        expected = expected_native()
        sentinel = {"first_only": f"CASE{CASES.index(('ababa', 'a', 'x'))} false",
                    "swapped": f"CASE{CASES.index(('ababa', 'a', 'x'))} false",
                    "empty_noop": f"CASE{CASES.index(('a', '', 'x'))} false",
                    "unchecked_text": "ERROR byte0 false", "unchecked_needle": "ERROR byte1 false",
                    "unchecked_replacement": "ERROR byte2 false"}
        for name in ["clean", "restored"]:
            if name == "restored":
                for label, before, after in changes:
                    if before not in emitted:
                        sys.exit(f"LAN-TEXT-REPLACE FAIL mutation target missing: {label}")
                    actual = compile_native(work, emitted.replace(before, after), label)
                    rows = actual.stdout.decode().splitlines()
                    if actual.returncode != 0 or actual.stderr or len(rows) != len(expected) or sentinel[label] not in rows:
                        sys.exit(f"LAN-TEXT-REPLACE FAIL mutation not killed by observations: {label} {actual.stderr!r}")
                    print(f"LAN-TEXT-REPLACE MUT OK {label}")
            actual = compile_native(work, emitted, name)
            if actual.returncode != 0 or actual.stderr or actual.stdout.decode().splitlines() != expected:
                sys.exit(f"LAN-TEXT-REPLACE FAIL mutation baseline: {name}")
            print(f"LAN-TEXT-REPLACE MUT OK {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutations", action="store_true")
    args = parser.parse_args()
    if args.mutations:
        mutations()
    else:
        unittest.main(argv=[__file__], failfast=True)
