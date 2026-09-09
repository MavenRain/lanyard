#!/usr/bin/env python3
"""Read-only PIN, ANCHOR and DIFF checks for the two target libraries."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tomllib


LIBRARIES = {
    "toasty": "toasty-7bd502cb.sig",
    "topcoat": "topcoat-51caa01.sig",
}
# S3's exact spans, including href's final newline. Never inferred from line counts.
ANCHORS = (
    ("crates/topcoat-view/macro/src/lib.rs", 27, 34),
    ("crates/topcoat-view/grammar/src/component/attr.rs", 6, 15),
    ("crates/topcoat-view/grammar/src/component/item.rs", 21, 64),
    ("crates/topcoat-router/src/href.rs", 1, None),
)


class PinError(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PinError(f"duplicate pin key: {key}")
        result[key] = value
    return result


def git(root, *args):
    result = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(root), *args],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, timeout=15,
    )
    if result.returncode != 0:
        raise PinError(f"{root.name}: git {' '.join(args)}: {result.stderr.decode().strip()}")
    return result.stdout.decode().strip()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(root):
    rows = []
    for path, first, last in ANCHORS:
        lines = (root / path).read_bytes().splitlines(keepends=True)
        if len(lines) < (last or first):
            raise PinError(f"anchor truncated: {path}:{first}-{last}")
        fragment = b"".join(lines[first - 1:last])
        span = f"{first}-{last}" if last is not None else "whole"
        rows.append(f"{sha(fragment)}  topcoat/{path}:{span}\n")
    return "".join(rows)


def package_version(root, library):
    path = root / "crates" / library / "Cargo.toml"
    package = tomllib.loads(path.read_text())["package"]
    if package["name"] != library:
        raise PinError(f"{library}: crate manifest has a different package name")
    version = package["version"]
    if version == {"workspace": True}:
        version = tomllib.loads((root / "Cargo.toml").read_text())["workspace"]["package"]["version"]
    if not isinstance(version, str):
        raise PinError(f"{library}: expected a literal crate version")
    return version


def read_manifest(target):
    manifest = json.loads((target / "PIN.json").read_text(), object_pairs_hook=unique_object)
    if set(manifest) != {"format", "libraries"} or manifest["format"] != 1:
        raise PinError("unsupported PIN.json format")
    if not isinstance(manifest["libraries"], dict) or set(manifest["libraries"]) != set(LIBRARIES):
        raise PinError("PIN.json must contain toasty and topcoat exactly once")
    fields = {"commit", "crate_version", "release_tag", "release_commit", "signature_sha256"}
    for library, pin in manifest["libraries"].items():
        if not isinstance(pin, dict) or set(pin) != fields or any(not isinstance(v, str) or not v for v in pin.values()):
            raise PinError(f"{library}: invalid pin fields")
    return manifest["libraries"]


def read_identity(text):
    supplied = json.loads(text, object_pairs_hook=unique_object)
    fields = {"commit", "release_tag", "release_commit"}
    if not isinstance(supplied, dict) or set(supplied) - set(LIBRARIES):
        raise PinError("--identity names a library outside the pin")
    for library, values in supplied.items():
        if not isinstance(values, dict) or not set(values) <= fields or any(
            not isinstance(value, str) or not value for value in values.values()
        ):
            raise PinError(f"{library}: invalid identity override")
    return supplied


def check_pin(roots, pins, identity):
    for library, root in roots.items():
        pin = pins[library]
        # A supplied value replaces one read of the upstream object database.
        supplied = identity.get(library, {})
        tag = supplied.get("release_tag", pin["release_tag"])
        observations = {
            "commit": supplied.get("commit") or git(root, "rev-parse", "--verify", "HEAD^{commit}"),
            "crate_version": package_version(root, library),
            "release_commit": supplied.get("release_commit")
            or git(root, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"),
        }
        # Without an override the tag names the ref that the release_commit lookup
        # reads, so it has no source of its own.  A supplied tag was read upstream.
        if "release_tag" in supplied:
            observations["release_tag"] = supplied["release_tag"]
        for field, observed in observations.items():
            if observed != pin[field]:
                raise PinError(f"{library} {field}: expected {pin[field]}, observed {observed}")


def check_diff(target, pins, actual):
    expected = (target / "pin.sha256").read_text()
    if actual != expected:
        raise PinError("anchor fingerprint differs from target/pin.sha256")
    for library, filename in LIBRARIES.items():
        if sha((target / filename).read_bytes()) != pins[library]["signature_sha256"]:
            raise PinError(f"{filename}: signature changed without a reviewed pin update")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=Path(__file__).resolve().parent.parent / "target")
    parser.add_argument("--toasty", type=Path, default=Path("/Users/oobi/Documents/toasty"))
    parser.add_argument("--topcoat", type=Path, default=Path("/Users/oobi/Documents/topcoat"))
    parser.add_argument("--identity", default="{}",
                        help="JSON map of library to observed commit, release_tag and "
                             "release_commit, for a copy without an object database")
    args = parser.parse_args()
    leg = "PIN"
    try:
        pins = read_manifest(args.target)
        check_pin({"toasty": args.toasty, "topcoat": args.topcoat}, pins, read_identity(args.identity))
        print("TARGET-PIN PIN OK libraries=2")
        leg = "ANCHOR"
        actual = fingerprint(args.topcoat)
        print("TARGET-PIN ANCHOR OK sites=4")
        leg = "DIFF"
        check_diff(args.target, pins, actual)
        print("TARGET-PIN DIFF OK signatures=2 anchors=4")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(f"TARGET-PIN {leg} FAIL: {error}", file=sys.stderr)
        return 1
    print("TARGET-PIN OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
