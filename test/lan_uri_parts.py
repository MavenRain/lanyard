"""Check URI components through the interpreter, native adapters and HTTP."""
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
"""
CASES = [
    ("/", "/", ""), ("/todos", "/todos", ""), ("/todos?", "/todos", ""),
    ("/todos?filter=done", "/todos", "filter=done"), ("/?", "/", ""),
    ("/??x?y", "/", "?x?y"),
    ("/a%3fb?x=%3F%26+&y=%2f", "/a%3fb", "x=%3F%26+&y=%2f"),
    ("/a//b/../c?x=1&x=2", "/a//b/../c", "x=1&x=2"),
    ("/%C3%A9?name=%c3%a9", "/%C3%A9", "name=%c3%a9"),
    ("/%00?x=%FF", "/%00", "x=%FF"),
    ("/-._~!$&'()*+,;=:@/?/?:@", "/-._~!$&'()*+,;=:@/", "/?:@"),
    ("/" + "a" * 8191, "/" + "a" * 8191, ""),
    ("/?" + "b" * 8190, "/", "b" * 8190),
]
INVALID = ["https://example.com/a?q=ok", "relative", "*", "//example.com/a?q=ok",
           "/bad%?q=ok", "/ok?q=%", "/ok?q=%0", "/ok?q=%GG",
           "/?" + "a" * 8191]


def run(*command):
    return subprocess.run([str(arg) for arg in command], cwd=ROOT,
                          capture_output=True, timeout=180)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-URI-PARTS FAIL: {result.stdout!r} {result.stderr!r}")
    return result.stdout.decode()


def response(body):
    return (f"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body.encode())}\r\n\r\n{body}").encode()


def source():
    result = BASE + """mu Other : Type 0 :=
| otherNil : Other
| otherCons (head : Nat) (tail : Other) : Other
"""
    for part in ("path", "query"):
        result += f"""def {part} : Uri -> Bytes := Uri.{part} Bytes
def {part}_other : Uri -> Other := Uri.{part} Other
def {part}_roundtrip : Bytes -> Bytes := fun (text : Bytes) => {part} (Uri.from_text Bytes text)
def {part}_captured : Uri -> Bytes := fun (uri : Uri) =>
  let closure : Nat -> Bytes := fun (n : Nat) => {part} uri in closure 0
def {part}_unused : Uri -> Nat := fun (uri : Uri) => let unused : Bytes := {part} uri in 1
"""
    return result + 'def main : Bytes := path_roundtrip b"/todos?x=%2f"\n'


def function(name):
    return "f_" + name.encode().hex()


def harness():
    cases = ",\n".join("(" + ", ".join(json.dumps(value) for value in row) + ")" for row in CASES)
    invalid = ",\n".join(json.dumps(value) for value in INVALID)
    result = "\nfn main() {\nlet valid = [\n" + cases + "\n];\n"
    result += "valid.iter().enumerate().for_each(|(index, (input, path, query))| {\n"
    result += "let uri = input.parse::<topcoat::router::Uri>().map(Arc::new);\n"
    for part in ("path", "query"):
        for kind, name, family in [("DIRECT", part, "Bytes"), ("CAPTURED", part + "_captured", "Bytes"),
                                    ("ALTERNATE", part + "_other", "Other")]:
            result += f"""let actual = uri.as_ref().ok().and_then(|uri| {function(name)}(uri.clone()).ok())
    .and_then(|text| lan_model_text_to_{family.encode().hex()}(&text).ok());
println!("{part} {kind} {{index}} {{}}", actual.as_deref() == Some(*{part}));
"""
        result += f"""let actual = {function(part + '_roundtrip')}(Arc::new(lan_model_text_from_4279746573(input.to_string())))
    .and_then(|text| lan_model_text_to_4279746573(&text));
println!("{part} ROUNDTRIP {{index}} {{}}", actual.map(|text| text == *{part}).unwrap_or(false));
"""
    result += "});\nlet invalid = [\n" + invalid + "\n];\n"
    result += "invalid.iter().enumerate().for_each(|(index, input)| {\n"
    result += "let uri = input.parse::<topcoat::router::Uri>().map(Arc::new);\n"
    for part in ("path", "query"):
        for kind, name in [("REJECT", part), ("UNUSED", part + "_unused")]:
            result += f"""let rejected = uri.as_ref().map(|uri| matches!({function(name)}(uri.clone()), Err(Error::InvalidUri)))
    .unwrap_or(false);
