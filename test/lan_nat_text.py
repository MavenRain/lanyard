"""Check decimal text through HTTP, emitted Rust, and arithmetic mutations."""
from pathlib import Path
import argparse
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = """mu Bytes : Type 0 :=
| bytesNil : Bytes
| bytesCons (head : Nat) (tail : Bytes) : Bytes
def format : Nat -> Bytes := Text.from_nat Bytes
"""
HANDLER = "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => "
VALUES = sorted(set([*range(513), 10**100 - 1, 10**100, 10**100 + 1]
                    + [2**bits + offset for bits in range(8, 1025, 8)
                       for offset in (-1, 0, 1)]))
GENERATOR = random.Random(1024)
VALUES += [GENERATOR.getrandbits(bits) for bits in range(17, 2049, 31)]
DECIMALS = [(str(value), str(value)) for value in VALUES]
DECIMALS += [("0000", "0"), ("000257", "257")]
COMPUTED = [
    ("addition", "format (natAdd 18446744073709551615 1)", str(2**64)),
    ("product", "format (natMul 1099511627776 1099511627776)", str(2**80)),
    ("saturated", "format (natSub 1 2)", "0"),
    ("captured", "let n : Nat := 65536 in let f : prod () -> Bytes := "
     "fun (u : prod ()) => format n in f (tuple ())", "65536"),
    ("link", 'Text.concat Bytes b"/todos/" (format 256)', "/todos/256"),
]
PAGE = ("<ul><li><a href='/todos/3'>&lt;write&gt; &amp; test</a></li>"
        "<li><a href='/todos/20'>café</a></li></ul>")
MUTANTS = [
    ("radix", "digit * 256 + carry", "digit * 255 + carry"),
    ("limb-order", "value.0.iter().rev().fold", "value.0.iter().fold"),
    ("zero", "LanDecimalDigits(vec![0])", "LanDecimalDigits(vec![])"),
    ("carry", "(digits, next / 10)", "(digits, 0_u16)"),
]


def run(*args, cwd=ROOT):
    return subprocess.run([str(arg) for arg in args], cwd=cwd,
                          capture_output=True, timeout=180)


def response(body, content_type="text/plain"):
    encoded = body.encode()
    return (f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}; charset=utf-8\r\n"
            f"Content-Length: {len(encoded)}\r\n\r\n").encode() + encoded


def pure_source():
    return BASE + "".join(f"def {name} : Bytes := {expression}\n"
                          for name, expression, _ in COMPUTED)


def native_harness():
    pairs = ",\n".join(f'("{value}", "{expected}")' for value, expected in DECIMALS)
    checks = "".join(f'    println!("COMPUTED {name} {{}}", f_{name.encode().hex()}()'
                     '.and_then(|bytes| lan_model_text_to_4279746573(&bytes))'
                     f'.map(|text| text == "{expected}").unwrap_or(false));\n'
                     for name, _expression, expected in COMPUTED)
    return """
fn main() {
    let cases = [
""" + pairs + """
    ];
    cases.iter().enumerate().for_each(|(index, (input, expected))| {
        let matches = Nat::decimal(input).and_then(|value| f_666f726d6174(Arc::new(value)))
            .and_then(|bytes| lan_model_text_to_4279746573(&bytes))
            .map(|text| text == *expected).unwrap_or(false);
        println!("DECIMAL{index} {matches}");
    });
""" + checks + "}\n"


def compile_native(work, emitted, name):
    source, binary = work / f"{name}.rs", work / name
    source.write_text(emitted + native_harness())
    result = run("gateledger", "run", "--ledger", ROOT / ".gatework/gateledger",
                 "--dir", work, "--scope", source.name, "--toolchain", "1.98", "--",
                 "rustup", "run", "1.98", "rustc", "--edition", "2024", source, "-o", binary)
    if result.returncode != 0:
        sys.exit(result.stdout.decode() + result.stderr.decode())
    return run(binary)


def expected_native():
    return [f"DECIMAL{index} true" for index in range(len(DECIMALS))] + [
        f"COMPUTED {name} true" for name, _expression, _expected in COMPUTED]


