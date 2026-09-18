"""Check comparison argument effects with interpreted and native databases."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = (ROOT / "test/fixtures/text-equal-order.lan").read_text().split("def main :", 1)[0]
CONNECT = ('let db : Db := Db.connect Piece Bytes b"sqlite::memory:" in '
           "let ready : prod () := Db.push_schema db in ")
COMPARE = "Text.equal Bytes (left db) (right db)"
RECREATE = 'let recreated : Piece := Piece.create (tuple (1, b"once")) db in '
RETAINED = "let recorded : Piece := Piece.get_by_id 2 db in Text.concat Bytes recreated.1 recorded.1"
CASES = [
    ("different", f"let compared : Bool := {COMPARE} in {RECREATE}"
     f'case compared with | 0 (u : prod ()) => {RETAINED} | 1 (u : prod ()) => b"wrong"', "onceright", None),
    ("retained", f"let ignored : Bool := {COMPARE} in {RECREATE}{RETAINED}", "onceright", None),
    ("same", "case (Text.equal Bytes (left db) "
     "(let stored : Piece := Piece.get_by_id 1 db in stored.1)) with "
     '| 0 (u : prod ()) => b"no" | 1 (u : prod ()) => b"yes"', "yes", None),
    ("invalid", 'let ignored : Bool := Text.equal Bytes b"x" (bytesCons 255 bytesNil) in b"ok"',
     "UTF-8", "ModelUtf8"),
    ("order", "let allocated : Bytes := left db in "
     'let ignored : Bool := Text.equal Bytes (bytesCons 255 bytesNil) (left db) in b"ok"',
     "duplicate", "Database(_)"),
]


def source():
    return BASE + "".join(f"def {name} : Bytes := {CONNECT}{expression}\n"
                           for name, expression, _expected, _error in CASES)


def run(*command):
    return subprocess.run([str(arg) for arg in command], cwd=ROOT,
                          capture_output=True, timeout=180)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-TEXT-EQUAL-DATABASE FAIL: {result.stdout!r} {result.stderr!r}")
    return result.stdout.decode()


def harness():
    checks = []
    for name, _expression, expected, error in CASES:
        call = f"f_{name.encode().hex()}().await"
        check = (f"matches!({call}, Err(Error::{error}))" if error else
                 f'{call}.and_then(|text| lan_model_text_to_4279746573(&text))'
                 f'.map(|text| text == "{expected}").unwrap_or(false)')
        checks.append(f'    println!("DATABASE {name} {{}}", {check});\n')
    return '#[tokio::main(flavor = "current_thread")]\nasync fn main() {\n' + "".join(checks) + "}\n"


def interpreter():
    with tempfile.TemporaryDirectory(prefix="lanyard-text-equal-database-") as directory:
        program = Path(directory) / "program.lan"
        for name, _expression, body, error in CASES:
            program.write_text(source() + "def main : Cx -> Uri -> Response := "
                               f"fun (cx : Cx) (uri : Uri) => Response.text Bytes {name}\n")
            actual = run(DRIVER, "run", "--request", "/", program)
            expected = (f"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n"
                        f"Content-Length: {len(body.encode())}\r\n\r\n{body}").encode()
            passes = ((actual.returncode == 1 and not actual.stdout and body.encode() in actual.stderr)
                      if error else (actual.returncode == 0 and not actual.stderr and actual.stdout == expected))
            if not passes:
                sys.exit(f"LAN-TEXT-EQUAL-DATABASE FAIL {name}: {actual.stdout!r} {actual.stderr!r}")
    print(f"LAN-TEXT-EQUAL-DATABASE OK interpreter observations={len(CASES)}")


def prepare(args):
    destination = args.prepare.absolute()
    program = destination.with_suffix(".lan")
    if destination.exists() or program.exists():
        sys.exit("LAN-TEXT-EQUAL-DATABASE FAIL: output and sibling source must be fresh")
    destination.parent.mkdir(parents=True, exist_ok=True)
    program.write_text(source() + "def main : Bytes := different\n")
    require(run(sys.executable, "-P", ROOT / "dev/prepare-crate.py", "--source", program,
                "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock,
                "--output", destination))
    (destination / "src/main.rs").write_text(require(run(DRIVER, "emit", "--target", program)) + harness())
    (destination / "cases.json").write_text(json.dumps(CASES, indent=2) + "\n")
    print(f"LAN-TEXT-EQUAL-DATABASE PREPARED manifest={destination / 'Cargo.toml'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--interpreter", action="store_true")
    action.add_argument("--prepare", type=Path)
    action.add_argument("--check", type=Path)
    parser.add_argument("--toasty", type=Path)
    parser.add_argument("--topcoat", type=Path)
    parser.add_argument("--lock", type=Path)
    args = parser.parse_args()
    if args.interpreter:
        interpreter()
    elif args.prepare:
        if not all((args.toasty, args.topcoat, args.lock)):
            parser.error("--prepare requires --toasty, --topcoat and --lock")
        prepare(args)
    else:
        actual = run(args.check.absolute())
        expected = [f"DATABASE {name} true" for name, _expression, _body, _error in CASES]
        if actual.returncode != 0 or actual.stderr or actual.stdout.decode().splitlines() != expected:
            sys.exit(f"LAN-TEXT-EQUAL-DATABASE FAIL: {actual.stdout!r} {actual.stderr!r}")
        print(f"LAN-TEXT-EQUAL-DATABASE OK native observations={len(CASES)}")


if __name__ == "__main__":
    main()
