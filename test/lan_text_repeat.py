"""Check repetition, mixed argument types and evaluation in both runtimes."""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = """mu Bytes : Type 0 :=
| bytesNil : Bytes
| bytesCons (head : Nat) (tail : Bytes) : Bytes
def repeat : Bytes -> Nat -> Bytes := Text.repeat Bytes
"""
HUGE = "340282366920938463463374607431768211456"
TEXTS = ["", "a", "abc", " \r\n", "a\0b", "é", "e\u0301", "日本", "🦀"]
CASES = [(text, str(count), text * count) for text in TEXTS for count in [0, 1, 2, 3, 7, 32, 256]]
CASES += [("", HUGE, "")]
COMPUTED = [
    ("capture", 'let n : Nat := 3 in let f : Bytes -> Bytes := '
     'fun (t : Bytes) => repeat t n in f b"x"', "xxx"),
    ("compose", 'repeat (Text.trim Bytes b" x ") (Text.length Bytes b"1234")', "xxxx"),
    ("shared", 'let t : Bytes := b"abc" in repeat t (Text.length Bytes t)', "abcabcabc"),
    ("unused", 'let ignored : Bytes := repeat b"x" 3 in b"ok"', "ok"),
]
ERRORS = [
    ("byte", 'repeat (bytesCons 256 bytesNil) 0', "ModelByteRange", "0..255"),
    ("utf8", 'repeat (bytesCons 255 bytesNil) 0', "ModelUtf8", "UTF-8"),
    ("unused_utf8", 'let ignored : Bytes := repeat (bytesCons 255 bytesNil) 0 in b"ok"', "ModelUtf8", "UTF-8"),
    ("huge", f'repeat b"x" {HUGE}', "Arithmetic", "overflow"),
    ("product", 'repeat b"xx" 9223372036854775807', "Arithmetic", "overflow"),
    ("unused_huge", f'let ignored : Bytes := repeat b"x" {HUGE} in b"ok"', "Arithmetic", "overflow"),
]
ORDERED = """
def first : Bytes := b"ab"
def second : Nat := 3
def badfirst : Bytes := bytesCons 255 bytesNil
def ordered : Bytes := repeat first second
def unused_ordered : Bytes := let ignored : Bytes := repeat first second in b"ok"
def ordered_bad : Bytes := repeat badfirst second
mu Other : Type 0 := | otherNil : Other | otherCons (head : Nat) (tail : Other) : Other
def alternate : Other := Text.repeat Other (otherCons 120 otherNil) 3
"""


def run(*args, budget=60):
    return subprocess.run(list(map(str, args)), cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=budget)


def fail(message):
    sys.exit(f"LAN-TEXT-REPEAT FAIL {message}")


def require(result):
    if result.returncode:
        fail(f"command failed: {result.args!r}: {result.stdout!r} {result.stderr!r}")
    return result.stdout


def quote(text, rust=False):
    return '"' + ''.join('\\"' if char == '"' else '\\\\' if char == '\\' else
                         (f"\\u{{{ord(char):x}}}" if rust else f"\\x{ord(char):02x}")
                         if ord(char) < 32 or ord(char) == 127 else char for char in text) + '"'


def response(body):
    encoded = body.encode()
    return (f"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(encoded)}\r\n\r\n").encode() + encoded


def source():
    return BASE + ''.join(f"def {name} : Bytes := {expr}\n" for name, expr, *_ in COMPUTED + ERRORS) + ORDERED


def native_harness():
    cases = ',\n'.join('(' + ', '.join(quote(part, rust=True) for part in case) + ')' for case in CASES)
    checks = ''.join(f'println!("COMPUTED {name} {{}}", observe(f_{name.encode().hex()}()'
                     '.and_then(|text| lan_model_text_to_4279746573(&text)), '
                     f'{quote(expected, rust=True)}));\n' for name, _expr, expected in COMPUTED)
    checks += ''.join(f'println!("ERROR {name} {{}}", matches!(f_{name.encode().hex()}(), '
                      f'Err(Error::{error})));\n' for name, _expr, error, _message in ERRORS)
    for name, expected in [("ordered", "ababab"), ("unused_ordered", "ok")]:
        checks += f'let actual = f_{name.encode().hex()}();\n'
        checks += f'println!("ORDER {name} {{}}", observe(actual.and_then(|text| lan_model_text_to_4279746573(&text)), "{expected}"));\n'
    checks += 'let actual = f_6f7264657265645f626164();\nprintln!("ORDER bad {}", matches!(actual, Err(Error::ModelUtf8)));\n'
    checks += 'println!("ALTERNATE {}", observe(f_616c7465726e617465().and_then(|text| lan_model_text_to_4f74686572(&text)), "xxx"));\n'
    return """
fn observe(value: Result<String, Error>, expected: &str) -> bool {
    value.map(|text| text == expected).unwrap_or(false)
}
fn main() {
    let cases = [
""" + cases + """
    ];
    cases.iter().enumerate().for_each(|(index, (text, count, expected))| {
        let actual = Nat::decimal(count).and_then(|count| f_726570656174(
            Arc::new(lan_model_text_from_4279746573(text.to_string())), Arc::new(count)));
        println!("CASE{index} {}", observe(actual.and_then(|text| lan_model_text_to_4279746573(&text)), expected));
    });
""" + checks + "}\n"


