"""Compare directional Unicode trimming across the interpreter and native Rust."""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = """mu Bytes : Type 0 :=
| bytesNil : Bytes
| bytesCons (head : Nat) (tail : Bytes) : Bytes
def start : Bytes -> Bytes := Text.trim_start Bytes
def finish : Bytes -> Bytes := Text.trim_end Bytes
def TextType : Type 0 := Bytes
def first : Bytes := b" x "
def badfirst : Bytes := bytesCons 255 bytesNil
"""
# This explicit property set excludes Python's additional control separators.
WHITESPACE = [*range(0x09, 0x0e), 0x20, 0x85, 0xa0, 0x1680,
              *range(0x2000, 0x200b), 0x2028, 0x2029, 0x202f, 0x205f, 0x3000]
DEADLINE = time.monotonic() + 600


def fail(message):
    print(f"LAN-TEXT-TRIM FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def quote(text, rust=False):
    return '"' + ''.join('\\"' if char == '"' else '\\\\' if char == '\\' else
                         (f"\\u{{{ord(char):x}}}" if rust else f"\\x{ord(char):02x}")
                         if ord(char) < 32 or ord(char) == 127 else char for char in text) + '"'


def alias(side):
    return "start" if side == "start" else "finish"


def cases():
    values = [("edge", " x ", "x ", " x"), ("empty", "", "", ""),
              ("interior", " a b ", "a b ", " a b")]
    for index, scalar in enumerate(WHITESPACE):
        space = chr(scalar)
        values += [(f"ws_{index}", space + "é" + space, "é" + space, space + "é"),
                   (f"only_{index}", space * 3, "", ""),
                   (f"inside_{index}", "a" + space + "b", "a" + space + "b", "a" + space + "b")]
    for index, text in enumerate(["a\0b", "\0", "e\u0301", "日本", "🦀", "\x1c", "\x1d",
                                  "\x1e", "\x1f", "\u180e", "\u200b", "\ufeff"]):
        values.append((f"keep_{index}", " " + text + " ", text + " ", " " + text))
    result = [(side + "_" + name, f"{alias(side)} b{quote(text)}", expected)
              for name, text, leading, trailing in values
              for side, expected in [("start", leading), ("end", trailing)]]
    for side, expected in [("start", "x "), ("end", " x")]:
        result += [
            (side + "_type", f'Text.trim_{side} TextType b" x "', expected),
            (side + "_capture", f'let text : Bytes := b" x " in let f : Nat -> Bytes := '
             f'fun (n : Nat) => {alias(side)} text in f 0', expected),
            (side + "_shared", f'let text : Bytes := b" x " in Text.concat Bytes ({alias(side)} text) text', expected + " x "),
            (side + "_ordered", f'{alias(side)} first', expected),
            (side + "_unused", f'let ignored : Bytes := {alias(side)} first in b"ok"', "ok"),
        ]
    return result + [("compose", 'finish (start b" x ")', "x")]


CASES = cases()
BAD = [("range", 'bytesCons 256 bytesNil', "ModelByteRange", "0..255"),
       ("utf8", 'bytesCons 255 bytesNil', "ModelUtf8", "UTF-8"),
       ("tail", 'bytesCons 32 (bytesCons 120 (bytesCons 255 bytesNil))', "ModelUtf8", "UTF-8"),
       ("head", 'bytesCons 255 (bytesCons 120 (bytesCons 32 bytesNil))', "ModelUtf8", "UTF-8"),
       ("overlong", 'bytesCons 192 (bytesCons 175 bytesNil)', "ModelUtf8", "UTF-8"),
       ("truncated", 'bytesCons 195 bytesNil', "ModelUtf8", "UTF-8")]
ERRORS = [(side + "_" + name, f"{alias(side)} ({expression})", error, message)
          for side in ["start", "end"] for name, expression, error, message in BAD]
ERRORS += [(side + "_unused_error", f'let ignored : Bytes := {alias(side)} badfirst in b"ok"',
            "ModelUtf8", "UTF-8") for side in ["start", "end"]]


def run(*args, budget=60):
    remaining = DEADLINE - time.monotonic()
    if remaining <= 0:
        fail("text trim suite deadline exceeded")
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, capture_output=True,
                          timeout=min(budget, remaining), check=False)


def require(result):
    if result.returncode:
        fail(f"command failed ({result.returncode}): {result.stderr.decode(errors='replace')}")
    return result.stdout


def response(body):
    encoded = body.encode()
    return (f"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(encoded)}\r\n\r\n").encode() + encoded


def source():
    return BASE + ''.join(f"def {name} : Bytes := {expr}\n" for name, expr, *_ in CASES + ERRORS)


def emit(work):
    program = work / "native.lan"
    program.write_text(source())
    emitted = require(run(DRIVER, "emit", "--target", program)).decode()
    for name in ["first", "badfirst"]:
        emitted, count = re.subn(rf"(fn f_{name.encode().hex()}\(\)[^\n]*\{{)",
                                  lambda match: match[0] + f' print!("{name.upper()} ");', emitted)
        if count != 1:
            fail(f"instrumentation target {name}: {count}")
    return emitted


