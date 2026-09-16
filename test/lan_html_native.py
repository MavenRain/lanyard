"""Check native HTML escaping, response metadata and byte validation."""
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
def raw : Bytes -> Response := Response.html Bytes
def render : Bytes -> Response := fun (text : Bytes) => Response.html Bytes (Html.text Bytes text)
def captured : Response :=
  let text : Bytes := b"<captured>" in
  let read : prod () -> Bytes := fun (u : prod ()) => Html.text Bytes text in Response.html Bytes (read ())
def nested : Response :=
  let clean : Bytes -> Bytes := fun (text : Bytes) => Html.text Bytes (Text.trim Bytes text) in Response.html Bytes (clean b" <nested> ")
def plain : Response := Response.text Bytes b"<plain>"
def badByte : Response := raw (bytesCons 256 bytesNil)
def badUtf8 : Response := raw (bytesCons 255 bytesNil)
def badEscape : Response := render (bytesCons 255 bytesNil)
def unused : Response := let ignored : Bytes := Html.text Bytes (bytesCons 255 bytesNil) in raw b"ok"
def main : Response := render b"<hello>"
"""
GOOD = [("", ""), ("hello", "hello"), ("café", "café"), ("日😀", "日😀"),
        ("a\0b", "a\0b"), ("a\r\n\r\nX-Header:yes", "a\r\n\r\nX-Header:yes"),
        ("<b>&</b>", "&lt;b&gt;&amp;&lt;/b&gt;"), ("&lt;&amp;", "&amp;lt;&amp;amp;"),
        ("\"'=/", "\"'=/")]
OBSERVATIONS = len(GOOD) * 2 + 7


def run(*command):
    return subprocess.run([str(arg) for arg in command], cwd=ROOT,
                          text=True, capture_output=True, timeout=180)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-HTML-NATIVE FAIL: {result.stdout}{result.stderr}")
    return result.stdout


def rust_string(value):
    escapes = {'"': '\\"', '\\': '\\\\'}
    return '"' + ''.join(escapes.get(char, f"\\u{{{ord(char):x}}}" if ord(char) < 32
                                   or ord(char) == 127 else char) for char in value) + '"'


def harness():
    checks = []

    def observation(expression):
        checks.append(f'    println!("HTML{len(checks)} {{}}", {expression});\n')

    for text, escaped in GOOD:
        argument = f'Arc::new(lan_model_text_from_{b"Bytes".hex()}({rust_string(text)}.to_owned()))'
        for name, expected in [("raw", text), ("render", escaped)]:
            observation(f'observe(f_{name.encode().hex()}({argument}), {rust_string(expected)}, "text/html; charset=utf-8").await.unwrap_or(false)')
    for name, expected, content_type in [
        ("captured", "&lt;captured&gt;", "text/html"),
        ("nested", "&lt;nested&gt;", "text/html"),
        ("plain", "<plain>", "text/plain"),
    ]:
        observation(f'observe(f_{name.encode().hex()}(), {rust_string(expected)}, "{content_type}; charset=utf-8").await.unwrap_or(false)')
    for name, error in [("badByte", "ModelByteRange"), ("badUtf8", "ModelUtf8"),
                        ("badEscape", "ModelUtf8"), ("unused", "ModelUtf8")]:
        observation(f'format!("{{:?}}", f_{name.encode().hex()}()) == "Err({error})"')
    if len(checks) != OBSERVATIONS:
        sys.exit("LAN-HTML-NATIVE FAIL: observation count differs")
    return '''
async fn observe(value: Result<topcoat::router::response::Response, Error>, expected: &str, content_type: &str) -> Option<bool> {
    let (parts, body) = value.ok()?.into_parts();
    let bytes = topcoat::router::to_bytes(body, 8192).await.ok()?;
    Some(parts.status == topcoat::router::StatusCode::OK
        && parts.headers.get(topcoat::router::header::CONTENT_TYPE)? == content_type
        && bytes.as_ref() == expected.as_bytes())
}
#[tokio::main(flavor = "current_thread")]
async fn main() {
''' + "".join(checks) + "}\n"


def prepare(args):
    destination = args.prepare.absolute()
    source = destination.with_suffix(".lan")
    if destination.exists() or source.exists():
        sys.exit("LAN-HTML-NATIVE FAIL: output and sibling source must be fresh")
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
    (binary_dir / "async_html.rs").write_text(require(run(DRIVER, "emit", "--target", source)) + harness())
    (destination / "cases.json").write_text(json.dumps({"bodies": GOOD, "observations": OBSERVATIONS}, indent=2) + "\n")
    print(f"LAN-HTML-NATIVE PREPARED manifest={destination / 'Cargo.toml'} observations={OBSERVATIONS}")


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
        expected = [f"HTML{index} true" for index in range(OBSERVATIONS)]
        for binary in args.check:
            result = run(binary.absolute())
            output = require(result)
            if output.splitlines() != expected or result.stderr:
                sys.exit(f"LAN-HTML-NATIVE FAIL: {binary}: {output}{result.stderr}")
        print(f"LAN-HTML-NATIVE OK binaries={len(args.check)} observations={len(args.check) * OBSERVATIONS}")


if __name__ == "__main__":
    main()
