"""Check parsed model keys and effectful text arguments in both runtimes."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = """mu Bytes : Type 0 :=
| bytesNil : Bytes
| bytesCons (head : Nat) (tail : Bytes) : Bytes
model Todo with | id : Nat | title : Bytes end
def render : Nat -> Bytes := Text.from_nat Bytes
def allocate : Db -> Bytes := fun (db : Db) =>
  let row : Todo := Todo.create (tuple (257, b"000257")) db in row.1
"""
CONNECT = ('let db : Db := Db.connect Todo Bytes b"sqlite::memory:" in '
           "let ready : prod () := Db.push_schema db in ")
KEY = 'Text.to_nat Bytes (Form.field Bytes b"id=000257" b"id")'
CASES = [
    ("create", f'let key : Nat := {KEY} in '
     'let row : Todo := Todo.create (tuple (key, b"saved")) db in '
     'let fetched : Todo := Todo.get_by_id key db in fetched.0', "257", None),
    ("update", f'let key : Nat := {KEY} in '
     'let row : Todo := Todo.create (tuple (key, b"1")) db in '
     'let updated : Todo := Todo.update (tuple (key, b"00042")) db in '
     'let fetched : Todo := Todo.get_by_id key db in Text.to_nat Bytes fetched.1', "42", None),
    ("delete", f'let key : Nat := {KEY} in '
     'let row : Todo := Todo.create (tuple (key, b"saved")) db in '
     'let removed : prod () := Todo.delete_by_id key db in '
     'match Todo.all db as self in Todo.rows return Nat with '
     '| Todo.nil => 0 | Todo.cons head tail => 1', "0", None),
    ("once", "Text.to_nat Bytes (allocate db)", "257", None),
    ("retained", "let ignored : Nat := Text.to_nat Bytes (allocate db) in "
     "let fetched : Todo := Todo.get_by_id 257 db in fetched.0", "257", None),
    ("range", 'let key : Nat := Text.to_nat Bytes b"9223372036854775808" in '
     'let row : Todo := Todo.create (tuple (key, b"large")) db in row.0', "i64", "ModelRange"),
    ("invalid", 'let ignored : Nat := Text.to_nat Bytes b"bad" in '
     'let row : Todo := Todo.create (tuple (1, b"saved")) db in row.0', "decimal natural", "Digit"),
]


def source():
    return BASE + "".join(f"def {name} : Nat := {CONNECT}{expression}\n"
                           for name, expression, _expected, _error in CASES)


def run(*command):
    return subprocess.run([str(arg) for arg in command], cwd=ROOT,
                          capture_output=True, timeout=180)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-TEXT-NAT-DATABASE FAIL: {result.stdout.decode()}{result.stderr.decode()}")
    return result.stdout.decode()


def harness():
    checks = []
    for name, _expression, expected, error in CASES:
        call = f"f_{name.encode().hex()}().await"
        check = (f"matches!({call}, Err(Error::{error}))" if error else
                 f'{call}.map(|value| lan_text_from_nat(&value) == "{expected}").unwrap_or(false)')
        checks.append(f'    println!("DATABASE {name} {{}}", {check});\n')
    return '#[tokio::main(flavor = "current_thread")]\nasync fn main() {\n' + "".join(checks) + "}\n"


def interpreter():
    with tempfile.TemporaryDirectory(prefix="lanyard-text-nat-database-") as directory:
        program = Path(directory) / "program.lan"
        for name, _expression, body, error in CASES:
            program.write_text(source() + "def main : Cx -> Uri -> Response := "
                               f"fun (cx : Cx) (uri : Uri) => Response.text Bytes (render {name})\n")
            actual = run(DRIVER, "run", "--request", "/", program)
            expected = (f"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n"
                        f"Content-Length: {len(body.encode())}\r\n\r\n{body}").encode()
            passes = ((actual.returncode == 1 and not actual.stdout and body.encode() in actual.stderr)
                      if error else (actual.returncode == 0 and not actual.stderr and actual.stdout == expected))
            if not passes:
                sys.exit(f"LAN-TEXT-NAT-DATABASE FAIL {name}: {actual.stdout!r} {actual.stderr!r}")
    print(f"LAN-TEXT-NAT-DATABASE OK interpreter observations={len(CASES)}")


def prepare(args):
    destination = args.prepare.absolute()
    program = destination.with_suffix(".lan")
    if destination.exists() or program.exists():
        sys.exit("LAN-TEXT-NAT-DATABASE FAIL: output and sibling source must be fresh")
    destination.parent.mkdir(parents=True, exist_ok=True)
    program.write_text(source() + "def main : Nat := create\n")
    require(run(sys.executable, "-P", ROOT / "dev/prepare-crate.py", "--source", program,
                "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock,
                "--output", destination))
    (destination / "src/main.rs").write_text(require(run(DRIVER, "emit", "--target", program)) + harness())
    (destination / "cases.json").write_text(json.dumps(CASES, indent=2) + "\n")
    print(f"LAN-TEXT-NAT-DATABASE PREPARED manifest={destination / 'Cargo.toml'}")


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
            sys.exit(f"LAN-TEXT-NAT-DATABASE FAIL: {actual.stdout!r} {actual.stderr!r}")
        print(f"LAN-TEXT-NAT-DATABASE OK native observations={len(CASES)}")


if __name__ == "__main__":
    main()
