"""Require behavioral failures from isolated model listing mutations."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
UNIT = ["_build/default/test/lan_all.exe"]
MUTATIONS = [
    ("descending-keys", "rust/run_store.ml", "Bignum.compare left right",
     "Bignum.compare right left", "ascending keys and model isolation:"),
    ("all-models", "rust/run_store.ml",
     "(fun (name, _key, _row) -> String.equal name model.name)",
     "(fun (name, _key, _row) -> String.equal name name)", "ascending keys and model isolation:"),
    ("drop-row", "rust/run_store.ml", "(List.rev rows)",
     "(List.filteri (fun index _row -> index <> 0) (List.rev rows))", "ascending keys and model isolation:"),
    ("descending-query", "target/toasty-7bd502cb.sig", ".id().asc()",
     ".id().desc()", "checked ordered query:"),
    ("reverse-list", "rust/model.ml", "__lan_rows.into_iter().rev().try_fold(",
     "__lan_rows.into_iter().try_fold(", "checked ordered query:"),
]


def run(root, command, timeout=120):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=timeout)


def build(root):
    result = run(root, ["zsh", "dev/dunecho.sh", "build"], timeout=None)
    if result.returncode != 0:
        sys.exit(f"LAN-ALL-MUTATIONS build failed: {result.stdout}{result.stderr}")


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="all-mutations-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        build(scratch)
        result = run(scratch, UNIT)
        if result.returncode != 0:
            sys.exit(f"LAN-ALL-MUTATIONS clean control failed: {result.stdout}{result.stderr}")
        print("LAN-ALL-MUTATIONS CONTROL OK", flush=True)
        killed = 0
        survivors = []
        for name, relative, before, after, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-ALL-MUTATIONS {name}: expected exactly one source site")
            path.write_text(original.replace(before, after))
            build(scratch)
            result = run(scratch, UNIT)
            path.write_text(original)
            if result.returncode != 1 or failure not in result.stderr:
                survivors.append(f"LAN-ALL-MUTATIONS {name} survived: {result.stdout}{result.stderr}")
                break
            killed += 1
            print(f"LAN-ALL-MUTATIONS {name} KILLED", flush=True)
        build(scratch)
        result = run(scratch, UNIT)
        if result.returncode != 0:
            sys.exit(f"LAN-ALL-MUTATIONS restored control failed: {result.stdout}{result.stderr}")
        if survivors:
            print("\n".join(survivors), flush=True)
            sys.exit(f"LAN-ALL-MUTATIONS FAILED killed={killed}/{len(MUTATIONS)} restored=GREEN")
        print(f"LAN-ALL-MUTATIONS OK killed={killed}/{len(MUTATIONS)} restored=GREEN")


if __name__ == "__main__":
    main()
