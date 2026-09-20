"""Check UTF-8 byte lengths through the CLI and compiled Rust adapters."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = """mu Bytes : Type 0 :=
| bytesNil : Bytes
| bytesCons (head : Nat) (tail : Bytes) : Bytes
def measure : Bytes -> Nat := Text.length Bytes
def format : Nat -> Bytes := Text.from_nat Bytes
"""
VALUES = ["", "a", " \t\n", "\0", "é", "é", "😀", "日本", "a\0é😀"]
VALUES += ["x" * size for size in (127, 128, 255, 256, 257, 8191, 8192, 8193)]
VALUES += ["é😀" * size for size in (1, 42, 43, 128, 1365)]
COMPUTED = [
    ("concat", 'measure (Text.concat Bytes b"é" b"😀")', "6"),
    ("capture", 'let text : Bytes := b"😀" in let f : prod () -> Nat := '
     'fun (u : prod ()) => measure text in f ()', "4"),
    ("addition", 'natAdd (measure b"é") 255', "257"),
    ("formatted", "measure (format 18446744073709551616)", "20"),
    ("type_alias", 'Text.length TextType b"é"', "2"),
    ("other_family", "Text.length Octets (cons 195 (cons 169 nil))", "2"),
]
ERRORS = [
    ("bad_byte", "measure (bytesCons 256 bytesNil)", "ModelByteRange", "255"),
    ("big_byte", "measure (bytesCons 18446744073709551616 bytesNil)", "ModelByteRange", "255"),
    ("bad_utf8", "measure (bytesCons 192 (bytesCons 175 bytesNil))", "ModelUtf8", "UTF-8"),
    ("late_utf8", "measure (bytesCons 97 (bytesCons 128 bytesNil))", "ModelUtf8", "UTF-8"),
    ("unused_utf8", "let unused : Nat := measure (bytesCons 128 bytesNil) in 7", "ModelUtf8", "UTF-8"),
    ("unused_byte", "let unused : Nat := measure (bytesCons 256 bytesNil) in 7", "ModelByteRange", "255"),
]
DECLARATIONS = BASE + """def TextType : Type 0 := Bytes
mu Octets : Type 0 := | nil : Octets | cons (head : Nat) (tail : Octets) : Octets
"""
MUTANTS = [
    ("characters", "__lan_text.len()", "__lan_text.chars().count()"),
    ("narrow", "__lan_text.len()", "(__lan_text.len() as u8)"),
]


def run(*args, cwd=ROOT):
    return subprocess.run([str(arg) for arg in args], cwd=cwd,
                          capture_output=True, timeout=180)


def require(condition, message):
    if not condition:
        sys.exit("LAN-TEXT-LENGTH FAIL " + message)


def response(body):
    return (f"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body.encode())}\r\n\r\n{body}").encode()


def cli():
    fixture = ROOT / "test/fixtures/text-length.lan"
    for value in VALUES:
        form = urlencode({"text": value})
        if len(form.encode()) <= 8192:
            actual = run(DRIVER, "run", "--request", "/length", "--form", form, fixture)
            require(actual.returncode == 0 and not actual.stderr
                    and actual.stdout == response(str(len(value.encode()))),
                    f"form response for {value[:20]!r}: {actual.stderr!r}")
    with tempfile.TemporaryDirectory(prefix="lanyard-length-cli-") as directory:
        source = Path(directory) / "case.lan"
        for name, expression, expected in COMPUTED:
            source.write_text(DECLARATIONS + "def main : Cx -> Uri -> Response := "
                              "fun (cx : Cx) (uri : Uri) => "
                              f"Response.text Bytes (format ({expression}))\n")
            actual = run(DRIVER, "run", "--request", "/length", source)
            require(actual.returncode == 0 and not actual.stderr
                    and actual.stdout == response(expected), f"computed {name}: {actual!r}")
        for name, expression, _native_error, diagnostic in ERRORS:
            source.write_text(DECLARATIONS + f"def main : Nat := {expression}\n")
            actual = run(DRIVER, "run", source)
            require(actual.returncode != 0 and not actual.stdout
                    and diagnostic in actual.stderr.decode(), f"error {name}: {actual!r}")
        for declaration, diagnostic in [
            ("def main : Nat := Text.length Nat 1", "byte list"),
            ("def main : (0 A : Type 0) -> A -> Nat := "
             "fun (0 A : Type 0) (value : A) => Text.length A value", "closed"),
        ]:
            source.write_text(declaration + "\n")
            for command in [("run",), ("emit", "--target")]:
                actual = run(DRIVER, *command, source)
                require(actual.returncode != 0 and not actual.stdout
                        and diagnostic in actual.stderr.decode(), f"refusal {command}: {actual!r}")
    print("LAN-TEXT-LENGTH CLI OK groups=4")


def rust_string(text):
    # JSON escapes outside Rust's common escape set need Rust scalar syntax.
    return '"' + "".join('\\"' if character == '"' else '\\\\' if character == '\\'
                         else f"\\u{{{ord(character):x}}}" if ord(character) < 32
                         else character for character in text) + '"'


def harness():
    pairs = ",\n".join(f"({rust_string(value)}, {json.dumps(str(len(value.encode())))})"
                        for value in VALUES)
    checks = "".join(f'    println!("COMPUTED {name} {{}}", f_{name.encode().hex()}()'
                     f'.map(|value| lan_text_from_nat(&value) == "{expected}").unwrap_or(false));\n'
                     for name, _expression, expected in COMPUTED)
    checks += "".join(f'    println!("ERROR {name} {{}}", matches!(f_{name.encode().hex()}(), '
                      f'Err(Error::{error})));\n'
                      for name, _expression, error, _diagnostic in ERRORS)
    return """
