"""Require named behavioral failures from isolated update mutations."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
UNIT = ["_build/default/test/lan_update.exe"]
MUTATIONS = [
    ("no-update", "rust/run_store.ml", "Ok (value, replace { db with rows } store)",
     "let _rows = rows in Ok (value, store)", "updated row stored:"),
    ("all-keys", "rust/run_store.ml", "Bignum.compare key stored_key = 0",
     "Bignum.compare key key = 0", "other key preserved:"),
    ("all-models", "rust/run_store.ml", "String.equal model.name name",
     "String.equal name name", "other model preserved:"),
    ("missing-row-success", "rust/run_store.ml", "let* _previous = previous ()",
     'let* _previous = Some ("", key, value)', "missing row refused:"),
    ("erased-update", "target/toasty-7bd502cb.sig",
     "toasty::update!(__lan_row { #{fields} }).exec(&mut #{db}).await?; ",
     "", "checked model result:"),
]


def run(root, command, timeout=120):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=timeout)


def build(root):
    result = run(root, ["zsh", "dev/dunecho.sh", "build"], timeout=None)
    if result.returncode != 0:
        sys.exit(f"LAN-UPDATE-MUTATIONS build failed: {result.stdout}{result.stderr}")


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="update-mutations-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        build(scratch)
        result = run(scratch, UNIT)
        if result.returncode != 0:
            sys.exit(f"LAN-UPDATE-MUTATIONS clean control failed: {result.stdout}{result.stderr}")
        print("LAN-UPDATE-MUTATIONS CONTROL OK", flush=True)
        killed = 0
        survivors = []
        for name, relative, before, after, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-UPDATE-MUTATIONS {name}: expected exactly one source site")
            path.write_text(original.replace(before, after))
            build(scratch)
            result = run(scratch, UNIT)
            path.write_text(original)
            if result.returncode != 1 or failure not in result.stderr:
                survivors.append(f"LAN-UPDATE-MUTATIONS {name} survived: {result.stdout}{result.stderr}")
                break
            killed += 1
            print(f"LAN-UPDATE-MUTATIONS {name} KILLED", flush=True)
        build(scratch)
        result = run(scratch, UNIT)
        if result.returncode != 0:
            sys.exit(f"LAN-UPDATE-MUTATIONS restored control failed: {result.stdout}{result.stderr}")
        if survivors:
            print("\n".join(survivors), flush=True)
            sys.exit(f"LAN-UPDATE-MUTATIONS FAILED killed={killed}/{len(MUTATIONS)} restored=GREEN")
        print(f"LAN-UPDATE-MUTATIONS OK killed={killed}/{len(MUTATIONS)} restored=GREEN")


if __name__ == "__main__":
    main()
