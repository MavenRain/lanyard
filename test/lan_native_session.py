"""Check native script crates against independent transcripts and the interpreter."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "_build/default/bin/lanyard.exe"
BYTES = """mu Bytes : Type 0 :=
| bytesNil : Bytes
| bytesCons (head : Nat) (tail : Bytes) : Bytes
"""
REDIRECT = "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => topcoat.see_other uri\n"


def run(*args, timeout=120, **kwargs):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, capture_output=True,
                          timeout=timeout, **kwargs)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-NATIVE-SESSION FAIL exit={result.returncode}: {result.stdout!r} {result.stderr!r}")
    return result


def response(body, kind="plain"):
    data = body.encode()
    return (f"HTTP/1.1 200 OK\r\nContent-Type: text/{kind}; charset=utf-8\r\n"
            f"Content-Length: {len(data)}\r\n\r\n").encode() + data


def redirect(uri):
    return f"HTTP/1.1 303 See Other\r\nLocation: {uri}\r\nContent-Length: 0\r\n\r\n".encode()


def cases():
    todo = (ROOT / "test/fixtures/todo-session.lan").read_text()
    pages = ["<ul><li>20: café</li></ul>",
             "<ul><li>3: &lt;write&gt; &amp; test</li><li>20: café</li></ul>",
             "<ul><li>3: updated (done)</li><li>20: café</li></ul>"]
    pages += ["<ul><li>3: updated (done)</li></ul>"] * 3
    return {
        "todo": (todo, (ROOT / "test/fixtures/todo-session.requests").read_text(),
                 response("ready") + b"".join(response(page, "html") for page in pages), None),
        "redirect": (REDIRECT, "/first\n/last?x=%2f\n",
                     redirect("/first") + redirect("/last?x=%2f"), None),
        "uri": (BYTES + "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => Response.text Bytes (Uri.to_text Bytes uri)\n",
                "/a??b\n/%c3%a9\n", response("/a??b") + response("/%c3%a9"), None),
        "form": (BYTES + 'def main : Cx -> Uri -> Bytes -> Response := fun (cx : Cx) (uri : Uri) (body : Bytes) => Response.text Bytes (Form.field Bytes body b"value")\n',
                 '/\tvalue=café"\\\n/\tvalue=%0A%00%F0%9F%8D%B5\n',
                 response('café"\\') + response("\n\0🍵"), None),
        "unused_form": (BYTES + 'def main : Cx -> Uri -> Bytes -> SeeOther := fun (cx : Cx) (uri : Uri) (body : Bytes) => topcoat.see_other uri\n',
                        "/first\t\n/last\tunused=1\n", redirect("/first") + redirect("/last"), None),
        "many": (REDIRECT, "".join(f"/r{i}\n" for i in range(128)),
                 b"".join(redirect(f"/r{i}") for i in range(128)), None),
        "late_failure": (todo, "/init\t\n/todos/create\tid=1&title=one\n/todos/update\tid=2&title=missing\n",
                         b"", "request 3:"),
        "no_schema": (todo, "/todos\t\n", b"", "request 1:"),
    }


def materialize(directory, name, source, script):
    path = directory / f"{name}.lan"
    requests = directory / f"{name}.requests"
    path.write_text(source)
    requests.write_text(script)
    return path, requests


class NativeSession(unittest.TestCase):
    def test_emission_is_deterministic_and_preserves_dependency_pins(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            path, requests = materialize(directory, "main", REDIRECT, "/first\n/last\n")
            for name in ("one", "two"):
                result = require(run(EXE, "emit", "--crate", directory / name, "--requests", requests, path))
                self.assertEqual(result.stdout, b"")
                self.assertEqual(result.stderr, b"")
            for file in ("Cargo.toml", "src/main.rs"):
                self.assertEqual((directory / "one" / file).read_bytes(), (directory / "two" / file).read_bytes())
            pins = json.loads((ROOT / "target/PIN.json").read_text())["libraries"]
            manifest = (directory / "one/Cargo.toml").read_text()
            for library in pins.values():
                self.assertIn(library["commit"], manifest)

    def test_invalid_scripts_are_usage_errors_before_source_io(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            script = directory / "bad.requests"
            for text in ("", "//host\n", "/\tx=%GG\n", "/\t\textra\n", "/\n" * 129):
                script.write_text(text)
                for command in (("emit", "--crate"), ("build", "--out")):
                    result = run(EXE, *command, directory / "out", "--requests", script, directory / "missing.lan")
                    self.assertEqual(result.returncode, 64, result.stderr)
                    self.assertIn(b"request script", result.stderr)
                    self.assertEqual(result.stdout, b"")
                    self.assertFalse((directory / "out").exists())

    def test_bad_entry_points_and_body_modes_leave_no_crate(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for source, script, fragment in (("def main : Nat := 1", "/\n", b"request 1: "),
                                             (REDIRECT, "/\n/\tx=1\n", b"request 2: "),
                                             (cases()["form"][0], "/\n", b"request 1: ")):
                path, requests = materialize(directory, "bad", source, script)
                result = run(EXE, "emit", "--crate", directory / "out", "--requests", requests, path)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(fragment, result.stderr)
                self.assertIn(b"entry point must have type", result.stderr)
                self.assertEqual(result.stdout, b"")
                self.assertFalse((directory / "out").exists())
                self.assertFalse((directory / "out.partial").exists())

    def test_option_conflicts_fail_before_source_io(self):
        for flags in (("--requests", "a", "--requests", "b"),
                      ("--requests", "a", "--print-model", "Todo"),
                      ("--print-model", "Todo", "--requests", "a"),
                      ("--requests",), ("--requests", "a", "--steps", "1")):
            for command in (("build", "--out"), ("emit", "--crate")):
                result = run(EXE, *command, "/unused", *flags, "missing.lan")
                self.assertEqual(result.returncode, 64, result.stderr)
                self.assertIn(b"usage:", result.stderr)
                self.assertEqual(result.stdout, b"")

    def test_build_emits_before_invoking_cargo_with_existing_flags(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            path, requests = materialize(directory, "main", REDIRECT, "/first\n")
            cargo = directory / "cargo"
            cargo.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\nexit 17\n')
            cargo.chmod(0o755)
            result = run(EXE, "build", "--requests", requests, "--out", directory / "out",
                         "--release", "--offline", path,
                         env={**os.environ, "PATH": str(directory) + os.pathsep + os.environ["PATH"]})
            self.assertEqual(result.returncode, 17, result.stderr)
            self.assertEqual(result.stdout, b"build\n--release\n--offline\n")
            self.assertIn(b"cargo_exit=17", result.stderr)
            self.assertTrue((directory / "out/src/main.rs").is_file())


def prepare(args):
    destination = args.prepare.absolute()
    destination.mkdir(parents=True)
    bins = []
    for name, (source, script, expected, error) in cases().items():
        path, requests = materialize(destination, name, source, script)
        interpreted = run(EXE, "run", "--requests", requests, path)
        if interpreted.stdout != expected or interpreted.returncode != (1 if error else 0):
            sys.exit(f"LAN-NATIVE-SESSION FAIL {name}: interpreter disagrees with expected transcript: {interpreted}")
        command = ["python3", "-P", ROOT / "dev/prepare-crate.py", "--source", path,
                   "--requests", requests, "--output", destination / name,
                   "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock]
        require(run(*command, timeout=900))
        bins.append(f'\n[[bin]]\nname = "lan-session-{name}"\npath = "{name}/src/main.rs"\n')
    mutations = {
        "order": ("redirect", "[response_0, response_1].concat()", "[response_1, response_0].concat()"),
        "partial": ("late_failure", "    let response_1 =", "    std::io::Write::write_all(&mut std::io::stdout().lock(), response_0.as_bytes()).map_err(LanSessionError::Output)?;\n    let response_1 ="),
    }
    for name, (original, before, after) in mutations.items():
        source = (destination / original / "src/main.rs").read_text()
        if source.count(before) != 1:
            sys.exit(f"LAN-NATIVE-SESSION FAIL mutation {name} has no unique target")
        path = f"mutant-{name}.rs"
        (destination / path).write_text(source.replace(before, after))
        bins.append(f'\n[[bin]]\nname = "lan-session-mutant-{name}"\npath = "{path}"\n')
    manifest = (destination / "todo/Cargo.toml").read_text()
    (destination / "Cargo.toml").write_text(manifest + "".join(bins))
    (destination / "Cargo.lock").write_bytes(args.lock.read_bytes())
    print(f"LAN-NATIVE-SESSION PREPARED cases={len(cases())} mutants={len(mutations)} manifest={destination / 'Cargo.toml'}")


def check(directory):
    for name, (_source, _script, expected, error) in cases().items():
        for repeat in range(2):
            result = run(directory / f"lan-session-{name}")
            if result.stdout != expected or result.returncode != (1 if error else 0):
                sys.exit(f"LAN-NATIVE-SESSION FAIL {name} repeat={repeat}: {result}")
            if error and error.encode() not in result.stderr:
                sys.exit(f"LAN-NATIVE-SESSION FAIL {name}: missing indexed error: {result.stderr!r}")
            if error is None and result.stderr:
                sys.exit(f"LAN-NATIVE-SESSION FAIL {name}: unexpected stderr: {result.stderr!r}")
    reversed_output = redirect("/last?x=%2f") + redirect("/first")
    reversed_result = require(run(directory / "lan-session-mutant-order"))
    if reversed_result.stdout != reversed_output or reversed_result.stderr:
        sys.exit("LAN-NATIVE-SESSION FAIL order mutant did not produce the expected wrong ordering")
    partial = run(directory / "lan-session-mutant-partial")
    if partial.returncode != 1 or partial.stdout != response("ready") or b"request 3:" not in partial.stderr:
        sys.exit("LAN-NATIVE-SESSION FAIL partial mutant did not expose the expected partial transcript")
    print(f"LAN-NATIVE-SESSION OK cases={len(cases())} executions={2 * len(cases())} mutants=2")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--prepare", type=Path)
    modes.add_argument("--check", type=Path)
    parser.add_argument("--toasty", type=Path)
    parser.add_argument("--topcoat", type=Path)
    parser.add_argument("--lock", type=Path)
    args = parser.parse_args()
    if args.prepare:
        if not all((args.toasty, args.topcoat, args.lock)):
            parser.error("--prepare requires --toasty, --topcoat and --lock")
        prepare(args)
    elif args.check:
        check(args.check.absolute())
    else:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeSession)
        result = unittest.TextTestRunner().run(suite)
        if not result.wasSuccessful():
            sys.exit(1)
        print(f"LAN-NATIVE-SESSION-CLI OK groups={result.testsRun}")
