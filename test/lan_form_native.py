"""Prepare and check form adapters against the pinned target libraries."""
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
def lookup : Bytes -> Bytes -> Bytes := Form.field Bytes
def captured : Bytes :=
  let body : Bytes := b"title=captured" in
  let read : Bytes -> Bytes := fun (name : Bytes) => Form.field Bytes body name in
  read b"title"
def badByte : Bytes := lookup (bytesCons 256 bytesNil) b"title"
def badUtf8 : Bytes := lookup (bytesCons 255 bytesNil) b"title"
def badName : Bytes := lookup b"title=x" (bytesCons 255 bytesNil)
def unused : Bytes := let ignored : Bytes := lookup b"title=%" b"title" in b"ok"
def argumentOrder : Bytes := Form.field Bytes (bytesCons 255 bytesNil)
  (let invalid : Uri := Uri.from_text Bytes b"//host" in b"title")
def main : Bytes := lookup b"title=x" b"title"
"""
GOOD = [
    ("title=write+tests", "title", "write tests"), ("title=", "title", ""),
    ("%74itle=caf%C3%A9", "title", "café"), ("title=café", "title", "café"),
    ("title=%26%3D%2B%25%00", "title", "&=+%\0"), ("title=%2526", "title", "%26"),
    ("other=x&title=a=b=c", "title", "a=b=c"),
    ("%E6%97%A5=%F0%9F%98%80", "日", "😀"),
    ("a+b=space&a%2Bb=plus", "a+b", "plus"),
    ("title=" + "x" * 8186, "title", "x" * 8186),
    ("&".join(f"k{i}={i}" for i in range(128)), "k127", "127"),
]
BAD = ["", "other=value", "title", "=value", "title=one&title=two",
       "title=one&%74itle=two", "title=x&a=1&a=2", "title=x&", "&title=x",
       "title=x&&a=1", "title=%", "title=%0", "title=%GG", "title=x&other=%ff",
       "title=%c0%af", "title=%ed%a0%80", "title=%f4%90%80%80", "title=%e2%82",
       "%ff=x&title=ok", "title=" + "x" * 8187,
       "&".join(f"k{i}=x" for i in range(129))]
OBSERVATIONS = len(GOOD) + len(BAD) + 6


def run(*command):
    return subprocess.run([str(arg) for arg in command], cwd=ROOT,
                          text=True, capture_output=True, timeout=180)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-FORM-NATIVE FAIL: {result.stdout}{result.stderr}")
    return result.stdout


def rust_string(value):
    escapes = {'"': '\\"', '\\': '\\\\'}
    return '"' + ''.join(escapes.get(char, f"\\u{{{ord(char):x}}}" if ord(char) < 32
                                   or ord(char) == 127 else char) for char in value) + '"'


def harness():
    convert = "f_" + b"lookup".hex()
    from_text = "lan_model_text_from_" + b"Bytes".hex()
    to_text = "lan_model_text_to_" + b"Bytes".hex()
    checks = []
    for body, name, expected in GOOD + [(body, "title", None) for body in BAD]:
        args = ", ".join(f"Arc::new({from_text}({rust_string(value)}.to_owned()))"
                         for value in (body, name))
        call = f"{convert}({args})"
        condition = (f"{call}.and_then(|value| {to_text}(&value)).map(|text| text == "
                     f"{rust_string(expected)}).unwrap_or(false)" if expected is not None
                     else f'format!("{{:?}}", {call}) == "Err(InvalidForm)"')
        checks.append(f'    println!("FORM{len(checks)} {{}}", {condition});\n')
    checks.append(f'    println!("FORM{len(checks)} {{}}", f_{b"captured".hex()}()'
                  f'.and_then(|value| {to_text}(&value)).map(|text| text == "captured").unwrap_or(false));\n')
    for name, error in [("badByte", "ModelByteRange"), ("badUtf8", "ModelUtf8"),
                        ("badName", "ModelUtf8"), ("unused", "InvalidForm"),
                        ("argumentOrder", "InvalidUri")]:
        checks.append(f'    println!("FORM{len(checks)} {{}}", '
                      f'format!("{{:?}}", f_{name.encode().hex()}()) == "Err({error})");\n')
    return "\nfn main() {\n" + "".join(checks) + "}\n"


def prepare(args):
    destination = args.prepare.absolute()
    source = destination.with_suffix(".lan")
    if destination.exists() or source.exists():
        sys.exit("LAN-FORM-NATIVE FAIL: output and sibling source must be fresh")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(BASE)
    require(run(sys.executable, "-P", ROOT / "dev/prepare-crate.py", "--source", source,
                "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock,
                "--output", destination))
    (destination / "src/main.rs").write_text(require(run(DRIVER, "emit", "--target", source)) + harness())
    source.write_text(BASE + 'def withDatabase : Db -> Bytes := fun (db : Db) => '
                      'let ready : prod () := Db.push_schema db in lookup b"title=x" b"title"\n')
    binary_dir = destination / "src/bin"
    binary_dir.mkdir()
    (binary_dir / "async_form.rs").write_text(require(run(DRIVER, "emit", "--target", source)) + harness())
    (destination / "cases.json").write_text(json.dumps({"accepted": GOOD, "refused": BAD}, indent=2) + "\n")
    print(f"LAN-FORM-NATIVE PREPARED manifest={destination / 'Cargo.toml'} observations={OBSERVATIONS}")


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
        expected = [f"FORM{index} true" for index in range(OBSERVATIONS)]
        for binary in args.check:
            result = run(binary.absolute())
            output = require(result)
            if output.splitlines() != expected or result.stderr:
                sys.exit(f"LAN-FORM-NATIVE FAIL: {binary}: {output}{result.stderr}")
        print(f"LAN-FORM-NATIVE OK binaries={len(args.check)} observations={len(args.check) * OBSERVATIONS}")


if __name__ == "__main__":
    main()