fn main() {
    let cases = [
""" + pairs + """
    ];
    cases.iter().enumerate().for_each(|(index, (input, expected))| {
        let matches = f_6d656173757265(Arc::new(lan_model_text_from_4279746573(input.to_string())))
            .map(|value| lan_text_from_nat(&value) == *expected).unwrap_or(false);
        println!("LENGTH{index} {matches}");
    });
""" + checks + "}\n"


def native():
    expected = ([f"LENGTH{index} true" for index in range(len(VALUES))]
                + [f"COMPUTED {name} true" for name, _expression, _value in COMPUTED]
                + [f"ERROR {name} true" for name, _expression, _error, _diagnostic in ERRORS])
    with tempfile.TemporaryDirectory(prefix="lanyard-length-native-") as directory:
        work = Path(directory)
        source = work / "native.lan"
        source.write_text(DECLARATIONS + "".join(f"def {name} : Nat := {expression}\n"
                          for name, expression, *_rest in COMPUTED + ERRORS))
        actual = run(DRIVER, "emit", "--target", source)
        require(actual.returncode == 0 and not actual.stderr, f"native emission: {actual.stderr!r}")
        emitted = actual.stdout.decode()
        initialized = run("git", "init", "--quiet", work)
        require(initialized.returncode == 0, f"native Git scope: {initialized.stderr!r}")

        def check(name, implementation):
            rust, binary = work / f"{name}.rs", work / name
            rust.write_text(implementation + harness())
            result = run("gateledger", "run", "--ledger", ROOT / ".gatework/gateledger",
                         "--dir", work, "--scope", rust.name, "--toolchain", "1.98", "--",
                         "rustup", "run", "1.98", "rustc", "--edition", "2024", rust, "-o", binary)
            require(result.returncode == 0, f"compile {name}: {result.stdout!r} {result.stderr!r}")
            result = run(binary)
            require(result.returncode == 0 and not result.stderr, f"run {name}: {result.stderr!r}")
            return result.stdout.decode().splitlines()

        require(check("baseline", emitted) == expected, "native observations differ")
        for name, needle, replacement in MUTANTS:
            require(needle in emitted, f"mutation target missing: {name}")
            observed = check(name, emitted.replace(needle, replacement))
            require(len(observed) == len(expected) and any(line.endswith(" false") for line in observed),
                    f"mutation survived: {name}")
    print(f"LAN-TEXT-LENGTH NATIVE OK observations={len(expected)} mutants={len(MUTANTS)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true")
    args = parser.parse_args()
    if args.native:
        native()
    else:
        cli()
