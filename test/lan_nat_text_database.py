"""Compare database-backed Todo pages and effectful Nat inputs in both runtimes."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
CONNECT = ('let db : Db := Db.connect Todo Bytes b"sqlite::memory:" in '
           "let ready : prod () := Db.push_schema db in ")
CASES = [
    ("empty", "page db", "<ul></ul>", "text/html"),
    ("single", 'let row : Todo := Todo.create (tuple (0, b"")) db in page db',
     "<ul><li><a href='/todos/0'></a></li></ul>", "text/html"),
    ("multiple", 'let last : Todo := Todo.create (tuple (20, b"café")) db in '
     'let first : Todo := Todo.create (tuple (3, b"<write> & test")) db in page db',
     "<ul><li><a href='/todos/3'>&lt;write&gt; &amp; test</a></li>"
     "<li><a href='/todos/20'>café</a></li></ul>", "text/html"),
    ("once", "Response.text Bytes (Text.from_nat Bytes (allocate db))", "257", "text/plain"),
    ("retained", "let ignored : Bytes := Text.from_nat Bytes (allocate db) in page db",
     "<ul><li><a href='/todos/257'>saved</a></li></ul>", "text/html"),
]


def source():
    prefix = (ROOT / "test/fixtures/todo-list.lan").read_text().split("def main :")[0]
    allocation = ("def allocate : Db -> Nat := fun (db : Db) => "
                  'let row : Todo := Todo.create (tuple (257, b"saved")) db in row.0\n')
    definitions = "".join(f"def {name} : Response := {CONNECT}{expression}\n"
                          for name, expression, _body, _type in CASES)
    return prefix + allocation + definitions


def run(*command):
    return subprocess.run([str(arg) for arg in command], cwd=ROOT,
                          capture_output=True, timeout=180)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-NAT-TEXT-DATABASE FAIL: {result.stdout.decode()}{result.stderr.decode()}")
    return result.stdout.decode()


def harness():
    checks = "".join(f'    println!("DATABASE {name} {{}}", observe(f_{name.encode().hex()}().await, '
                     f'{json.dumps(body, ensure_ascii=False)}, "{content_type}; charset=utf-8")'
                     '.await.unwrap_or(false));\n'
                     for name, _expression, body, content_type in CASES)
    return """
async fn observe(value: Result<topcoat::router::response::Response, Error>, expected: &str, content_type: &str) -> Option<bool> {
    let (parts, body) = value.ok()?.into_parts();
    let bytes = topcoat::router::to_bytes(body, 8192).await.ok()?;
    Some(parts.status == topcoat::router::StatusCode::OK
        && parts.headers.get(topcoat::router::header::CONTENT_TYPE)? == content_type
        && bytes.as_ref() == expected.as_bytes())
}
#[tokio::main(flavor = "current_thread")]
async fn main() {
""" + checks + "}\n"


def interpreter():
    with tempfile.TemporaryDirectory(prefix="lanyard-nat-text-database-") as directory:
        program = Path(directory) / "program.lan"
        for name, _expression, body, content_type in CASES:
            program.write_text(source() + "def main : Cx -> Uri -> Response := "
                               f"fun (cx : Cx) (uri : Uri) => {name}\n")
            actual = run(DRIVER, "run", "--request", "/", program)
            expected = (f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}; charset=utf-8\r\n"
                        f"Content-Length: {len(body.encode())}\r\n\r\n{body}").encode()
            if actual.returncode != 0 or actual.stderr or actual.stdout != expected:
                sys.exit(f"LAN-NAT-TEXT-DATABASE FAIL {name}: {actual.stdout!r} {actual.stderr!r}")
    print(f"LAN-NAT-TEXT-DATABASE OK interpreter observations={len(CASES)}")


def prepare(args):
    destination = args.prepare.absolute()
    program = destination.with_suffix(".lan")
    if destination.exists() or program.exists():
        sys.exit("LAN-NAT-TEXT-DATABASE FAIL: output and sibling source must be fresh")
    destination.parent.mkdir(parents=True, exist_ok=True)
    program.write_text(source() + "def main : Response := multiple\n")
    require(run(sys.executable, "-P", ROOT / "dev/prepare-crate.py", "--source", program,
                "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock,
                "--output", destination))
    (destination / "src/main.rs").write_text(require(run(DRIVER, "emit", "--target", program)) + harness())
    (destination / "cases.json").write_text(json.dumps(CASES, ensure_ascii=False, indent=2) + "\n")
    print(f"LAN-NAT-TEXT-DATABASE PREPARED manifest={destination / 'Cargo.toml'}")


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
        expected = [f"DATABASE {name} true" for name, _expression, _body, _type in CASES]
        if actual.returncode != 0 or actual.stderr or actual.stdout.decode().splitlines() != expected:
            sys.exit(f"LAN-NAT-TEXT-DATABASE FAIL: {actual.stdout!r} {actual.stderr!r}")
        print(f"LAN-NAT-TEXT-DATABASE OK native observations={len(CASES)}")


if __name__ == "__main__":
    main()
