"""Exercise listener CLI boundaries and real HTTP requests to emitted programs."""
import argparse
import concurrent.futures
import http.client
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "_build/default/bin/lanyard.exe"
ADDRESS = "127.0.0.1:0"
FORM = {"Content-Type": "application/x-www-form-urlencoded"}
BYTES = "mu Bytes : Type 0 :=\n| bytesNil : Bytes\n| bytesCons (head : Nat) (tail : Bytes) : Bytes\n"
REDIRECT = "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => topcoat.see_other uri\n"


def run(*args, timeout=60, **kwargs):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, capture_output=True,
                          timeout=timeout, **kwargs)


def require(result):
    if result.returncode != 0:
        sys.exit(f"LAN-HTTP FAIL exit={result.returncode}: {result.stdout!r} {result.stderr!r}")
    return result


def cases():
    return {
        "redirect": REDIRECT,
        "uri": (ROOT / "test/fixtures/uri-text.lan").read_text(),
        "todo": (ROOT / "test/fixtures/todo-session.lan").read_text(),
        "form": BYTES + "def main : Cx -> Uri -> Bytes -> Response := fun (cx : Cx) (uri : Uri) (body : Bytes) => Response.text Bytes (Form.field Bytes body b\"title\")\n",
        "ignored": BYTES + "def main : Cx -> Uri -> Bytes -> SeeOther := fun (cx : Cx) (uri : Uri) (body : Bytes) => topcoat.see_other uri\n",
    }


class Cli(unittest.TestCase):
    def test_addresses_before_source_io(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "out"
            for address in ["", "localhost:3000", "0.0.0.0:3000", "[::1]:3000", "127.0.0.1",
                            "127.0.0.1:-1", "127.0.0.1:+1", "127.0.0.1:65536",
                            "127.0.0.1:0x80", "127.0.0.1: 80", "127.0.0.1:80\n"]:
                for command, option in [("emit", "--crate"), ("build", "--out")]:
                    with self.subTest(address=address, command=command):
                        result = run(EXE, command, option, destination, "--listen", address, "missing.lan")
                        self.assertEqual(result.returncode, 64, result.stderr)
                        self.assertEqual(result.stdout, b"")
                        self.assertFalse(destination.exists())

    def test_conflicting_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            for options in [["--listen", ADDRESS, "--listen", ADDRESS],
                            ["--listen", ADDRESS, "--requests", "missing.requests"],
                            ["--requests", "missing.requests", "--listen", ADDRESS],
                            ["--listen", ADDRESS, "--print-model", "Todo"],
                            ["--print-model", "Todo", "--listen", ADDRESS],
                            ["--listen"], ["--listen", ADDRESS, "--steps", "10"]]:
                for command, option in [("emit", "--crate"), ("build", "--out")]:
                    result = run(EXE, command, option, Path(tmp) / "out", *options, "missing.lan")
                    self.assertEqual(result.returncode, 64, result.stderr)
                    self.assertFalse((Path(tmp) / "out").exists())

    def test_checked_entry_before_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.lan"
            for source in ["def main : Nat := 1\n",
                           "def main : Cx -> Uri -> Nat := fun (cx : Cx) (uri : Uri) => 1\n",
                           "def main : Cx -> Uri -> Nat -> SeeOther := fun (cx : Cx) (uri : Uri) (n : Nat) => topcoat.see_other uri\n"]:
                path.write_text(source)
                result = run(EXE, "emit", "--crate", Path(tmp) / "out", "--listen", ADDRESS, path)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stdout, b"")
                self.assertFalse((Path(tmp) / "out").exists())

    def test_build_flags_and_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = directory / "main.lan"
            source.write_text(REDIRECT)
            cargo = directory / "cargo"
            cargo.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\nexit 17\n')
            cargo.chmod(0o755)
            result = run(EXE, "build", "--listen", ADDRESS, "--out", directory / "out",
                         "--offline", "--release", source,
                         env={**os.environ, "PATH": str(directory) + os.pathsep + os.environ["PATH"]})
            self.assertEqual(result.returncode, 17, result.stderr)
            self.assertEqual(result.stdout, b"build\n--release\n--offline\n")
            self.assertIn(b"cargo_exit=17", result.stderr)
            generated = (directory / "out/src/main.rs").read_bytes()
            result = run(EXE, "emit", "--crate", directory / "out", "--listen", ADDRESS, source)
            self.assertEqual(result.returncode, 64, result.stderr)
            self.assertEqual((directory / "out/src/main.rs").read_bytes(), generated)


