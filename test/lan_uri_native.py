"""Prepare and check emitted URI programs against the pinned target libraries."""
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
def convert : Bytes -> Uri := Uri.from_text Bytes
def badByte : Uri := convert (bytesCons 256 bytesNil)
def badUtf8 : Uri := convert (bytesCons 255 bytesNil)
def redirect : SeeOther := topcoat.see_other (convert b"/")
def main : Uri := convert b"/"
"""
GOOD = ["/", "/todos", "/a/b?x=1&x=2", "/a??b", "/%00%0d%0A", "/%c3%a9",
        "/-._~!$&'()*+,;=:@/?", "/a//b", "/" + "a" * 8191]
BAD = ["", "relative", "https://example.com/", "//example.com/", "/space here",
       "/#fragment", "/\\", "/[x]", "/\r\nLocation: /other", "/\0", "/\x7f",
       "/café", "/%", "/%0", "/%GG", "/%0x", "/" + "a" * 8192]
OBSERVATIONS = len(GOOD) + len(BAD) + 3


def run(*command):
    return subprocess.run([str(arg) for arg in command], cwd=ROOT,
                          text=True, capture_output=True, timeout=180)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-URI-NATIVE FAIL: {result.stdout}{result.stderr}")
    return result.stdout


def rust_string(value):
    escapes = {'"': '\\"', '\\': '\\\\'}
    return '"' + ''.join(escapes.get(char, f"\\u{{{ord(char):x}}}" if ord(char) < 32
                                   or ord(char) == 127 else char) for char in value) + '"'


def harness():
    convert = "f_" + b"convert".hex()
    from_text = "lan_model_text_from_" + b"Bytes".hex()
    checks = []
    for index, value in enumerate(GOOD + BAD):
        argument = f"Arc::new({from_text}({rust_string(value)}.to_owned()))"
        call = f"{convert}({argument})"
        condition = (f"{call}.map(|uri| uri.to_string() == {rust_string(value)}).unwrap_or(false)"
                     if index < len(GOOD) else f'format!("{{:?}}", {call}) == "Err(InvalidUri)"')
        checks.append(f'    println!("URI{index} {{}}", {condition});\n')
    for name, error in [("badByte", "ModelByteRange"), ("badUtf8", "ModelUtf8")]:
        checks.append(f'    println!("URI{len(checks)} {{}}", '
                      f'format!("{{:?}}", f_{name.encode().hex()}()) == "Err({error})");\n')
    checks.append(f'    println!("URI{len(checks)} {{}}", f_{b"redirect".hex()}().is_ok());\n')
    return "\nfn main() {\n" + "".join(checks) + "}\n"


def prepare(args):
    destination = args.prepare.absolute()
    if destination.exists():
        sys.exit("LAN-URI-NATIVE FAIL: output must be a fresh directory")
    source = destination.with_suffix(".lan")
    if source.exists():
        sys.exit("LAN-URI-NATIVE FAIL: sibling source already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(BASE)
    require(run(sys.executable, "-P", ROOT / "dev/prepare-crate.py", "--source", source,
                "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock,
                "--output", destination))
    (destination / "src/main.rs").write_text(require(run(DRIVER, "emit", "--target", source)) + harness())
    source.write_text(BASE + 'def withDatabase : Db -> Uri := fun (db : Db) => '
                      'let ready : prod () := Db.push_schema db in convert b"/"\n')
    binary_dir = destination / "src/bin"
    binary_dir.mkdir()
    (binary_dir / "async_uri.rs").write_text(require(run(DRIVER, "emit", "--target", source)) + harness())
    (destination / "cases.json").write_text(json.dumps({"accepted": GOOD, "refused": BAD}, indent=2) + "\n")
    print(f"LAN-URI-NATIVE PREPARED manifest={destination / 'Cargo.toml'} observations={OBSERVATIONS}")


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
        expected = [f"URI{index} true" for index in range(OBSERVATIONS)]
        for binary in args.check:
            result = run(binary.absolute())
            output = require(result)
            if output.splitlines() != expected or result.stderr:
                sys.exit(f"LAN-URI-NATIVE FAIL: {binary}: {output}{result.stderr}")
        print(f"LAN-URI-NATIVE OK binaries={len(args.check)} observations={len(args.check) * OBSERVATIONS}")


if __name__ == "__main__":
    main()
