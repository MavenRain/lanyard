"""Require URI text refusals and exact spelling in isolated compiler builds."""
from contextlib import ExitStack
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
MUTATIONS = [
    ("skip-interpreter-validation", "rust/run_store.ml",
     "let* uri = Run_http.uri uri in", "let* uri = Ok uri in", "refused path 0:"),
    ("replace-uri-text", "rust/run_store.ml",
     "of_text operation.family uri, store", 'of_text operation.family "/", store', "accepted path 1:"),
    ("skip-emitted-validation", "rust/text_ops.ml",
     "lan_uri_validate(&__lan_uri_text)?; ", "", "emitted validation:"),
]


def run(root, command):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=900)


def check(root, failure=None):
    build = run(root, ["zsh", "dev/dunecho.sh", "build"])
    if build.returncode != 0:
        sys.exit(f"LAN-URI-TEXT-MUT build failed: {build.stdout}{build.stderr}")
    result = run(root, ["_build/default/test/lan_uri_text.exe"])
    expected = 0 if failure is None else 1
    if result.returncode != expected or (failure is not None and failure not in result.stderr):
        sys.exit(f"LAN-URI-TEXT-MUT expected {failure or 'passing control'}: {result.stdout}{result.stderr}")


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="uri-text-mut-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        check(scratch)
        print("LAN-URI-TEXT-MUT CONTROL OK", flush=True)
        for name, relative, before, after, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-URI-TEXT-MUT {name}: expected exactly one source site")
            with ExitStack() as restore:
                restore.callback(path.write_text, original)
                path.write_text(original.replace(before, after))
                check(scratch, failure)
            print(f"LAN-URI-TEXT-MUT {name} KILLED", flush=True)
        check(scratch)
    print(f"LAN-URI-TEXT-MUT OK killed={len(MUTATIONS)}/{len(MUTATIONS)} restored=GREEN")


if __name__ == "__main__":
    main()
