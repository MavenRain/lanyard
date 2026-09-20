"""Check optional form fields through the CLI and compiled target adapters."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
BASE = """mu Bytes : Type 0 :=
| bytesNil : Bytes
| bytesCons (head : Nat) (tail : Bytes) : Bytes
def Bool : Type 0 := sum ((prod () : Type 0), (prod () : Type 0))
"""
CASES = [
    ("", "title", False), ("title=", "title", True), ("title=x", "other", False),
    ("title=other", "other", False), ("Title=x", "title", False), ("title=x", "", False),
    ("%74itle=caf%C3%A9", "title", True), ("a+b=x", "a b", True),
    ("a%2Bb=x", "a+b", True), ("a%252Bb=x", "a%2Bb", True),
    ("%E6%97%A5=x", "日", True), ("a%00b=x", "a\0b", True),
    ("first=1&last=", "last", True), ("a%26b%3Dc=x", "a&b=c", True),
    ("title=" + "x" * 8186, "title", True),
    ("&".join(f"k{i}=" for i in range(128)), "k127", True),
]
INVALID = [
    "title=x&other=%", "title", "=x", "title=x&title=y", "title=x&%74itle=y",
    "title=x&a=1&a=2", "title=x&", "title=x&&a=1", "title=%0", "title=%GG",
    "title=x&other=%ff", "title=%c0%af", "title=%ed%a0%80", "title=%f4%90%80%80",
    "title=%e2%82", "%ff=x&title=ok", "title=" + "x" * 8187,
    "&".join(f"k{i}=" for i in range(129)),
]
KINDS = [("DIRECT", "presence", "Bytes"), ("CAPTURED", "captured", "Bytes"),
         ("ALTERNATE", "other", "Other")]


def run(*command):
    return subprocess.run(list(map(str, command)), cwd=ROOT, capture_output=True, timeout=180)


def require(result):
    if result.returncode:
        sys.exit(f"LAN-FORM-HAS FAIL: {result.stdout!r} {result.stderr!r}")
    return result.stdout.decode()


def source():
    return BASE + """mu Other : Type 0 :=
| otherNil : Other
| otherCons (head : Nat) (tail : Other) : Other
def render : Bool -> Bytes := fun (present : Bool) => case present with
| 1 (u : prod ()) => b"present"
| 0 (u : prod ()) => b"absent"
def alias : Bytes -> Bytes -> Bool := Form.has Bytes
def presence : Bytes -> Bytes -> Bytes := fun (body : Bytes) (name : Bytes) => render (alias body name)
def captured : Bytes -> Bytes -> Bytes := fun (body : Bytes) (name : Bytes) =>
  let lookup : Bytes -> Bool := fun (key : Bytes) => Form.has Bytes body key in render (lookup name)
def other : Other -> Other -> Bytes := fun (body : Other) (name : Other) => render (Form.has Other body name)
def unused : Bytes -> Nat := fun (body : Bytes) => let ignored : Bool := Form.has Bytes body b"title" in 1
def ordered : Bool := Form.has Bytes (bytesCons 255 bytesNil)
  (let invalid : Uri := Uri.from_text Bytes b"//host" in b"title")
def main : Bytes := presence b"title=" b"title"
"""


def function(name):
    return "f_" + name.encode().hex()


def rust_string(value):
    return json.dumps(value, ensure_ascii=False).replace("\\u0000", "\\0")


def harness():
    rows = ",\n".join(f"({rust_string(body)}, {rust_string(name)}, {str(expected).lower()})"
                       for body, name, expected in CASES)
    result = "\nfn main() {\nlet cases = [\n" + rows + "\n];\n"
    result += "cases.iter().enumerate().for_each(|(index, (body, name, expected))| {\n"
    for kind, name, family in KINDS:
        encode = "lan_model_text_from_" + family.encode().hex()
        result += f"""let actual = {function(name)}(Arc::new({encode}(body.to_string())), Arc::new({encode}(name.to_string())))
    .and_then(|value| lan_model_text_to_4279746573(&value));
println!("{kind} {{index}} {{}}", actual.as_deref().ok() == Some(if *expected {{ "present" }} else {{ "absent" }}));
"""
    result += "});\nlet invalid = [\n" + ",\n".join(map(rust_string, INVALID)) + "\n];\n"
    result += "invalid.iter().enumerate().for_each(|(index, body)| {\n"
    for label, key in [("PRESENT", "title"), ("ABSENT", "absent")]:
        result += f"""let rejected = matches!({function('presence')}(Arc::new(lan_model_text_from_4279746573(body.to_string())),
    Arc::new(lan_model_text_from_4279746573("{key}".to_string()))), Err(Error::InvalidForm));