def native_harness():
    checks = ''.join(f'println!("CASE {name} {{}}", f_{name.encode().hex()}()'
                     '.and_then(|text| lan_model_text_to_4279746573(&text))'
                     f'.map(|text| text == {quote(expected, rust=True)}).unwrap_or(false));\n'
                     for name, _expr, expected in CASES)
    checks += ''.join(f'println!("ERROR {name} {{}}", matches!(f_{name.encode().hex()}(), '
                      f'Err(Error::{error})));\n' for name, _expr, error, _message in ERRORS)
    return "fn main() {\n" + checks + "}\n"


def expected_native():
    return [("FIRST " if name.endswith(("_ordered", "_unused")) else "") + f"CASE {name} true"
            for name, *_ in CASES] + [
            ("BADFIRST " if name.endswith("_unused_error") else "") + f"ERROR {name} true"
            for name, *_ in ERRORS]


def native(work, emitted, name):
    program, binary = work / f"{name}.rs", work / name
    program.write_text(emitted + native_harness())
    require(run("git", "init", "--quiet", work))
    require(run("gateledger", "run", "--ledger", ROOT / ".gatework/gateledger", "--dir", work,
                "--scope", program.name, "--toolchain", "1.98", "--", "rustup", "run", "1.98",
                "rustc", "--edition", "2024", program, "-o", binary, budget=180))
    return require(run(binary)).decode().splitlines()


def interpreter(work):
    program = work / "run.lan"
    handler = "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => Response.text Bytes "
    for name, expression, expected in CASES:
        program.write_text(BASE + handler + "(" + expression + ")\n")
        if require(run(DRIVER, "run", "--request", "/", program)) != response(expected):
            fail(f"interpreter mismatch: {name}")
    for name, expression, _error, message in ERRORS:
        program.write_text(BASE + handler + "(" + expression + ")\n")
        result = run(DRIVER, "run", "--request", "/", program)
        if result.returncode == 0 or result.stdout or message.encode() not in result.stderr:
            fail(f"missing interpreter refusal: {name}")
    for family in ["TextList", "Other"]:
        program.write_text((BASE + handler + '(Text.concat Bytes (start b" x ") (finish b" y "))').replace("Bytes", family))
        if require(run(DRIVER, "run", "--request", "/", program)) != response("x  y"):
            fail(f"alternate family: {family}")
        emitted = require(run(DRIVER, "emit", "--target", program))
        if b".trim_start()" not in emitted or b".trim_end()" not in emitted:
            fail(f"alternate family emission: {family}")
    fixture = ROOT / "test/fixtures/text-trim.lan"
    if require(run(DRIVER, "run", "--request", "/", "--form",
                   urlencode({"start": "\u3000left ", "end": " right\u0085"}), fixture)) != response("left  right"):
        fail("form fixture response")
    for side in ["start", "end"]:
        for body, message in [
            (f"def main : Nat := Text.trim_{side} Nat 1", "byte list"),
            (f"def main : (0 A : Type 0) -> A -> A := fun (0 A : Type 0) (t : A) => Text.trim_{side} A t", "closed"),
        ]:
            program.write_text(BASE + body)
            result = run(DRIVER, "emit", "--target", program)
            if result.returncode == 0 or message.encode() not in result.stderr:
                fail(f"missing compiler refusal: {body}")
    print(f"LAN-TEXT-TRIM CLI OK cases={len(CASES)} errors={len(ERRORS)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutations", action="store_true")
    args = parser.parse_args()
    (ROOT / ".gatework").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="text-trim-", dir=ROOT / ".gatework") as directory:
        work = Path(directory)
        if not args.mutations:
            interpreter(work)
        emitted, expected = emit(work), expected_native()
        if native(work, emitted, "clean") != expected:
            fail("native baseline mismatch")
        print(f"LAN-TEXT-TRIM NATIVE OK observations={len(expected)}")
        if args.mutations:
            for side in ["start", "end"]:
                anchor = f".trim_{side}().to_owned()"
                for label, replacement in [("both", ".trim().to_owned()"), ("identity", ".to_owned()")]:
                    if anchor not in emitted:
                        fail(f"missing mutation anchor: {anchor}")
                    actual = native(work, emitted.replace(anchor, replacement), f"{side}-{label}")
                    sentinel = f"CASE {side}_edge false"
                    if len(actual) != len(expected) or sentinel not in actual:
                        fail(f"mutation survived or incomplete: {side}-{label}")
                    print(f"LAN-TEXT-TRIM MUTATION KILLED {side}-{label}")
            if native(work, emitted, "restored") != expected:
                fail("restored baseline mismatch")
            print("LAN-TEXT-TRIM MUTATIONS OK killed=4 restored=ok")


if __name__ == "__main__":
    main()
