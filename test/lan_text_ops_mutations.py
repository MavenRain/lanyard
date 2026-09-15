"""Require named failures for text adapter mutations, with restored controls."""
from contextlib import ExitStack
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
UNIT = ["_build/default/test/lan_text_ops.exe"]
MUTATIONS = [
    ("omit-unicode-space", "rust/text_ops.ml", "0x20; 0x85; 0xa0; 0x1680;",
     "0x20; 0x85; 0x1680;", "Unicode trim:"),
    ("invert-empty", "rust/run_store.ml", '(if String.equal text "" then 1 else 0)',
     '(if String.equal text "" then 0 else 1)', "empty true:"),
    ("metadata-name-only", "rust/text_ops.ml", "fun text -> text.row = row",
     "fun text -> text.row.name = row.name", "metadata type arguments:"),
    ("trim-one-end", "target/topcoat-51caa01.sig", ".trim().to_owned()",
     ".trim_start().to_owned()", "emitted trim:"),
    ("omit-direct-specialization", "surface/specialize.ml", "if specialized source then",
     "if Option.is_some (arguments source) then", "ASCII trim:"),
]


def run(root, command):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=900)


def build(root):
    result = run(root, ["zsh", "dev/dunecho.sh", "build"])
    if result.returncode != 0:
        sys.exit(f"LAN-TEXT-MUTATIONS build failed: {result.stdout}{result.stderr}")


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="text-mutations-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        build(scratch)
        result = run(scratch, UNIT)
        if result.returncode != 0:
            sys.exit(f"LAN-TEXT-MUTATIONS clean control failed: {result.stdout}{result.stderr}")
        print("LAN-TEXT-MUTATIONS CONTROL OK", flush=True)
        killed = 0
        failures = []
        for name, relative, before, after, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-TEXT-MUTATIONS {name}: expected exactly one source site")
            with ExitStack() as restore:
                restore.callback(path.write_text, original)
                path.write_text(original.replace(before, after))
                build(scratch)
                result = run(scratch, UNIT)
            if result.returncode != 1 or failure not in result.stderr:
                failures.append(f"LAN-TEXT-MUTATIONS {name} survived: {result.stdout}{result.stderr}")
            killed += 1
            print(f"LAN-TEXT-MUTATIONS {name} KILLED", flush=True)
        build(scratch)
        result = run(scratch, UNIT)
        if result.returncode != 0:
            sys.exit(f"LAN-TEXT-MUTATIONS restored control failed: {result.stdout}{result.stderr}")
        if failures:
            print("\n".join(failures), flush=True)
            sys.exit(f"LAN-TEXT-MUTATIONS FAILED killed={killed}/{len(MUTATIONS)} restored=GREEN")
        print(f"LAN-TEXT-MUTATIONS OK killed={killed}/{len(MUTATIONS)} restored=GREEN")


if __name__ == "__main__":
    main()
