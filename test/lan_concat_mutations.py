"""Require concat order and validation failures with restored build controls."""
from contextlib import ExitStack
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
MUTATIONS = [
    ("reverse-inputs", "rust/run_store.ml", "(left ^ right)", "(right ^ left)", "left before right:"),
    ("skip-left-validation", "rust/run_store.ml", 'text ~what:"concat left" operation.family left',
     'Ok (let _value = left in "")', "left byte range:"),
    ("skip-right-validation", "rust/run_store.ml", 'text ~what:"concat right" operation.family right',
     'Ok (let _value = right in "")', "right byte range:"),
    ("skip-effect-contract", "rust/text_ops.ml", "entry.effects = effects operation && row.effects = entry.effects",
     "true", "metadata effects:"),
]


def check(root, failure=None):
    build = subprocess.run(["zsh", "dev/dunecho.sh", "build"], cwd=root,
                           text=True, capture_output=True, timeout=900)
    if build.returncode != 0:
        sys.exit(f"LAN-CONCAT-MUTATIONS build failed: {build.stdout}{build.stderr}")
    result = subprocess.run(["_build/default/test/lan_concat.exe"], cwd=root,
                            text=True, capture_output=True, timeout=60)
    if result.returncode != (0 if failure is None else 1) or (failure is not None and failure not in result.stderr):
        sys.exit(f"LAN-CONCAT-MUTATIONS expected {failure or 'passing control'}: {result.stdout}{result.stderr}")


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="concat-mutations-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        check(scratch)
        print("LAN-CONCAT-MUTATIONS CONTROL OK", flush=True)
        for name, relative, before, after, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-CONCAT-MUTATIONS {name}: expected exactly one source site")
            with ExitStack() as restore:
                restore.callback(path.write_text, original)
                path.write_text(original.replace(before, after))
                check(scratch, failure)
            print(f"LAN-CONCAT-MUTATIONS {name} KILLED", flush=True)
        check(scratch)
    print(f"LAN-CONCAT-MUTATIONS OK killed={len(MUTATIONS)}/{len(MUTATIONS)} restored=GREEN")


if __name__ == "__main__":
    main()
