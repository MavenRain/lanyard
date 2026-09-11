"""Prepare the offline pinned-API probe without building or accessing a database."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        print(f"FOREIGN-TYPES-PREPARE FAIL: {message}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toasty", type=Path, required=True)
    parser.add_argument("--topcoat", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args()
    pins = json.loads((ROOT / "target/PIN.json").read_text())["libraries"]
    paths = {"toasty": args.toasty.resolve(), "topcoat": args.topcoat.resolve()}
    for name, path in paths.items():
        head = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                              text=True, capture_output=True, timeout=30)
        require(head.returncode == 0 and head.stdout.strip() == pins[name]["commit"], f"{name} pin differs")
        status = subprocess.run(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=no"],
                                text=True, capture_output=True, timeout=30)
        require(status.returncode == 0 and not status.stdout, f"{name} tracked sources are dirty")
    destination = ROOT / ".gatework/foreign-types-pinned"
    source = destination / "src"
    source.mkdir(parents=True, exist_ok=True)
    cargo = ['[package]', 'name = "lanyard-foreign-validation"', 'version = "0.0.0"',
             'edition = "2024"', 'license = "MIT OR Apache-2.0"', '', '[dependencies]']
    for name, path in paths.items():
        crate = json.dumps(str(path / "crates" / name))
        features = ', features = ["router"]' if name == "topcoat" else ""
        cargo.append(f'{name} = {{ path = {crate}, default-features = false{features} }}')
    (destination / "Cargo.toml").write_text("\n".join(cargo) + "\n")
    shutil.copyfile(args.lock, destination / "Cargo.lock")
    shutil.copyfile(ROOT / "test/goldens/foreign-types.rs", source / "golden.rs")
    shutil.copyfile(ROOT / "test/foreign-types-pinned.rs", source / "main.rs")
    print(f"FOREIGN-TYPES-PREPARE OK manifest={destination / 'Cargo.toml'}")


if __name__ == "__main__":
    main()