def expected_native():
    return ([f"CASE{index} true" for index in range(len(CASES))]
            + [f"COMPUTED {name} true" for name, _expr, _expected in COMPUTED]
            + [f"ERROR {name} true" for name, *_ in ERRORS]
            + ["FIRST SECOND ORDER ordered true", "FIRST SECOND ORDER unused_ordered true",
               "BADFIRST SECOND ORDER bad true", "ALTERNATE true"])


def emit(work):
    program = work / "native.lan"
    program.write_text(source())
    emitted = require(run(DRIVER, "emit", "--target", program)).decode()
    for name in ["first", "second", "badfirst"]:
        emitted, count = re.subn(rf"(fn f_{name.encode().hex()}\(\)[^\n]*\{{)",
                                  lambda match: match[0] + f' print!("{name.upper()} ");', emitted)
        if count != 1:
            fail(f"instrumentation target {name}: {count}")
    return emitted


def native(work, emitted, name):
    program, binary = work / f"{name}.rs", work / name
    program.write_text(emitted + native_harness())
    require(run("git", "init", "--quiet", work))
    require(run("gateledger", "run", "--ledger", ROOT / ".gatework/gateledger", "--dir", work,
                "--scope", program.name, "--toolchain", "1.98", "--", "rustup", "run", "1.98",
                "rustc", "--edition", "2024", program, "-o", binary, budget=180))
    return require(run(binary)).decode().splitlines()


def interpreter(work):
    ordered = require(run(DRIVER, "run", "--request", "/", ROOT / "test/fixtures/text-repeat-order.lan"))
    if ordered != response("abab:once:ab"):
        fail(f"database evaluation order: {ordered!r}")
    fixture = ROOT / "test/fixtures/text-repeat.lan"
    for text, count, expected in CASES:
        actual = require(run(DRIVER, "run", "--request", "/", "--form",
                             urlencode({"text": text, "count": count}), fixture))
        if actual != response(expected):
            fail(f"form mismatch: {(text, count)!r}: {actual!r}")
    program = work / "run.lan"
    handler = "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => Response.text Bytes "
    for family in ["Bytes", "TextList"]:
        for name, _expr, expected in COMPUTED:
            program.write_text((source() + handler + name + "\n").replace("Bytes", family))
            if require(run(DRIVER, "run", "--request", "/", program)) != response(expected):
                fail(f"computed mismatch: {family} {name}")
    for name, _expr, _error, message in ERRORS:
        program.write_text(source() + handler + name + "\n")
        result = run(DRIVER, "run", "--request", "/", program)
        if result.returncode == 0 or message.encode() not in result.stderr:
            fail(f"missing refusal {name}: {result.stdout!r} {result.stderr!r}")
    for body, message in [
        ('def main : Nat := Text.repeat Nat 1 2', "byte list"),
        ('def main : (0 A : Type 0) -> A -> Nat -> A := fun (0 A : Type 0) (t : A) (n : Nat) => Text.repeat A t n', "closed"),
        ('def main : Bytes := let f : Nat -> Bytes := Text.repeat Bytes b"x" in f 3', "arity"),
    ]:
        program.write_text(BASE + body)
        result = run(DRIVER, "emit", "--target", program)
        if result.returncode == 0 or message.encode() not in result.stderr:
            fail(f"missing compiler refusal: {result.stderr!r}")
    print("LAN-TEXT-REPEAT CLI OK")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutations", action="store_true")
    args = parser.parse_args()
    (ROOT / ".gatework").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="text-repeat-", dir=ROOT / ".gatework") as directory:
        work = Path(directory)
        if not args.mutations:
            interpreter(work)
        emitted = emit(work)
        expected = expected_native()
        actual = native(work, emitted, "clean")
        if actual != expected:
            fail(f"native mismatch: {actual!r}")
        print(f"LAN-TEXT-REPEAT NATIVE OK observations={len(expected)}")
        if args.mutations:
            mutants = [
                ("once", '(0..count).for_each(|_| output.push_str(text));', 'output.push_str(text);', "CASE7 false"),
                ("short", '(0..count).for_each', '(0..count.saturating_sub(1)).for_each', "CASE9 false"),
                ("empty", 'if text.is_empty() { return Ok(String::new()); }', 'if text.is_empty() { return Err(Error::Arithmetic); }', "CASE0 false"),
                ("narrow", 'count.0.iter().rev()', 'count.0.iter().take(1).rev()', "ERROR huge false"),
            ]
            print("LAN-TEXT-REPEAT MUT OK clean")
            for name, before, after, sentinel in mutants:
                if emitted.count(before) != 1:
                    fail(f"mutation target {name}")
                rows = native(work, emitted.replace(before, after), name)
                if len(rows) != len(expected) or sentinel not in rows:
                    fail(f"mutation survived {name}: {rows!r}")
                print(f"LAN-TEXT-REPEAT MUT OK {name}")
            if native(work, emitted, "restored") != expected:
                fail("restored native baseline failed")
            print("LAN-TEXT-REPEAT MUT OK restored")


if __name__ == "__main__":
    main()
