"""Require response contract failures in isolated builds with restored controls."""
from contextlib import ExitStack
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
MUTATIONS = [
    ("wrong-status", "rust/run_http.ml", "HTTP/1.1 200 OK", "HTTP/1.1 201 Created", "direct call:"),
    ("wrong-length", "rust/run_http.ml", "string_of_int (String.length body)", '"0"', "UTF-8 byte length:"),
    ("skip-response-validation", "rust/run_http.ml", "not (String.is_valid_utf_8 body)", "false", "invalid runtime response:"),
    ("skip-effect-contract", "rust/text_ops.ml", "entry.effects = effects operation && row.effects = entry.effects",
     "true", "metadata effects:"),
]


def run(root, command):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=900)


def check(root, failure=None):
    build = run(root, ["zsh", "dev/dunecho.sh", "build"])
    if build.returncode != 0:
        sys.exit(f"LAN-RESPONSE-MUTATIONS build failed: {build.stdout}{build.stderr}")
    result = run(root, ["_build/default/test/lan_response.exe"])
    expected = 0 if failure is None else 1
    if result.returncode != expected or (failure is not None and failure not in result.stderr):
        sys.exit(f"LAN-RESPONSE-MUTATIONS expected {failure or 'passing control'}: {result.stdout}{result.stderr}")


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="response-mutations-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        check(scratch)
        print("LAN-RESPONSE-MUTATIONS CONTROL OK", flush=True)
        for name, relative, before, after, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-RESPONSE-MUTATIONS {name}: expected exactly one source site")
            with ExitStack() as restore:
                restore.callback(path.write_text, original)
                path.write_text(original.replace(before, after))
                check(scratch, failure)
            print(f"LAN-RESPONSE-MUTATIONS {name} KILLED", flush=True)
        check(scratch)
    print(f"LAN-RESPONSE-MUTATIONS OK killed={len(MUTATIONS)}/{len(MUTATIONS)} restored=GREEN")


if __name__ == "__main__":
    main()
