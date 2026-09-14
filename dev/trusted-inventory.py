"""Inventory compiler sources and enforce an explicitly approved trust policy."""
import argparse
import functools
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import sys

ROOT = Path(__file__).resolve().parent.parent
FORMULA = "5481 + A_rir + A_emit + A_sig"
GENERATED = "_build/default/target/target_generated.ml"
GROUPS = {
    "kernel": tuple("lib/" + name + ".ml" for name in (
        "shape", "term", "rules", "check", "value", "eval", "conv", "totality",
        "positivity", "global", "order", "bignum")),
    "erase": ("lib/erase.ml",),
    "rir": ("lib/rir.ml",),
    "printer": tuple("rust/" + name + ".ml" for name in (
        "emit", "effects", "foreign", "connection", "template", "model", "crate", "reachable")),
    "signatures": (GENERATED,),
    "carried-eraser": ("lib/erase_kan.ml", "lib/eterm.ml"),
    "target-bridge": ("surface/lower.ml", "surface/specialize.ml", "surface/fuse.ml"),
    "kernel-support": tuple("lib/" + name for name in (
        "budget.ml", "budget.mli", "error.ml", "level.ml", "level.mli", "literal.ml",
        "pp.ml", "prim.ml", "quantity.ml", "spec_count.ml")),
    "frontend": tuple("surface/" + name + ".ml" for name in (
        "axioms", "elab", "lexer", "parser", "syntax", "term_scope", "token")),
    "driver": ("bin/lanyard.ml",),
}
ALLOWANCES = {"rir": "A_rir", "printer": "A_emit", "signatures": "A_sig"}
SOURCE_SUFFIXES = {".ml", ".mli", ".mll", ".mly"}
POLICY_MODULE = "dev/trusted-policy.py"


def regular_bytes(root, name):
    """Reject links, including linked parent directories, and special files."""
    relative = Path(name)
    for part in (relative, *relative.parents):
        path = root / part
        if path.is_symlink():
            raise ValueError(f"{part}: symlink in an inventory path")
    path = root / relative
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f"{name}: expected a regular file")
    return path.read_bytes()


@functools.cache
def load_policy():
    """Load the policy code on demand, so a missing, linked or special module
    becomes a TRUSTED-INVENTORY FAIL row. An import-time load made the same
    fault a raw traceback in this script and in every consumer of it. The
    module comes from THIS script's root, never from the measured root."""
    # regular_bytes rejects a link or a special file and reports the reason.
    regular_bytes(ROOT, POLICY_MODULE)
    spec = importlib.util.spec_from_file_location("trusted_policy", ROOT / POLICY_MODULE)
    if spec is None or spec.loader is None:
        raise ValueError(f"{POLICY_MODULE}: expected a loadable policy module")
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    return policy


def reraise(error):
    """Fail the census on an unreadable directory instead of skipping it."""
    raise error


def sources(root):
    """Include new compiler sources as candidates; never infer their trust scope."""
    found = set()
    for directory in ("lib", "surface", "rust", "bin", "target"):
        base = root / directory
        if base.is_symlink() or not base.is_dir():
            raise ValueError(f"{directory}: expected a compiler source directory")
        # A walk reports a directory it cannot read. rglob dropped it in
        # silence, which hid the sources below it from the census.
        for parent, directories, names in base.walk(on_error=reraise, follow_symlinks=False):
            for path in sorted(parent / name for name in (*directories, *names)):
                if path.is_symlink():
                    raise ValueError(f"{path.relative_to(root)}: symlink in compiler sources")
                if path.suffix in SOURCE_SUFFIXES:
                    found.add(path.relative_to(root).as_posix())
    return found | {GENERATED}


def inventory(root):
    declared = {name: group for group, names in GROUPS.items() for name in names}
    script = regular_bytes(root, "dev/trusted-lines.sh").decode()
    bucket = re.findall(r"^\s*\$root/(lib/[a-z_]+\.ml)\s*$", script, re.MULTILINE)
    if sorted(bucket) != sorted(GROUPS["kernel"]):
        raise ValueError("the shell kernel bucket differs from the twelve-file inventory")
    found = sources(root)
    missing = sorted(declared.keys() - found)
    if missing:
        raise ValueError("required compiler sources missing: " + ", ".join(missing))
    files = []
    for name in sorted(found):
        data = regular_bytes(root, name)
        files.append({"path": name, "group": declared.get(name, "unassigned"),
                      "lines": data.count(b"\n"), "bytes": len(data),
                      "sha256": hashlib.sha256(data).hexdigest()})
    groups = []
    for name in (*GROUPS, "unassigned"):
        members = [row for row in files if row["group"] == name]
        scope = "kernel" if name == "kernel" else "base" if name == "erase" else "pending"
        groups.append({"name": name, "scope": scope, "allowance": ALLOWANCES.get(name),
                       "lines": sum(row["lines"] for row in members),
                       "files": [row["path"] for row in members]})
    kernel = next(row["lines"] for row in groups if row["name"] == "kernel")
    passed = kernel <= 4000
    report = {"format": 1, "status": "PENDING" if passed else "FAIL",
              "counting": "newline bytes (wc -l), including comments and blank lines",
              "kernel": {"lines": kernel, "limit": 4000, "passed": passed},
              "ceiling": {"base": 5481, "formula": FORMULA, "total": None,
                          "A_rir": None, "A_emit": None, "A_sig": None},
              "groups": groups, "files": files,
              "pending_rulings": ["A_rir", "A_emit", "A_sig", "base growth",
                                  "trusted-file scope"], "m0_exit": "not-stamped"}
    policy = load_policy()
    return policy.apply(report, regular_bytes(root, policy.PATH))


def encoded(report):
    return (json.dumps(report, indent=2) + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, help="new JSON file for the inventory")
    args = parser.parse_args()
    try:
        report = inventory(args.root.resolve())
        data = encoded(report)
        if args.output is not None:
            with args.output.open("xb") as stream:
                stream.write(data)
        print(f"TRUSTED-INVENTORY files={len(report['files'])} sha256={hashlib.sha256(data).hexdigest()}")
        policy = report["policy"]
        candidate = "PASS" if policy["passed"] else "FAIL"
        print(f"TRUSTED-POLICY {policy['status']} candidate={candidate} "
              f"lines={policy['lines']}/{policy['limit']} sha256={policy['sha256']}")
        if policy["status"] == "APPROVED":
            for check in policy["checks"]:
                if not check["passed"]:
                    print(f"TRUSTED-POLICY group={check['name']} lines={check['lines']}/{check['limit']} "
                          f"paths_match={str(check['paths_match']).lower()}")
        if not report["kernel"]["passed"]:
            print(f"TRUSTED-INVENTORY kernel={report['kernel']['lines']}/4000")
        print(f"TRUSTED-INVENTORY {report['status']}")
        return 1 if report["status"] == "FAIL" else 0
    except (OSError, ValueError) as error:
        print(f"TRUSTED-INVENTORY FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
