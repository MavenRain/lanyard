"""Check native concatenation and validation in both generated error variants."""
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
def concat : Bytes -> Bytes -> Bytes := Text.concat Bytes
def join : Bytes -> Bytes -> Response := fun (left : Bytes) (right : Bytes) =>
  Response.text Bytes (concat left right)
def captured : Response :=
  let prefix : Bytes := b"prefix:" in
  let append : Bytes -> Bytes := fun (value : Bytes) => Text.concat Bytes prefix value in
  Response.text Bytes (append b"captured")
def nested : Response := Response.text Bytes (Text.concat Bytes b"a" (Text.concat Bytes b"b" b"c"))
def shared : Response := let text : Bytes := b"twice" in join text text
def page : Response := Response.html Bytes
  (Text.concat Bytes b"<p>" (Text.concat Bytes (Html.text Bytes b"<script>&") b"</p>"))
def badLeftByte : Response := join (bytesCons 256 bytesNil) b"ok"
def badRightByte : Response := join b"ok" (bytesCons 256 bytesNil)
def badLeftUtf8 : Response := join (bytesCons 255 bytesNil) b"ok"
def badRightUtf8 : Response := join b"ok" (bytesCons 255 bytesNil)
def splitUtf8 : Response := join (bytesCons 195 bytesNil) (bytesCons 169 bytesNil)
def unusedLeft : Response := let ignored : Bytes := Text.concat Bytes (bytesCons 255 bytesNil) b"ok" in join b"ok" b""
def unusedRight : Response := let ignored : Bytes := Text.concat Bytes b"ok" (bytesCons 255 bytesNil) in join b"ok" b""
def main : Response := join b"left" b"right"
"""
GOOD = [("", ""), ("", "right"), ("left", ""), ("left", "right"),
        ("café", "日😀"), ("a\0", "\r\nb"), ("<b>", "&lt;\"'"),
        ("x" * 256, "y" * 256)]
ERRORS = [("badLeftByte", "ModelByteRange"), ("badRightByte", "ModelByteRange"),
          ("badLeftUtf8", "ModelUtf8"), ("badRightUtf8", "ModelUtf8"),
          ("splitUtf8", "ModelUtf8"), ("unusedLeft", "ModelUtf8"), ("unusedRight", "ModelUtf8")]
OBSERVATIONS = len(GOOD) + 4 + len(ERRORS)


def run(*command):
    return subprocess.run([str(arg) for arg in command], cwd=ROOT,
                          text=True, capture_output=True, timeout=180)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-CONCAT-NATIVE FAIL: {result.stdout}{result.stderr}")
    return result.stdout


def rust_string(value):
    escapes = {'"': '\\"', '\\': '\\\\'}
    return '"' + ''.join(escapes.get(char, f"\\u{{{ord(char):x}}}" if ord(char) < 32
                                   or ord(char) == 127 else char) for char in value) + '"'


def harness(*, ordered=False):
    checks = []

    def observation(expression):
        checks.append(f'    println!("CONCAT{len(checks)} {{}}", {expression});\n')

    for left, right in GOOD:
        arguments = ", ".join(f'Arc::new(lan_model_text_from_{b"Bytes".hex()}({rust_string(text)}.to_owned()))'
                              for text in (left, right))
        observation(f'observe(f_{b"join".hex()}({arguments}), {rust_string(left + right)}, "text/plain; charset=utf-8").await.unwrap_or(false)')
    for name, expected, content_type in [("captured", "prefix:captured", "text/plain"),
                                         ("nested", "abc", "text/plain"), ("shared", "twicetwice", "text/plain"),
                                         ("page", "<p>&lt;script&gt;&amp;</p>", "text/html")]:
        observation(f'observe(f_{name.encode().hex()}(), {rust_string(expected)}, "{content_type}; charset=utf-8").await.unwrap_or(false)')
    for name, error in ERRORS:
        observation(f'format!("{{:?}}", f_{name.encode().hex()}()) == "Err({error})"')
    if len(checks) != OBSERVATIONS:
        sys.exit("LAN-CONCAT-NATIVE FAIL: observation count differs")
    if ordered:
        observation(f'observe(f_{b"ordered".hex()}().await, "leftright", "text/plain; charset=utf-8").await.unwrap_or(false)')
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
        sys.exit("LAN-CONCAT-NATIVE FAIL: output and sibling source must be fresh")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(BASE)
    require(run(sys.executable, "-P", ROOT / "dev/prepare-crate.py", "--source", source,
                "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock,
                "--output", destination))
    (destination / "src/main.rs").write_text(require(run(DRIVER, "emit", "--target", source)) + harness())
    order = (ROOT / "test/fixtures/concat-order.lan").read_text()
    order = order[order.index("model Piece"):].replace("def main :", "def ordered :")
    source.write_text(BASE + order)
    binary_dir = destination / "src/bin"
    binary_dir.mkdir()
    (binary_dir / "async_concat.rs").write_text(require(run(DRIVER, "emit", "--target", source)) + harness(ordered=True))
    (destination / "cases.json").write_text(json.dumps({"pairs": GOOD, "errors": ERRORS,
                                                       "observations": {"sync": OBSERVATIONS, "async": OBSERVATIONS + 1}}, indent=2) + "\n")
    print(f"LAN-CONCAT-NATIVE PREPARED manifest={destination / 'Cargo.toml'} observations={OBSERVATIONS}")


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
        for binary in args.check:
            result = run(binary.absolute())
            count = OBSERVATIONS + (1 if binary.name == "async_concat" else 0)
            expected = [f"CONCAT{index} true" for index in range(count)]
            if result.returncode != 0 or result.stderr or result.stdout.splitlines() != expected:
                sys.exit(f"LAN-CONCAT-NATIVE FAIL: {binary}: {result.stdout}{result.stderr}")
            print(f"LAN-CONCAT-NATIVE OK binary={binary.name} observations={count}")


if __name__ == "__main__":
    main()
