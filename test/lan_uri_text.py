"""Exercise request inspection through the driver and the pinned native URI type."""
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
def render : Uri -> Bytes := Uri.to_text Bytes
"""
PATHS = ["/", "/todos", "/todos?", "/todos?x=1&x=2", "/a??b", "/?",
         "/%00%0d%0A", "/%c3%a9", "/%C3%A9", "/a//b", "/a/../b",
         "/-._~!$&'()*+,;=:@/?", "/" + "a" * 8191]
INVALID = ["https://example.com/", "relative", "*", "//example.com/",
           "/%", "/%0", "/%GG", "/%0x", "/" + "a" * 8192]
NATIVE_SOURCE = BASE + """mu Other : Type 0 :=
| otherNil : Other
| otherCons (head : Nat) (tail : Other) : Other
def alternate : Uri -> Other := Uri.to_text Other
def roundtrip : Bytes -> Bytes := fun (text : Bytes) => render (Uri.from_text Bytes text)
def captured : Uri -> Bytes := fun (uri : Uri) =>
  let closure : Nat -> Bytes := fun (n : Nat) => Uri.to_text Bytes uri in closure 0
def unused : Uri -> Nat := fun (uri : Uri) => let ignored : Bytes := render uri in 1
def main : Bytes := roundtrip b"/todos?x=%2f"
"""


def run(*command):
    return subprocess.run([str(arg) for arg in command], cwd=ROOT,
                          capture_output=True, timeout=180)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-URI-TEXT FAIL: {result.stdout!r} {result.stderr!r}")
    return result.stdout.decode()


def response(body):
    return (f"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body.encode())}\r\n\r\n{body}").encode()


def harness():
    valid = ",\n".join(json.dumps(path) for path in PATHS)
    invalid = ",\n".join(json.dumps(path) for path in INVALID)
    return """
fn main() {
    let valid = [
""" + valid + """
    ];
    valid.iter().enumerate().for_each(|(index, path)| {
        let uri = path.parse::<topcoat::router::Uri>().map(Arc::new);
        let rendered = uri.as_ref().ok().and_then(|uri| f_72656e646572(uri.clone()).ok())
            .and_then(|text| lan_model_text_to_4279746573(&text).ok());
        let preserved = uri.as_ref().map(|uri| uri.to_string() == *path).unwrap_or(false);
        println!("RENDER {index} {}", rendered.as_deref() == Some(*path) && preserved);
        let roundtrip = f_726f756e6474726970(Arc::new(lan_model_text_from_4279746573(path.to_string())))
            .and_then(|text| lan_model_text_to_4279746573(&text));
        println!("ROUNDTRIP {index} {}", roundtrip.map(|text| text == *path).unwrap_or(false));
        let captured = uri.as_ref().ok().and_then(|uri| f_6361707475726564(uri.clone()).ok())
            .and_then(|text| lan_model_text_to_4279746573(&text).ok());
        println!("CAPTURED {index} {}", captured.as_deref() == Some(*path));
        let alternate = uri.as_ref().ok().and_then(|uri| f_616c7465726e617465(uri.clone()).ok())
            .and_then(|text| lan_model_text_to_4f74686572(&text).ok());
        println!("ALTERNATE {index} {}", alternate.as_deref() == Some(*path));
    });
    let invalid = [
""" + invalid + """
    ];
    invalid.iter().enumerate().for_each(|(index, path)| {
        let uri = path.parse::<topcoat::router::Uri>().map(Arc::new);
        let rejected = uri.as_ref().map(|uri| matches!(f_72656e646572(uri.clone()), Err(Error::InvalidUri)))
            .unwrap_or(false);
        println!("REJECT {index} {rejected}");
        let retained = uri.as_ref().map(|uri| matches!(f_756e75736564(uri.clone()), Err(Error::InvalidUri)))
            .unwrap_or(false);
        println!("UNUSED {index} {retained}");
    });
}
"""


def expected_native():
    return ([f"{kind} {index} true" for index in range(len(PATHS))
             for kind in ("RENDER", "ROUNDTRIP", "CAPTURED", "ALTERNATE")]
            + [f"{kind} {index} true" for index in range(len(INVALID)) for kind in ("REJECT", "UNUSED")])


def prepare(args):
    destination = args.prepare.absolute()
    program = destination.with_suffix(".lan")
    if destination.exists() or program.exists():
        sys.exit("LAN-URI-TEXT FAIL: output and sibling source must be fresh")
    destination.parent.mkdir(parents=True, exist_ok=True)
    program.write_text(NATIVE_SOURCE)
    require(run(sys.executable, "-P", ROOT / "dev/prepare-crate.py", "--source", program,
                "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock,
                "--output", destination))
    (destination / "src/main.rs").write_text(require(run(DRIVER, "emit", "--target", program)) + harness())
    (destination / "expected.json").write_text(json.dumps(expected_native(), indent=2) + "\n")
    print(f"LAN-URI-TEXT PREPARED manifest={destination / 'Cargo.toml'}")


class UriText(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="lanyard-uri-text-")
        self.addCleanup(directory.cleanup)
        self.program = Path(directory.name) / "program.lan"

    def test_request_routing(self):
        for path in PATHS:
            with self.subTest(path=path[:80]):
                actual = run(DRIVER, "run", "--request", path, ROOT / "test/fixtures/uri-text.lan")
                expected = "todos" if path == "/todos" else "unmatched: " + path
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr), (0, response(expected), b""))

    def test_roundtrip_and_reuse(self):
        for path in PATHS[:-1]:
            with self.subTest(path=path):
                self.program.write_text(BASE + "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => "
                                        f"let parsed : Uri := Uri.from_text Bytes b{json.dumps(path)} in "
                                        "Response.text Bytes (Text.concat Bytes (render parsed) (render parsed))\n")
                actual = run(DRIVER, "run", "--request", "/", self.program)
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr), (0, response(path + path), b""))

    def test_invalid_request_boundary(self):
        for path in INVALID + ["", "/\r\nLocation: /other", "/#fragment"]:
            with self.subTest(path=path[:80]):
                actual = run(DRIVER, "run", "--request", path, ROOT / "test/fixtures/uri-text.lan")
                self.assertEqual((actual.returncode, actual.stdout), (64, b""))
                self.assertIn(b"request URI", actual.stderr)

    def test_refusal_before_output(self):
        destination = self.program.parent / "crate"
        for body in ["def main : Uri -> Nat := Uri.to_text Nat",
                     "def main : Bytes := Uri.to_text Bytes 1"]:
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
            actual = run(args.check.absolute())
            if actual.returncode != 0 or actual.stderr or actual.stdout.decode().splitlines() != expected_native():
                sys.exit(f"LAN-URI-TEXT FAIL native: {actual.stdout!r} {actual.stderr!r}")
            print(f"LAN-URI-TEXT OK native observations={len(expected_native())}")
    else:
        unittest.main(argv=[sys.argv[0], *remaining])