println!("{part} {kind} {{index}} {{rejected}}");
"""
    return result + "});\n}\n"


def expected_native(unchecked=False):
    return ([f"{part} {kind} {index} true" for index in range(len(CASES))
             for part in ("path", "query") for kind in ("DIRECT", "CAPTURED", "ALTERNATE", "ROUNDTRIP")]
            + [f"{part} {kind} {index} {'false' if unchecked else 'true'}"
               for index in range(len(INVALID)) for part in ("path", "query") for kind in ("REJECT", "UNUSED")])


def prepare(args):
    destination = args.prepare.absolute()
    program = destination.with_suffix(".lan")
    if destination.exists() or program.exists():
        sys.exit("LAN-URI-PARTS FAIL: output and sibling source must be fresh")
    destination.parent.mkdir(parents=True, exist_ok=True)
    program.write_text(source())
    require(run(sys.executable, "-P", ROOT / "dev/prepare-crate.py", "--source", program,
                "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock,
                "--output", destination))
    code = require(run(DRIVER, "emit", "--target", program)) + harness()
    (destination / "src/main.rs").write_text(code)
    marker = "lan_uri_validate(&__lan_uri_text)?; "
    if code.count(marker) != 4:
        sys.exit("LAN-URI-PARTS FAIL: expected four specialized validation sites")
    (destination / "src/bin").mkdir()
    (destination / "src/bin/uri-parts-unchecked.rs").write_text(code.replace(marker, ""))
    print(f"LAN-URI-PARTS PREPARED manifest={destination / 'Cargo.toml'}")


def check(target):
    executables = [("lanyard-program", False), ("uri-parts-unchecked", True)]
    for name, unchecked in executables:
        actual = run(target.absolute() / name)
        if actual.returncode != 0 or actual.stderr or actual.stdout.decode().splitlines() != expected_native(unchecked):
            sys.exit(f"LAN-URI-PARTS FAIL {name}: {actual.stdout!r} {actual.stderr!r}")
    mutants = sum(unchecked for _name, unchecked in executables)
    print(f"LAN-URI-PARTS NATIVE OK observations={len(expected_native())} mutants={mutants}")


class UriParts(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="lanyard-uri-parts-")
        self.addCleanup(directory.cleanup)
        self.program = Path(directory.name) / "program.lan"

    def test_components(self):
        for part, column in [("path", 1), ("query", 2)]:
            self.program.write_text(BASE + f"def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => Response.text Bytes (Uri.{part} Bytes uri)\n")
            for row in CASES:
                with self.subTest(part=part, uri=row[0][:80]):
                    actual = run(DRIVER, "run", "--request", row[0], self.program)
                    self.assertEqual((actual.returncode, actual.stdout, actual.stderr), (0, response(row[column]), b""))

    def test_query_fields(self):
        for uri, body in [("/hello?name=Ada+Lovelace", "hello Ada Lovelace"),
                          ("/hello?name=caf%C3%A9", "hello café"),
                          ("/hello?name=a%26b%3Fc%2Bd", "hello a&b?c+d"),
                          ("/hello", "hello world"), ("/hello?", "hello world"),
                          ("/hello?name=", "hello "), ("/other?name=Ada", "/other")]:
            with self.subTest(uri=uri):
                actual = run(DRIVER, "run", "--request", uri, ROOT / "test/fixtures/uri-parts.lan")
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr), (0, response(body), b""))
        for query in ["other=x", "name=a&name=b", "name=%FF", "&".join(f"x{i}=v" for i in range(129))]:
            with self.subTest(query=query[:80]):
                actual = run(DRIVER, "run", "--request", "/hello?" + query, ROOT / "test/fixtures/uri-parts.lan")
                self.assertEqual((actual.returncode, actual.stdout), (1, b""))
                self.assertIn(b"form", actual.stderr)

    def test_invalid_request_boundary(self):
        for uri in INVALID + ["", "/ok?q=#fragment", "/bad path?q=ok", "/ok?q=bad path"]:
            with self.subTest(uri=uri[:80]):
                actual = run(DRIVER, "run", "--request", uri, ROOT / "test/fixtures/uri-parts.lan")
                self.assertEqual((actual.returncode, actual.stdout), (64, b""))
                self.assertIn(b"request URI", actual.stderr)

    def test_refusal_before_output(self):
        destination = self.program.parent / "crate"
        for part in ("path", "query"):
            for body in [f"def main : Uri -> Nat := Uri.{part} Nat", f"def main : Bytes := Uri.{part} Bytes 1"]:
                with self.subTest(body=body):
                    self.program.write_text(BASE + body)
                    actual = run(DRIVER, "emit", "--crate", destination, self.program)
                    self.assertEqual((actual.returncode, actual.stdout), (1, b""))
                    self.assertFalse(destination.exists())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
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
            print(f"LAN-URI-PARTS CLI OK groups={result.testsRun}")
        sys.exit(0 if result.wasSuccessful() else 1)
