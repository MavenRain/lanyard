"""Require named FORM failures in isolated builds and a restored control."""
from contextlib import ExitStack
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
MUTATIONS = [
    ("skip-duplicates", "rust/form_data.ml",
     "List.mem_assoc name fields", "false", "refused form 4:"),
    ("skip-body-bound", "rust/form_data.ml",
     "String.length body > max_bytes", "false", "body limit refused:"),
    ("skip-emitted-validation", "rust/form_data.ml",
     "lan_form_validate_component(key)?;", "", "emitted parser:"),
    ("skip-effect-contract", "rust/text_ops.ml",
     "entry.effects = effects operation && row.effects = entry.effects",
     "true", "metadata effects:"),
]


def run(root, command):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=900)


def check(root, failure=None):
    build = run(root, ["zsh", "dev/dunecho.sh", "build"])
    if build.returncode != 0:
        sys.exit(f"LAN-FORM-MUTATIONS build failed: {build.stdout}{build.stderr}")
    result = run(root, ["_build/default/test/lan_form.exe"])
    expected = 0 if failure is None else 1
    if result.returncode != expected or (failure is not None and failure not in result.stderr):
        sys.exit(f"LAN-FORM-MUTATIONS expected {failure or 'passing control'}: {result.stdout}{result.stderr}")


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="form-mutations-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        check(scratch)
        print("LAN-FORM-MUTATIONS CONTROL OK", flush=True)
        for name, relative, before, after, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-FORM-MUTATIONS {name}: expected exactly one source site")
            with ExitStack() as restore:
                restore.callback(path.write_text, original)
                path.write_text(original.replace(before, after))
                check(scratch, failure)
            print(f"LAN-FORM-MUTATIONS {name} KILLED", flush=True)
        check(scratch)
    print(f"LAN-FORM-MUTATIONS OK killed={len(MUTATIONS)}/{len(MUTATIONS)} restored=GREEN")


if __name__ == "__main__":
    main()
