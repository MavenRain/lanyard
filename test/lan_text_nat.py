"""Check decimal parsing in forms, the interpreter, and emitted native Rust."""
from pathlib import Path
import argparse
import json
import random
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
def parse : Bytes -> Nat := Text.to_nat Bytes
def format : Nat -> Bytes := Text.from_nat Bytes
"""
HANDLER = "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => "
VALUES = sorted(set([*range(257), 10**100 - 1, 10**100, 10**100 + 1]
                    + [2**bits + offset for bits in range(8, 1025, 8)
                       for offset in (-1, 0, 1)]))
GENERATOR = random.Random(2048)
VALUES += [GENERATOR.getrandbits(bits) for bits in range(17, 2049, 31)]
DECIMALS = [(str(value), str(value)) for value in VALUES]
DECIMALS += [("0000", "0"), ("000257", "257")]
INVALID = ["", " ", " 1", "1 ", "\t1", "1\n", "+1", "-1", "1.0", "1e2",
           "0x10", "1_000", "1,000", "1a", "a1", "１２", "١", "1\0", "\0"]
COMPUTED = [
    ("addition", 'natAdd (parse b"18446744073709551616") 1', str(2**64 + 1)),
    ("concat", 'parse (Text.concat Bytes b"10" b"24")', "1024"),
    ("captured", 'let text : Bytes := b"65536" in let f : prod () -> Nat := '
     'fun (u : prod ()) => parse text in f ()', "65536"),
    ("roundtrip", "parse (format 340282366920938463463374607431768211456)", str(2**128)),
]
ERRORS = [
    ("bad_utf8", "parse (bytesCons 192 (bytesCons 175 bytesNil))", "ModelUtf8"),
    ("bad_byte", "parse (bytesCons 256 bytesNil)", "ModelByteRange"),
    ("unused_error", 'let ignored : Nat := parse b"bad" in 42', "Digit"),
]
MUTANTS = [
    ("empty", "if text.is_empty()", "if false"),
    ("radix", "n.scale(10)?", "n.scale(9)?"),
    ("plus", "Nat::decimal(text) }", "Nat::decimal(text.trim_start_matches('+')) }"),
    ("zero", "if text.is_empty()", 'if text.is_empty() || text == "0"'),
]


def run(*args, cwd=ROOT):
    return subprocess.run([str(arg) for arg in args], cwd=cwd,
                          capture_output=True, timeout=180)


def response(body, content_type="text/plain"):
    encoded = body.encode()
    return (f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}; charset=utf-8\r\n"
            f"Content-Length: {len(encoded)}\r\n\r\n").encode() + encoded


def pure_source():
    return BASE + "".join(f"def {name} : Nat := {expression}\n"
                          for name, expression, _expected in COMPUTED + ERRORS)


def rust_string(value):
    return json.dumps(value, ensure_ascii=False).replace("\\u0000", "\\0")


def native_harness():
    pairs = ",\n".join(f'({rust_string(value)}, "{expected}")' for value, expected in DECIMALS)
    invalid = ",\n".join(rust_string(value) for value in INVALID)
    checks = "".join(f'    println!("COMPUTED {name} {{}}", f_{name.encode().hex()}()'
                     f'.map(|value| lan_text_from_nat(&value) == "{expected}").unwrap_or(false));\n'
                     for name, _expression, expected in COMPUTED)
    checks += "".join(f'    println!("ERROR {name} {{}}", matches!(f_{name.encode().hex()}(), '
                      f'Err(Error::{error})));\n' for name, _expression, error in ERRORS)
    return """