def prepare(args):
    destination = args.prepare.absolute()
    destination.mkdir(parents=True)
    bins = []
    for name, source in cases().items():
        path = destination / f"{name}.lan"
        path.write_text(source)
        require(run("python3", "-P", ROOT / "dev/prepare-crate.py", "--source", path,
                    "--listen", ADDRESS, "--output", destination / name,
                    "--toasty", args.toasty, "--topcoat", args.topcoat, "--lock", args.lock,
                    timeout=300))
        bins.append(f'\n[[bin]]\nname = "lan-http-{name}"\npath = "{name}/src/main.rs"\n')
    mutations = {
        "unchecked-form": ("ignored", "    lan_form_fields(form).map_err(|_error| LanHttpError::BadRequest)?;"),
        "unchecked-uri": ("redirect", "    lan_uri_validate(&uri.to_string()).map_err(|_error| LanHttpError::BadRequest)?;"),
    }
    for name, (original, check) in mutations.items():
        source = (destination / original / "src/main.rs").read_text()
        if source.count(check) != 1:
            sys.exit(f"LAN-HTTP FAIL mutation site differs: {name}")
        (destination / f"{name}.rs").write_text(source.replace(check, "    // Mutation control removes boundary validation."))
        bins.append(f'\n[[bin]]\nname = "lan-http-{name}"\npath = "{name}.rs"\n')
    (destination / "Cargo.toml").write_text((destination / "redirect/Cargo.toml").read_text() + "".join(bins))
    (destination / "Cargo.lock").write_bytes((destination / "redirect/Cargo.lock").read_bytes())
    print(f"LAN-HTTP PREPARED cases={len(cases())} mutants={len(mutations)}")


