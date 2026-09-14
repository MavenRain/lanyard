"""Require specific behavioral failures from five isolated interpreter mutations."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
UNIT = ["_build/default/test/lan_run.exe"]
CLI = [sys.executable, "-P", "test/lan_run.py"]
MUTATIONS = [
    ("arguments", "rust/interp.ml", "(List.rev arguments) fn.body", "arguments fn.body",
     UNIT, "arguments in declaration order:"),
    ("steps", "rust/interp.ml", "state.steps <= 0", "state.steps < -1000",
     UNIT, "step bound:"),
    ("foreign", "rust/run_store.ml", 'refuse ("foreign operation " ^ row.schema)',
     "Ok (Unit, store)", UNIT, "foreign refusal:"),
    ("connection-isolation", "rust/run_store.ml", "Ok (Database database.id,", "Ok (Database 0,",
     CLI, "FAIL: test_separate_connections"),
    ("lookup-key", "rust/run_store.ml", "Bignum.equal key stored_key", "Bignum.equal stored_key stored_key",
     CLI, "FAIL: test_distinct_keys"),
]


def run(root, command, timeout=120):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=timeout)


def build(root):
    # A cold build of the copied tree has no bound. Machine load must not
    # report a build as a surviving mutant.
    result = run(root, ["zsh", "dev/dunecho.sh", "build"], timeout=None)
    if result.returncode != 0:
        sys.exit(f"LAN-RUN-MUTATIONS build failed: {result.stdout}{result.stderr}")


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="run-mutations-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        build(scratch)
        for command in (UNIT, CLI):
            result = run(scratch, command)
            if result.returncode != 0:
                sys.exit(f"LAN-RUN-MUTATIONS clean control failed: {result.stdout}{result.stderr}")
        print("LAN-RUN-MUTATIONS CONTROL OK", flush=True)
        killed = 0
        for name, relative, before, after, command, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-RUN-MUTATIONS {name}: expected exactly one source site")
            path.write_text(original.replace(before, after))
            build(scratch)
            result = run(scratch, command)
            path.write_text(original)
            if result.returncode != 1 or failure not in result.stderr:
                sys.exit(f"LAN-RUN-MUTATIONS {name} survived: {result.stdout}{result.stderr}")
            killed += 1
            print(f"LAN-RUN-MUTATIONS {name} KILLED", flush=True)
        print(f"LAN-RUN-MUTATIONS OK killed={killed}/{len(MUTATIONS)}")


if __name__ == "__main__":
    main()
