"""Check substring search, Boolean branching, failures and native semantics."""
import argparse
import itertools
from pathlib import Path
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
def Bool : Type 0 := sum ((prod () : Type 0), (prod () : Type 0))
def same : Bytes -> Bytes -> Bool := Text.contains Bytes
def label : Bool -> Bytes := fun (value : Bool) =>
  case value with | 0 (u : prod ()) => b"no" | 1 (u : prod ()) => b"yes"
def compare : Bytes -> Bytes -> Bytes := fun (left : Bytes) (right : Bytes) => label (same left right)
"""
HANDLER = "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => "
VALUES = ["", "a", "A", " a", "a ", "ab", "ac", "\0", "a\0b", "a\0c",
          "café", "é", "e\u0301", "🦀", "\r\n", "x" * 96]
PAIRS = list(itertools.product(VALUES, repeat=2))
PAIRS += [("prefix-tail", "prefix"), ("prefix-tail", "tail"), ("prefix-tail", "fix-ta"),
          ("ababababac", "ababac"), ("aaaaab", "aaab"), ("aaaaab", "aaac"),
          ("日本語", "本"), ("a🦀b", "🦀"), ("a\0b", "\0b"),
          ("a" * 4096 + "b", "a" * 256 + "b"), ("a" * 4096, "a" * 256 + "b")]
COMPUTED = [
    ("captured", 'let left : Bytes := b"x" in let f : Bytes -> Bool := '
     'fun (right : Bytes) => same left right in label (f b"x")', "yes"),
    ("composed", 'compare (Text.trim Bytes b" xy ") (Text.concat Bytes b"x" b"y")', "yes"),
    ("shared", 'let text : Bytes := b"shared" in compare text text', "yes"),
    ("unused", 'let ignored : Bool := same b"x" b"y" in b"ok"', "ok"),
]
ERRORS = [
    ("left_byte", 'label (same (bytesCons 256 bytesNil) b"x")', "ModelByteRange"),
    ("right_byte", 'label (same b"x" (bytesCons 256 bytesNil))', "ModelByteRange"),
    ("left_utf8", 'label (same (bytesCons 255 bytesNil) b"x")', "ModelUtf8"),
    ("right_utf8", 'label (same b"x" (bytesCons 255 bytesNil))', "ModelUtf8"),
    ("both_utf8", 'label (same (bytesCons 255 bytesNil) (bytesCons 255 bytesNil))', "ModelUtf8"),
    ("unused_error", 'let ignored : Bool := same b"x" (bytesCons 255 bytesNil) in b"ok"', "ModelUtf8"),
    ("empty_needle", 'label (same (bytesCons 255 bytesNil) b"")', "ModelUtf8"),
    ("empty_text", 'label (same b"" (bytesCons 255 bytesNil))', "ModelUtf8"),
    ("empty_byte", 'label (same (bytesCons 256 bytesNil) b"")', "ModelByteRange"),
]
MUTANTS = [
    ("equality", "__lan_text.contains(__lan_needle.as_str())", "__lan_text == __lan_needle"),
    ("prefix", "__lan_text.contains(__lan_needle.as_str())", "__lan_text.starts_with(__lan_needle.as_str())"),
    ("reversed", "__lan_text.contains(__lan_needle.as_str())", "__lan_needle.contains(__lan_text.as_str())"),
    ("nonempty", "__lan_text.contains(__lan_needle.as_str())",
     "!__lan_needle.is_empty() && __lan_text.contains(__lan_needle.as_str())"),
    ("unchecked_needle", "let __lan_needle = lan_model_text_to_4279746573(&__lan_needle_arg)?;",
     "let __lan_needle = lan_model_text_to_4279746573(&__lan_needle_arg).unwrap_or_default();"),
]


def run(*args, cwd=ROOT):
    return subprocess.run([str(arg) for arg in args], cwd=cwd, capture_output=True, timeout=180)


def require(result):
    if result.returncode != 0 or result.stderr:
        sys.exit(f"LAN-TEXT-CONTAINS FAIL: {result.stdout!r} {result.stderr!r}")
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
                          for name, expression, _expected in COMPUTED + ERRORS)


def native_harness():
    pairs = ",\n".join(f"({rust_string(left)}, {rust_string(right)}, "
                       f"{rust_string('yes' if right in left else 'no')})" for left, right in PAIRS)
    checks = "".join(f'    println!("COMPUTED {name} {{}}", observe(f_{name.encode().hex()}()'
                     '.and_then(|text| lan_model_text_to_4279746573(&text)), '
                     f'{rust_string(expected)}));\n' for name, _expression, expected in COMPUTED)
    checks += "".join(f'    println!("ERROR {name} {{}}", matches!(f_{name.encode().hex()}(), '
                      f'Err(Error::{error})));\n' for name, _expression, error in ERRORS)
    return """