class NaturalText(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="lanyard-nat-text-")
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)

    def source(self, body, base=BASE):
        source = self.work / "program.lan"
        source.write_text(base + body)
        return source

    def test_decimal_responses(self):
        for value in [0, 9, 10, 255, 256, 65536, 2**64, 2**128, 10**100]:
            with self.subTest(value=value):
                source = self.source(HANDLER + f"Response.text Bytes (format {value})\n")
                actual = run(DRIVER, "run", "--request", "/", source)
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (0, response(str(value)), b""))

    def test_computed_responses(self):
        for _name, expression, expected in COMPUTED:
            with self.subTest(expression=expression):
                source = self.source(HANDLER + f"Response.text Bytes ({expression})\n")
                actual = run(DRIVER, "run", "--request", "/", source)
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (0, response(expected), b""))

    def test_fixtures(self):
        for name, body, content_type in [("nat-text", str(2**64), "text/plain"),
                                         ("todo-list", PAGE, "text/html")]:
            with self.subTest(name=name):
                actual = run(DRIVER, "run", "--request", "/", ROOT / f"test/fixtures/{name}.lan")
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (0, response(body, content_type), b""))

    def test_empty_and_single_list(self):
        prefix = (ROOT / "test/fixtures/todo-list.lan").read_text().split("def main :")[0]
        for seed, expected in [("", "<ul></ul>"),
                               ('let row : Todo := Todo.create (tuple (0, b"")) db in ',
                                "<ul><li><a href='/todos/0'></a></li></ul>")]:
            with self.subTest(expected=expected):
                source = self.source(HANDLER +
                                     'let db : Db := Db.connect Todo Bytes b"sqlite::memory:" in '
                                     "let ready : prod () := Db.push_schema db in " + seed + "page db\n",
                                     base=prefix)
                actual = run(DRIVER, "run", "--request", "/", source)
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (0, response(expected, "text/html"), b""))

    def test_alias_and_alternate_family(self):
        source = self.source("""def Output : Type 0 := Bytes
def decimal : Nat -> Output := Text.from_nat Output
def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => Response.text Output (decimal 000257)
""", base=BASE.replace("Bytes", "Buffer") + "def Bytes : Type 0 := Buffer\n")
        actual = run(DRIVER, "run", "--request", "/", source)
        self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                         (0, response("257"), b""))

    def test_reject_invalid_input_and_layout_before_emission(self):
        for expression in ['Text.from_nat Bytes b"1"', "Text.from_nat Bytes (tuple ())",
                           "Text.from_nat Nat 1"]:
            with self.subTest(expression=expression):
                source = self.source(f"def main : Bytes := {expression}\n")
                output = self.work / "refused"
                actual = run(DRIVER, "emit", "--crate", output, source)
                self.assertNotEqual(actual.returncode, 0)
                self.assertEqual(actual.stdout, b"")
                self.assertFalse(output.exists())

    def test_native_decimal_parity(self):
        source = self.source("", base=pure_source())
        emitted = run(DRIVER, "emit", "--target", source)
        self.assertEqual((emitted.returncode, emitted.stderr), (0, b""))
        initialized = run("git", "init", "--quiet", self.work)
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        actual = compile_native(self.work, emitted.stdout.decode(), "decimal")
        self.assertEqual((actual.returncode, actual.stderr), (0, b""))
        self.assertEqual(actual.stdout.decode().splitlines(), expected_native())
        print(f"LAN-NAT-TEXT-NATIVE OK observations={len(expected_native())}")


def mutations():
    with tempfile.TemporaryDirectory(prefix="lanyard-nat-text-mutations-") as directory:
        work = Path(directory)
        source = work / "program.lan"
        source.write_text(pure_source())
        emitted = run(DRIVER, "emit", "--target", source)
        if emitted.returncode != 0 or emitted.stderr:
            sys.exit(emitted.stderr.decode())
        initialized = run("git", "init", "--quiet", work)
        if initialized.returncode != 0:
            sys.exit(initialized.stderr.decode())
        original = emitted.stdout.decode()
        for label, old, new in [("clean", "", ""), *MUTANTS, ("restored", "", "")]:
            if old and original.count(old) != 1:
                sys.exit(f"{label}: mutation anchor must occur exactly once")
            changed = original.replace(old, new, 1) if old else original
            actual = compile_native(work, changed, label.replace("-", "_"))
            if actual.returncode != 0 or actual.stderr:
                sys.exit(f"{label}: native execution failed")
            passed = actual.stdout.decode().splitlines() == expected_native()
            if passed != (not old):
                sys.exit(f"{label}: {'survived' if old else 'control failed'}")
            print(f"LAN-NAT-TEXT-MUTATION {'killed' if old else 'control'} {label}")
    print(f"LAN-NAT-TEXT-MUTATIONS OK killed={len(MUTANTS)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mutations", action="store_true")
    args, remaining = parser.parse_known_args()
    if args.mutations:
        mutations()
    else:
        unittest.main(argv=[__file__, *remaining])
