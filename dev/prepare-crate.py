"""Prepare an emitted crate against clean local checkouts of both target pins."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        sys.exit(f"CRATE-PREPARE FAIL: {message}")


def run(*args):
    command = [str(arg) for arg in args]
    try:
        return subprocess.run(command, cwd=ROOT, text=True,
                              capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        require(False, f"command timed out: {' '.join(command)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toasty", type=Path, required=True)
    parser.add_argument("--topcoat", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=ROOT / "test/fixtures/crate.lan")
    parser.add_argument("--lock", type=Path, help="seed Cargo's offline resolution from a validation lock")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(args.lock is None or args.lock.is_file(), f"lock file is missing: {args.lock}")
    lock = args.lock.read_bytes() if args.lock is not None else None
    pins = json.loads((ROOT / "target/PIN.json").read_text())["libraries"]
    libraries = {"toasty": args.toasty.resolve(), "topcoat": args.topcoat.resolve()}
    for name, path in libraries.items():
        require(name in pins and "commit" in pins[name], f"target/PIN.json has no {name} commit")
        head = run("git", "-C", path, "rev-parse", "HEAD")
        status = run("git", "-C", path, "status", "--porcelain", "--untracked-files=no")
        require(head.returncode == 0 and head.stdout.strip() == pins[name]["commit"], f"{name} pin differs")
        require(status.returncode == 0 and not status.stdout, f"{name} tracked sources are dirty")
    destination = args.output.absolute()
    emitted = run(ROOT / "_build/default/bin/lanyard.exe", "emit", "--crate", destination, args.source.absolute())
    require(emitted.returncode == 0 and not emitted.stdout, emitted.stderr)
    manifest = destination / "Cargo.toml"
    original = manifest.read_text()
    dependencies = tomllib.loads(original)["dependencies"]
    replacement = original
    for name, path in libraries.items():
        require(name in dependencies, f"emitted manifest has no {name} dependency")
        dependency = dependencies[name]
        require("git" in dependency and "rev" in dependency,
                f"emitted {name} dependency is not a git pin")
        require(dependency["rev"] == pins[name]["commit"], f"emitted {name} pin differs")
        before = f'git = {json.dumps(dependency["git"])}, rev = {json.dumps(dependency["rev"])}'
        require(replacement.count(before) == 1, f"{name} dependency layout differs")
        replacement = replacement.replace(before, f'path = {json.dumps(str(path / "crates" / name), ensure_ascii=False)}')
    (destination / "Cargo.git.toml").write_text(original)
    manifest.write_text(replacement)
    if lock is not None:
        (destination / "Cargo.lock").write_bytes(lock)
    print(f"CRATE-PREPARE OK manifest={manifest}")


if __name__ == "__main__":
    main()
