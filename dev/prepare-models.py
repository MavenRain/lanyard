"""Prepare a pinned Toasty model probe for an offline build and local SQLite run."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        print(f"MODELS-PREPARE FAIL: {message}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toasty", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args()
    toasty = args.toasty.resolve()
    pin = json.loads((ROOT / "target/PIN.json").read_text())["libraries"]["toasty"]["commit"]
    head = subprocess.run(["git", "-C", str(toasty), "rev-parse", "HEAD"],
                          text=True, capture_output=True, timeout=30)
    require(head.returncode == 0 and head.stdout.strip() == pin, "Toasty pin differs")
    status = subprocess.run(["git", "-C", str(toasty), "status", "--porcelain", "--untracked-files=no"],
                            text=True, capture_output=True, timeout=30)
    require(status.returncode == 0 and not status.stdout, "Toasty tracked sources are dirty")
    destination = ROOT / ".gatework/models-pinned"
    source = destination / "src"
    source.mkdir(parents=True, exist_ok=True)
    cargo = ['[package]', 'name = "lanyard-model-validation"', 'version = "0.0.0"',
             'edition = "2024"', 'license = "MIT OR Apache-2.0"', '', '[dependencies]',
             f'toasty = {{ path = {json.dumps(str(toasty / "crates/toasty"))}, default-features = false, features = ["sqlite"] }}',
             'tokio = { version = "1", features = ["rt", "macros"] }']
    (destination / "Cargo.toml").write_text("\n".join(cargo) + "\n")
    shutil.copyfile(args.lock, destination / "Cargo.lock")
    shutil.copyfile(ROOT / "test/goldens/models.rs", source / "golden.rs")
    shutil.copyfile(ROOT / "test/models-pinned.rs", source / "main.rs")
    shutil.copyfile(ROOT / "test/models-text-oracle.rs", source / "text-oracle.rs")
    print(f"MODELS-PREPARE OK manifest={destination / 'Cargo.toml'}")


if __name__ == "__main__":
    main()
