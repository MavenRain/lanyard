"""Validate emitted text responses against the pinned Topcoat response and body APIs."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = """mu Bytes : Type 0 :=
| bytesNil : Bytes
| bytesCons (head : Nat) (tail : Bytes) : Bytes
def render : Bytes -> Response := Response.text Bytes
def captured : Response :=
  let text : Bytes := b"captured" in
  let read : prod () -> Bytes := fun (u : prod ()) => text in Response.text Bytes (read ())
def nested : Response :=
  let clean : Bytes -> Bytes := fun (text : Bytes) => Text.trim Bytes text in Response.text Bytes (clean b" nested ")
def badByte : Response := render (bytesCons 256 bytesNil)
def badUtf8 : Response := render (bytesCons 255 bytesNil)
def unused : Response := let ignored : Response := badUtf8 in render b"ok"
def main : Response := render b"hello"
"""
GOOD = ["", "hello", "café", "日😀", "a\0b", "a\r\n\r\nX-Header:yes", "<b>hello</b>"]
OBSERVATIONS = len(GOOD) + 5


def run(*command):
    return subprocess.run([str(arg) for arg in command], cwd=ROOT,
                          text=True, capture_output=True, timeout=180)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-RESPONSE-NATIVE FAIL: {result.stdout}{result.stderr}")
    return result.stdout


def rust_string(value):
    escapes = {'"': '\\"', '\\': '\\\\'}
    return '"' + ''.join(escapes.get(char, f"\\u{{{ord(char):x}}}" if ord(char) < 32
                                   or ord(char) == 127 else char) for char in value) + '"'


def harness():
    checks = []
    for text in GOOD:
        literal = rust_string(text)
        argument = f'Arc::new(lan_model_text_from_{b"Bytes".hex()}({literal}.to_owned()))'
        checks.append(f'    println!("RESPONSE{len(checks)} {{}}", '
                      f'observe(f_{b"render".hex()}({argument}), {literal}).await.unwrap_or(false));\n')
    checks.append(f'    println!("RESPONSE{len(checks)} {{}}", '
                  f'observe(f_{b"captured".hex()}(), "captured").await.unwrap_or(false));\n')
    checks.append(f'    println!("RESPONSE{len(checks)} {{}}", '
                  f'observe(f_{b"nested".hex()}(), "nested").await.unwrap_or(false));\n')
    for name, error in [("badByte", "ModelByteRange"), ("badUtf8", "ModelUtf8"), ("unused", "ModelUtf8")]:
        checks.append(f'    println!("RESPONSE{len(checks)} {{}}", '
                      f'format!("{{:?}}", f_{name.encode().hex()}()) == "Err({error})");\n')
    return '''
async fn observe(value: Result<topcoat::router::response::Response, Error>, expected: &str) -> Option<bool> {
    let (parts, body) = value.ok()?.into_parts();
    let bytes = topcoat::router::to_bytes(body, 8192).await.ok()?;
    Some(parts.status == topcoat::router::StatusCode::OK
        && parts.headers.get(topcoat::router::header::CONTENT_TYPE)? == "text/plain; charset=utf-8"
        && bytes.as_ref() == expected.as_bytes())
}
#[tokio::main(flavor = "current_thread")]
async fn main() {
''' + "".join(checks) + "}\n"


def prepare(args):
    destination = args.prepare.absolute()
    source = destination.with_suffix(".lan")
    if destination.exists() or source.exists():
        sys.exit("LAN-RESPONSE-NATIVE FAIL: output and sibling source must be fresh")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(BASE)
    require(run(sys.executable, "-P", ROOT / "dev/prepare-crate.py", "--source", source,
                "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock,
                "--output", destination))
    (destination / "src/main.rs").write_text(require(run(DRIVER, "emit", "--target", source)) + harness())
    source.write_text(BASE + 'def withDatabase : Db -> Response := fun (db : Db) => '
                      'let ready : prod () := Db.push_schema db in render b"database"\n')
    binary_dir = destination / "src/bin"
    binary_dir.mkdir()
    (binary_dir / "async_response.rs").write_text(require(run(DRIVER, "emit", "--target", source)) + harness())
    (destination / "cases.json").write_text(json.dumps({"bodies": GOOD, "observations": OBSERVATIONS}, indent=2) + "\n")
    print(f"LAN-RESPONSE-NATIVE PREPARED manifest={destination / 'Cargo.toml'} observations={OBSERVATIONS}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", type=Path)
    action.add_argument("--check", type=Path, nargs="+")
    parser.add_argument("--toasty", type=Path)
    parser.add_argument("--topcoat", type=Path)
    parser.add_argument("--lock", type=Path)
    args = parser.parse_args()
    if args.prepare:
        if not all((args.toasty, args.topcoat, args.lock)):
            parser.error("--prepare requires --toasty, --topcoat and --lock")
        prepare(args)
    else:
        expected = [f"RESPONSE{index} true" for index in range(OBSERVATIONS)]
        for binary in args.check:
            result = run(binary.absolute())
            output = require(result)
            if output.splitlines() != expected or result.stderr:
                sys.exit(f"LAN-RESPONSE-NATIVE FAIL: {binary}: {output}{result.stderr}")
        print(f"LAN-RESPONSE-NATIVE OK binaries={len(args.check)} observations={len(args.check) * OBSERVATIONS}")


if __name__ == "__main__":
    main()