class Http(unittest.TestCase):
    binary_dir = None

    def start(self, name):
        process = subprocess.Popen([str(self.binary_dir / f"lan-http-{name}")],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(self.stop, process)
        readable, _writable, _errors = select.select([process.stderr], [], [], 15)
        self.assertTrue(readable, "server did not report readiness")
        line = process.stderr.readline()
        self.assertRegex(line, rb"^LANYARD-LISTEN http://127\.0\.0\.1:[0-9]+\n$")
        return int(line.rsplit(b":", 1)[1]), process

    def stop(self, process):
        if process.poll() is None:
            process.terminate()
        stdout, stderr = process.communicate(timeout=15)
        self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual(stdout, b"")

    def request(self, port, method, uri, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        connection.request(method, uri, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def test_uri_redirect_and_methods(self):
        port, _process = self.start("redirect")
        for uri in ["/", "/a/b?x=1?two", "/%C3%A9", "/%2F"]:
            status, headers, body = self.request(port, "GET", uri)
            self.assertEqual((status, headers.get("location"), body), (303, uri, b""))
        self.assertEqual(self.request(port, "DELETE", "/")[0], 405)
        self.assertEqual(self.request(port, "POST", "/", b"x=1", FORM)[0], 400)
        self.assertEqual(self.request(port, "GET", "/bad%Q0")[0], 400)
        status, headers, _body = self.request(port, "GET", "/bad#fragment")
        self.assertEqual((status, headers.get("location")), (303, "/bad"))
        port, _process = self.start("uri")
        for uri in ["/", "/a?x=1?two", "/%C3%A9"]:
            self.assertEqual(self.request(port, "GET", uri)[::2], (200, f"unmatched: {uri}".encode()))

    def test_todo_lifecycle_and_restart(self):
        port, _process = self.start("todo")
        script = (ROOT / "test/fixtures/todo-session.requests").read_text().splitlines()
        pages = [b"ready", "<ul><li>20: café</li></ul>".encode(),
                 "<ul><li>3: &lt;write&gt; &amp; test</li><li>20: café</li></ul>".encode(),
                 "<ul><li>3: updated (done)</li><li>20: café</li></ul>".encode()]
        pages += [b"<ul><li>3: updated (done)</li></ul>"] * 3
        for line, expected in zip(script, pages, strict=True):
            uri, form = line.split("\t")
            status, headers, body = self.request(port, "POST", uri, form, FORM)
            self.assertEqual((status, body), (200, expected))
            self.assertEqual(int(headers["content-length"]), len(expected))
        fresh, _process = self.start("todo")
        self.assertEqual(self.request(fresh, "GET", "/init")[0], 200)
        self.assertEqual(self.request(fresh, "GET", "/todos")[::2], (200, b"<ul></ul>"))

    def test_form_boundaries_and_recovery(self):
        port, _process = self.start("form")
        for body in [b"title=%GG", b"title=%FF", b"title=one&title=two", b"ti%74le=one&title=two",
                     b"=empty", b"missing", b"title=\xff"]:
            self.assertEqual(self.request(port, "POST", "/", body, FORM)[0], 400)
        self.assertEqual(self.request(port, "POST", "/", b"title=x", {})[0], 415)
        self.assertEqual(self.request(port, "GET", "/", b"title=x", FORM)[0], 400)
        self.assertEqual(self.request(port, "POST", "/", b"title=" + b"a" * 8192, FORM)[0], 413)
        self.assertEqual(self.request(port, "POST", "/", b"title=" + b"a" * 8186, FORM)[::2], (200, b"a" * 8186))
        fields = "title=ok&" + "&".join(f"k{n}=v" for n in range(127))
        self.assertEqual(self.request(port, "POST", "/", fields, FORM)[::2], (200, b"ok"))
        self.assertEqual(self.request(port, "POST", "/", fields + "&extra=v", FORM)[0], 400)
        self.assertEqual(self.request(port, "POST", "/", b"title=", FORM)[::2], (200, b""))
        self.assertEqual(self.request(port, "GET", "/")[0], 500)
        self.assertEqual(self.request(port, "POST", "/", b"title=caf%C3%A9", FORM)[::2], (200, "café".encode()))
        ignored, _process = self.start("ignored")
        self.assertEqual(self.request(ignored, "GET", "/")[0], 303)
        self.assertEqual(self.request(ignored, "POST", "/", b"bad=%XX", FORM)[0], 400)

    def test_body_timeout(self):
        port, _process = self.start("form")
        with socket.create_connection(("127.0.0.1", port), timeout=10) as client:
            client.sendall(b"POST / HTTP/1.1\r\nHost: localhost\r\nContent-Length: 5\r\n\r\nx")
            self.assertIn(b"408 Request Timeout", client.recv(4096))
        self.assertEqual(self.request(port, "POST", "/", b"title=ok", FORM)[::2], (200, b"ok"))

    def test_mutation_controls(self):
        form, _process = self.start("unchecked-form")
        self.assertEqual(self.request(form, "POST", "/", b"bad=%XX", FORM)[0], 303)
        uri, _process = self.start("unchecked-uri")
        self.assertEqual(self.request(uri, "GET", "/bad%Q0")[0], 303)

    def test_concurrent_handlers_and_panics(self):
        port, _process = self.start("todo")
        self.assertEqual(self.request(port, "GET", "/todos")[0], 500)
        self.assertEqual(self.request(port, "GET", "/init")[0], 200)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            replies = list(pool.map(lambda n: self.request(port, "POST", "/todos/create", f"id={n}&title=item", FORM), range(4)))
        self.assertEqual([reply[0] for reply in replies], [200] * 4)
        expected = "<ul>" + "".join(f"<li>{n}: item</li>" for n in range(4)) + "</ul>"
        self.assertEqual(self.request(port, "GET", "/todos")[::2], (200, expected.encode()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare", type=Path)
    mode.add_argument("--check", type=Path)
    parser.add_argument("--toasty", type=Path)
    parser.add_argument("--topcoat", type=Path)
    parser.add_argument("--lock", type=Path)
    args = parser.parse_args()
    if args.prepare is not None:
        prepare(args)
    else:
        Http.binary_dir = args.check
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Http if args.check else Cli)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            sys.exit(1)
        print(f"LAN-HTTP {'RUNTIME' if args.check else 'CLI'} OK groups={result.testsRun}")


if __name__ == "__main__":
    main()