fn observe(value: Result<String, Error>, expected: &str) -> bool {
    value.map(|text| text == expected).unwrap_or(false)
}
fn main() {
    let cases = [
""" + pairs + """
    ];
    cases.iter().enumerate().for_each(|(index, (left, right, expected))| {
        let actual = f_636f6d70617265(
            Arc::new(lan_model_text_from_4279746573(left.to_string())),
            Arc::new(lan_model_text_from_4279746573(right.to_string())));
        println!("PAIR{index} {}", observe(actual.and_then(|text| lan_model_text_to_4279746573(&text)), expected));
    });
""" + checks + "}\n"


def expected_native():
    return ([f"PAIR{index} true" for index in range(len(PAIRS))]
            + [f"COMPUTED {name} true" for name, _expression, _expected in COMPUTED]
            + [f"ERROR {name} true" for name, _expression, _error in ERRORS])


def emit(work):
    program = work / "native.lan"
    program.write_text(source())
    return require(run(DRIVER, "emit", "--target", program))


def compile_native(work, emitted, name):
    program, binary = work / f"{name}.rs", work / name
    program.write_text(emitted + native_harness())
    require(run("git", "init", "--quiet", work))
    result = run("gateledger", "run", "--ledger", ROOT / ".gatework/gateledger", "--dir", work,
                 "--scope", program.name, "--toolchain", "1.98", "--", "rustup", "run", "1.98",
                 "rustc", "--edition", "2024", program, "-o", binary)
    if result.returncode != 0:
        sys.exit(f"LAN-TEXT-CONTAINS FAIL native build: {result.stdout!r} {result.stderr!r}")
    return run(binary)


class TextContains(unittest.TestCase):
    def setUp(self):
        (ROOT / ".gatework").mkdir(exist_ok=True)
        directory = tempfile.TemporaryDirectory(prefix="text-contains-", dir=ROOT / ".gatework")
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)

    def test_form_branching(self):
        for action in ["save", "Save", "save ", "", "saved", "save\0", "保存"]:
            with self.subTest(action=action):
                actual = run(DRIVER, "run", "--request", "/", "--form", urlencode({"action": action}),
                             ROOT / "test/fixtures/text-contains.lan")
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (0, response("found" if "save" in action else "not found"), b""))

    def test_missing_form_field(self):
        actual = run(DRIVER, "run", "--request", "/", "--form", "", ROOT / "test/fixtures/text-contains.lan")
        self.assertEqual((actual.returncode, actual.stdout), (1, b""))
        self.assertIn(b"missing field", actual.stderr)

    def test_interpreter_pairs(self):
        # Use form decoding to supply arbitrary Unicode and NULs without source escaping.
        program = self.work / "pairs.lan"
        program.write_text(BASE + "def main : Cx -> Uri -> Bytes -> Response := "
                           "fun (cx : Cx) (uri : Uri) (body : Bytes) => "
                           'Response.text Bytes (compare (Form.field Bytes body b"left") '
                           '(Form.field Bytes body b"right"))\n')
        for left, right in PAIRS:
            with self.subTest(left=left, right=right):
                actual = run(DRIVER, "run", "--request", "/", "--form",
                             urlencode({"left": left, "right": right}), program)
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (0, response("yes" if right in left else "no"), b""))

    def test_computed_and_alternate_family(self):
        program = self.work / "computed.lan"
        for family in ["Bytes", "TextList"]:
            for name, _expression, expected in COMPUTED:
                with self.subTest(family=family, name=name):
                    program.write_text((source() + HANDLER + f"Response.text Bytes {name}\n")
                                       .replace("Bytes", family))
                    actual = run(DRIVER, "run", "--request", "/", program)
                    self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                     (0, response(expected), b""))
                    require(run(DRIVER, "emit", "--target", program))

    def test_failures_and_unused_results(self):
        program = self.work / "error.lan"
        for name, _expression, error in ERRORS:
            with self.subTest(name=name):
                program.write_text(source() + HANDLER + f"Response.text Bytes {name}\n")
                actual = run(DRIVER, "run", "--request", "/", program)
                self.assertEqual((actual.returncode, actual.stdout), (1, b""))
                self.assertIn(b"UTF-8" if error == "ModelUtf8" else b"0..255", actual.stderr)

    def test_effectful_arguments(self):
        fixture = (ROOT / "test/fixtures/text-contains-order.lan").read_text()
        program = self.work / "order.lan"
        for unused in [False, True]:
            with self.subTest(unused=unused):
                program.write_text(fixture if not unused else fixture[:fixture.index("  case same with")]
                                   + "  Response.text Bytes (Text.concat Bytes recreated.1 recorded.1)\n")
                actual = run(DRIVER, "run", "--request", "/", program)
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (0, response("onceright"), b""))
                require(run(DRIVER, "emit", "--target", program))
                if unused:
                    omitted = program.read_text().replace(
                        "  let same : Bool := Text.contains Bytes (left db) (right db) in\n", "")
                    program.write_text(omitted)
                    control = run(DRIVER, "run", "--request", "/", program)
                    self.assertEqual((control.returncode, control.stdout), (1, b""))
                    self.assertIn(b"model row not found", control.stderr)

    def test_refusal_before_output(self):
        program, destination = self.work / "bad.lan", self.work / "crate"
        for expression in ["Text.contains Nat 1 1", 'Text.contains Bytes b"x" 1']:
            with self.subTest(expression=expression):
                program.write_text(BASE + f"def main : Bool := {expression}\n")
                actual = run(DRIVER, "emit", "--crate", destination, program)
                self.assertEqual((actual.returncode, actual.stdout), (1, b""))
                self.assertFalse(destination.exists())

    def test_native(self):
        actual = compile_native(self.work, emit(self.work), "clean")
        self.assertEqual((actual.returncode, actual.stderr), (0, b""))
        self.assertEqual(actual.stdout.decode().splitlines(), expected_native())
        print(f"LAN-TEXT-CONTAINS NATIVE OK observations={len(expected_native())}")


def mutations():
    with tempfile.TemporaryDirectory(prefix="lanyard-text-contains-mut-") as directory:
        work = Path(directory)
        emitted = emit(work)
        for name, before, after in [("clean", "", ""), *MUTANTS, ("restored", "", "")]:
            if before and emitted.count(before) != 1:
                sys.exit(f"LAN-TEXT-CONTAINS-MUT FAIL anchor {name}: {emitted.count(before)}")
            actual = compile_native(work, emitted.replace(before, after) if before else emitted, name)
            if actual.returncode != 0 or actual.stderr:
                sys.exit(f"LAN-TEXT-CONTAINS-MUT FAIL runtime {name}: {actual.stderr!r}")
            rows = actual.stdout.decode().splitlines()
            expected = expected_native()
            observed_names = [row.rsplit(" ", 1)[0] for row in rows]
            if observed_names != [row.rsplit(" ", 1)[0] for row in expected]:
                sys.exit(f"LAN-TEXT-CONTAINS-MUT FAIL incomplete observations {name}")
            if before:
                failed = sum(row.endswith(" false") for row in rows)
                if not failed:
                    sys.exit(f"LAN-TEXT-CONTAINS-MUT SURVIVED {name}")
                print(f"LAN-TEXT-CONTAINS-MUT KILLED {name} observations={failed}")
            elif rows != expected:
                sys.exit(f"LAN-TEXT-CONTAINS-MUT FAIL {name}")
            else:
                print(f"LAN-TEXT-CONTAINS-MUT OK {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutations", action="store_true")
    args, remaining = parser.parse_known_args()
    if args.mutations:
        if remaining:
            parser.error("unexpected mutation arguments")
        mutations()
    else:
        unittest.main(argv=[sys.argv[0], *remaining])