println!("REJECT-{label} {{index}} {{rejected}}");
"""
    result += f"""println!("UNUSED {{index}} {{}}", matches!({function('unused')}(Arc::new(lan_model_text_from_4279746573(body.to_string()))), Err(Error::InvalidForm)));
}});
println!("ORDER {{}}", matches!({function('ordered')}(), Err(Error::InvalidUri)));
}}
"""
    return result


def expected_native(unchecked=False):
    rows = []
    for index, (body, name, expected) in enumerate(CASES):
        actual = any(field.partition("=")[0] == name for field in body.split("&") if "=" in field)
        result = str(actual == expected if unchecked else True).lower()
        rows.extend(f"{kind} {index} {result}" for kind, _name, _family in KINDS)
    for index in range(len(INVALID)):
        rows.extend(f"{kind} {index} {'false' if unchecked else 'true'}"
                    for kind in ("REJECT-PRESENT", "REJECT-ABSENT", "UNUSED"))
    return rows + ["ORDER true"]


def prepare(args):
    destination = args.prepare.absolute()
    program = destination.with_suffix(".lan")
    if destination.exists() or program.exists():
        sys.exit("LAN-FORM-HAS FAIL: output and sibling source must be fresh")
    destination.parent.mkdir(parents=True, exist_ok=True)
    program.write_text(source())
    require(run(sys.executable, "-P", ROOT / "dev/prepare-crate.py", "--source", program,
                "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock,
                "--output", destination))
    code = require(run(DRIVER, "emit", "--target", program)) + harness()
    (destination / "src/main.rs").write_text(code)
    marker = "Ok(lan_form_fields(body)?.iter().any(|(key, _value)| key == name))"
    if code.count(marker) != 1:
        sys.exit("LAN-FORM-HAS FAIL: expected one checked presence helper")
    unchecked = "Ok(body.split('&').filter_map(|field| field.split_once('=')).any(|(key, _value)| key == name))"
    (destination / "src/bin").mkdir()
    (destination / "src/bin/form-has-unchecked.rs").write_text(code.replace(marker, unchecked))
    print(f"LAN-FORM-HAS PREPARED manifest={destination / 'Cargo.toml'}")


def check(target):
    for name, unchecked in [("lanyard-program", False), ("form-has-unchecked", True)]:
        actual = run(target.absolute() / name)
        if actual.returncode or actual.stderr or actual.stdout.decode().splitlines() != expected_native(unchecked):
            sys.exit(f"LAN-FORM-HAS FAIL {name}: {actual.stdout!r} {actual.stderr!r}")
    print(f"LAN-FORM-HAS NATIVE OK observations={len(expected_native())} mutants=1")


class FormHas(unittest.TestCase):
    def test_optional_checkbox(self):
        for body, expected in [("", b"pending"), ("title=x", b"pending"),
                               ("completed=", b"completed"), ("%63ompleted=on", b"completed")]:
            with self.subTest(body=body):
                actual = run(DRIVER, "run", "--request", "/todos", "--form", body,
                             ROOT / "test/fixtures/form-has.lan")
                self.assertEqual(actual.returncode, 0, actual.stderr)
                self.assertEqual(actual.stderr, b"")
                self.assertEqual(actual.stdout.split(b"\r\n\r\n", 1)[-1], expected)

    def test_query_presence(self):
        with tempfile.TemporaryDirectory(prefix="lanyard-form-has-") as temporary:
            program = Path(temporary) / "query.lan"
            program.write_text(BASE + """def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) =>
  case Form.has Bytes (Uri.query Bytes uri) b"done" with
  | 1 (u : prod ()) => Response.text Bytes b"present"
  | 0 (u : prod ()) => Response.text Bytes b"absent"
""")
            for uri, expected in [("/todos", b"absent"), ("/todos?", b"absent"),
                                  ("/todos?other=x", b"absent"), ("/todos?done=", b"present")]:
                actual = run(DRIVER, "run", "--request", uri, program)
                self.assertEqual(actual.returncode, 0, actual.stderr)
                self.assertEqual(actual.stdout.split(b"\r\n\r\n", 1)[-1], expected)
            actual = run(DRIVER, "run", "--request", "/todos?done=x&bad=%ff", program)
            self.assertNotEqual(actual.returncode, 0)
            self.assertEqual(actual.stdout, b"")
            self.assertIn(b"UTF-8", actual.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--prepare", type=Path)
    action.add_argument("--check", type=Path)
    parser.add_argument("--toasty", type=Path)
    parser.add_argument("--topcoat", type=Path)
    parser.add_argument("--lock", type=Path)
    args, remaining = parser.parse_known_args()
    if args.prepare or args.check:
        if remaining:
            parser.error("unexpected native arguments")
        if args.prepare:
            if not all((args.toasty, args.topcoat, args.lock)):
                parser.error("--prepare requires --toasty, --topcoat and --lock")
            prepare(args)
        else:
            check(args.check)
    else:
        result = unittest.main(argv=[sys.argv[0], *remaining], exit=False).result
        if result.wasSuccessful():
            print(f"LAN-FORM-HAS CLI OK groups={result.testsRun}")
        sys.exit(0 if result.wasSuccessful() else 1)
