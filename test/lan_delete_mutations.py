"""Require named behavioral failures from isolated deletion mutations."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
UNIT = ["_build/default/test/lan_delete.exe"]
MUTATIONS = [
    ("no-delete", "rust/run_store.ml", "Ok (Unit, replace { db with rows } store)",
     "let _rows = rows in Ok (Unit, store)", "deleted row absent:"),
    ("all-keys", "rust/run_store.ml", "Bignum.equal stored_key key",
     "Bignum.equal stored_key stored_key", "other key preserved:"),
    ("all-models", "rust/run_store.ml", "String.equal name model.name && Bignum.equal stored_key key",
     "String.equal name name && Bignum.equal stored_key key", "other model preserved:"),
    ("erased-delete", "rust/model.ml", "| Delete -> Ok call", '| Delete -> Ok "()"',
     "checked unit result:"),
]


def run(root, command, timeout=120):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=timeout)


def build(root):
    result = run(root, ["zsh", "dev/dunecho.sh", "build"], timeout=None)
    if result.returncode != 0:
        sys.exit(f"LAN-DELETE-MUTATIONS build failed: {result.stdout}{result.stderr}")


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="delete-mutations-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        build(scratch)
        result = run(scratch, UNIT)
        if result.returncode != 0:
            sys.exit(f"LAN-DELETE-MUTATIONS clean control failed: {result.stdout}{result.stderr}")
        print("LAN-DELETE-MUTATIONS CONTROL OK", flush=True)
        killed = 0
        survivors = []
        for name, relative, before, after, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-DELETE-MUTATIONS {name}: expected exactly one source site")
            path.write_text(original.replace(before, after))
            build(scratch)
            result = run(scratch, UNIT)
            path.write_text(original)
            if result.returncode != 1 or failure not in result.stderr:
                survivors.append(f"LAN-DELETE-MUTATIONS {name} survived: {result.stdout}{result.stderr}")
                break
            killed += 1
            print(f"LAN-DELETE-MUTATIONS {name} KILLED", flush=True)
        build(scratch)
        result = run(scratch, UNIT)
        if result.returncode != 0:
            sys.exit(f"LAN-DELETE-MUTATIONS restored control failed: {result.stdout}{result.stderr}")
        if survivors:
            print("\n".join(survivors), flush=True)
            sys.exit(f"LAN-DELETE-MUTATIONS FAILED killed={killed}/{len(MUTATIONS)} restored=GREEN")
        print(f"LAN-DELETE-MUTATIONS OK killed={killed}/{len(MUTATIONS)} restored=GREEN")


if __name__ == "__main__":
    main()
