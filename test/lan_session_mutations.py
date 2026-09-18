"""Require behavioral failures for request-session state and input mutations."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
UNIT = ["_build/default/test/lan_session.exe"]
CLI = [sys.executable, "-P", "test/lan_session.py"]
MUTATIONS = [
    ("store-reset", "rust/interp.ml", "run (number + 1) state (text :: reversed) rest",
     "run (number + 1) { state with store } (text :: reversed) rest",
     CLI + ["Session.test_todo_lifecycle"], "FAIL: test_todo_lifecycle"),
    ("budget-reset", "rust/interp.ml", "run (number + 1) state (text :: reversed) rest",
     "run (number + 1) { state with steps } (text :: reversed) rest",
     UNIT, "aggregate step budget:"),
    ("response-order", "rust/interp.ml", 'String.concat "" (List.rev reversed)',
     'String.concat "" reversed', UNIT, "ordered transcript:"),
    ("URI-validation", "rust/run_script.ml", "let* uri = Run_http.uri uri in",
     "let* uri = Ok uri in", UNIT, "invalid URI escape:"),
]


def run(root, command, timeout=600):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=timeout)


def build(root):
    result = run(root, ["zsh", "dev/dunecho.sh", "build"], timeout=600)
    if result.returncode != 0:
        sys.exit(f"LAN-SESSION-MUTATIONS build failed: {result.stdout}{result.stderr}")


def controls(root, label):
    for command in (UNIT, CLI):
        result = run(root, command)
        if result.returncode != 0:
            sys.exit(f"LAN-SESSION-MUTATIONS {label} failed: {result.stdout}{result.stderr}")
    print(f"LAN-SESSION-MUTATIONS {label} OK", flush=True)


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="session-mutations-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", ".kanon-replies",
            "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        build(scratch)
        controls(scratch, "CLEAN")
        killed = 0
        for name, relative, before, after, command, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-SESSION-MUTATIONS {name}: expected exactly one source site")
            path.write_text(original.replace(before, after))
            build(scratch)
            result = run(scratch, command)
            path.write_text(original)
            if result.returncode != 1 or failure not in result.stderr:
                sys.exit(f"LAN-SESSION-MUTATIONS {name} survived: {result.stdout}{result.stderr}")
            killed += 1
            print(f"LAN-SESSION-MUTATIONS {name} KILLED", flush=True)
        build(scratch)
        controls(scratch, "RESTORED")
        print(f"LAN-SESSION-MUTATIONS OK killed={killed}/{len(MUTATIONS)}")


if __name__ == "__main__":
    main()