fn main() {
    let cases = [
""" + pairs + """
    ];
    cases.iter().enumerate().for_each(|(index, (input, expected))| {
        let matches = f_7061727365(Arc::new(lan_model_text_from_4279746573(input.to_string())))
            .map(|value| lan_text_from_nat(&value) == *expected).unwrap_or(false);
        println!("DECIMAL{index} {matches}");
    });
    let invalid = [
""" + invalid + """
    ];
    invalid.iter().enumerate().for_each(|(index, input)| {
        let rejected = matches!(f_7061727365(Arc::new(lan_model_text_from_4279746573(input.to_string()))), Err(Error::Digit));
        println!("INVALID{index} {rejected}");
    });
""" + checks + "}\n"


def expected_native():
    return ([f"DECIMAL{index} true" for index in range(len(DECIMALS))]
            + [f"INVALID{index} true" for index in range(len(INVALID))]
            + [f"COMPUTED {name} true" for name, _expression, _expected in COMPUTED]
            + [f"ERROR {name} true" for name, _expression, _expected in ERRORS])


def compile_native(work, emitted, name):
    source, binary = work / f"{name}.rs", work / name
    source.write_text(emitted + native_harness())
    initialized = run("git", "init", "--quiet", work)
    if initialized.returncode != 0:
        sys.exit(initialized.stderr.decode())
    result = run("gateledger", "run", "--ledger", ROOT / ".gatework/gateledger",
                 "--dir", work, "--scope", source.name, "--toolchain", "1.98", "--",
                 "rustup", "run", "1.98", "rustc", "--edition", "2024", source, "-o", binary)
    if result.returncode != 0:
        sys.exit(result.stdout.decode() + result.stderr.decode())
    return run(binary)


def emit(work):
    source = work / "native.lan"
    source.write_text(pure_source())
    actual = run(DRIVER, "emit", "--target", source)
    if actual.returncode != 0 or actual.stderr:
        sys.exit(f"LAN-TEXT-NAT FAIL emission: {actual.stderr!r}")
    return actual.stdout.decode()


class TextNatural(unittest.TestCase):
    def setUp(self):
        (ROOT / ".gatework").mkdir(exist_ok=True)
        directory = tempfile.TemporaryDirectory(prefix="text-nat-", dir=ROOT / ".gatework")
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)

    def source(self, body, base=BASE):
        source = self.work / "program.lan"
        source.write_text(base + body)
        return source

    def test_form_arithmetic(self):
        for value in ["0", "0000", "000257", str(2**64), str(2**128), str(10**100)]:
            with self.subTest(value=value):
                actual = run(DRIVER, "run", "--request", "/", "--form", urlencode({"value": value}),
                             ROOT / "test/fixtures/text-nat.lan")
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (0, response(str(int(value) + 1)), b""))

    def test_invalid_forms(self):
        for value in INVALID:
            with self.subTest(value=value):
                actual = run(DRIVER, "run", "--request", "/", "--form", urlencode({"value": value}),
                             ROOT / "test/fixtures/text-nat.lan")
                self.assertEqual(actual.returncode, 1)
                self.assertEqual(actual.stdout, b"")
                self.assertIn(b"invalid decimal natural text", actual.stderr)

    def test_computed(self):
        for _name, expression, expected in COMPUTED:
            with self.subTest(expression=expression):
                actual = run(DRIVER, "run", "--request", "/",
                             self.source(HANDLER + f"Response.text Bytes (format ({expression}))\n"))
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (0, response(expected), b""))

    def test_invalid_bytes_and_unused_failure(self):
        for name, expression, _error in ERRORS:
            with self.subTest(name=name):
                actual = run(DRIVER, "run", "--request", "/",
                             self.source(HANDLER + f"Response.text Bytes (format ({expression}))\n"))
                self.assertEqual(actual.returncode, 1)
                self.assertEqual(actual.stdout, b"")
                self.assertTrue(actual.stderr)

    def test_alias_and_alternate_family(self):
        source = self.source("def Input : Type 0 := Buffer\n"
                             "def decimal : Input -> Nat := Text.to_nat Input\n" + HANDLER +
                             'Response.text Buffer (Text.from_nat Buffer (decimal b"000257"))\n',
                             base=BASE.replace("Bytes", "Buffer"))
        actual = run(DRIVER, "run", "--request", "/", source)
        self.assertEqual((actual.returncode, actual.stdout, actual.stderr), (0, response("257"), b""))

    def test_todo_form_id(self):
        for value in ["0", "000257", str(2**63 - 1)]:
            actual = run(DRIVER, "run", "--request", "/todos", "--form",
                         urlencode({"id": value, "title": "<hello> & café"}),
                         ROOT / "test/fixtures/todo-form-id.lan")
            self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                             (0, response(f"{int(value)}: &lt;hello&gt; &amp; café", "text/html"), b""))
        actual = run(DRIVER, "run", "--request", "/todos", "--form",
                     urlencode({"id": str(2**63), "title": "out of range"}),
                     ROOT / "test/fixtures/todo-form-id.lan")
        self.assertEqual((actual.returncode, actual.stdout), (1, b""))
        self.assertIn(b"i64", actual.stderr)

    def test_layout_and_argument_refusals(self):
        for expression in ["Text.to_nat Bytes 1", "Text.to_nat Bytes ()", "Text.to_nat Nat 1"]:
            with self.subTest(expression=expression):
                destination = self.work / "refused"
                actual = run(DRIVER, "emit", "--crate", destination,
                             self.source(f"def main : Nat := {expression}\n"))
                self.assertNotEqual(actual.returncode, 0)
                self.assertFalse(destination.exists())

    def test_native(self):
        actual = compile_native(self.work, emit(self.work), "native")
        self.assertEqual((actual.returncode, actual.stderr), (0, b""))
        self.assertEqual(actual.stdout.decode().splitlines(), expected_native())
        print(f"LAN-TEXT-NAT NATIVE OK observations={len(expected_native())}")

    def test_helper_only_when_used(self):
        source = self.source("def main : Nat := 1\n", base="")
        actual = run(DRIVER, "emit", "--target", source)
        self.assertEqual(actual.returncode, 0)
        self.assertNotIn(b"lan_text_to_nat", actual.stdout)


def mutations():
    (ROOT / ".gatework").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="text-nat-mut-", dir=ROOT / ".gatework") as directory:
        work = Path(directory)
        emitted = emit(work)
        for name, before, after in [("clean", "", ""), *MUTANTS, ("restored", "", "")]:
            if before and emitted.count(before) != 1:
                sys.exit(f"LAN-TEXT-NAT-MUT FAIL {name}: ambiguous mutation anchor")
            changed = emitted.replace(before, after, 1) if before else emitted
            actual = compile_native(work, changed, name)
            passes = (actual.returncode == 0 and not actual.stderr
                      and actual.stdout.decode().splitlines() == expected_native())
            if passes != (not before):
                sys.exit(f"LAN-TEXT-NAT-MUT FAIL {name}: unexpected result")
            print(f"LAN-TEXT-NAT-MUT {'KILLED' if before else 'OK'} {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mutations", action="store_true")
    args, remaining = parser.parse_known_args()
    if args.mutations:
        mutations()
    else:
        unittest.main(argv=[sys.argv[0], *remaining])
