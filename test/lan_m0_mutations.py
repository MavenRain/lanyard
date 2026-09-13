"""Require EMIT-DIFF to reject byte drift and a deleted target print-rule row."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent


def run(root, *args, timeout=180):
    """Run a child under a deadline without a catch site: poll, then kill."""
    command = [str(arg) for arg in args]
    with tempfile.TemporaryFile(mode="w+") as out, tempfile.TemporaryFile(mode="w+") as err:
        child = subprocess.Popen(command, cwd=root, text=True, stdout=out, stderr=err)
        deadline = time.monotonic() + timeout
        while child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.25)
        if child.poll() is None:
            child.kill()
            child.wait()
            sys.exit(f"LAN-M0-MUTATIONS FAIL: timed out after {timeout}s: {' '.join(command)}")
        out.seek(0)
        err.seek(0)
        return subprocess.CompletedProcess(command, child.returncode, out.read(), err.read())


def require(condition, message):
    if not condition:
        sys.exit(f"LAN-M0-MUTATIONS FAIL: {message}")


def main():
    with tempfile.TemporaryDirectory(prefix="lanyard-m0-mutants-") as temporary:
        work = Path(temporary)
        shutil.copytree(ROOT / "corpus", work / "corpus")
        (work / "_build/default/bin").mkdir(parents=True)
        (work / "_build/default/bin/lanyard.exe").symlink_to(ROOT / "_build/default/bin/lanyard.exe")

        def gate():
            return run(work, sys.executable, "-P", ROOT / "dev/emit-diff.py", "--root", work)

        baseline = gate()
        require(baseline.returncode == 0 and "EMIT-DIFF OK" in baseline.stdout, baseline.stderr)
        golden = work / "corpus/m0/golden/src/main.rs"
        original = golden.read_bytes()
        golden.write_bytes(original + b"\n")
        drift = gate()
        require(drift.returncode == 1 and "golden drift: src/main.rs" in drift.stderr,
                f"byte drift survived: {drift}")
        golden.write_bytes(original)
        extra = work / "corpus/m0/golden/extra.rs"
        extra.write_text("// extra golden file\n")
        drift = gate()
        require(drift.returncode == 1 and "golden file set differs" in drift.stderr,
                f"extra file survived: {drift}")
        extra.unlink()

        # A separate compiler rebuild changes the trusted signature catalog.
        # The original checkout and its generated metadata retain their bytes.
        shutil.rmtree(work / "_build")
        for name in ("lib", "surface", "rust", "target", "bin"):
            shutil.copytree(ROOT / name, work / name)
        for name in ("dune", "dune-project"):
            shutil.copyfile(ROOT / name, work / name)
        (work / "dev").mkdir()
        for name in ("gen-target.py", "dunecho.sh"):
            shutil.copyfile(ROOT / "dev" / name, work / "dev" / name)
        signature = work / "target/toasty-7bd502cb.sig"
        rows = signature.read_text().splitlines(keepends=True)
        removed = [row for row in rows if row.startswith("{") and json.loads(row)["name"] == "Model.create"]
        require(len(removed) == 1 and "print" in json.loads(removed[0]), "missing print-rule mutation anchor")
        signature.write_text("".join(row for row in rows if row not in removed))
        generated = run(work, sys.executable, "-P", "dev/gen-target.py")
        require(generated.returncode == 0, f"mutated catalog generation: {generated.stderr}")
        built = run(work, "zsh", "dev/dunecho.sh", "build", timeout=900)
        require(built.returncode == 0 and "OK build" in built.stdout,
                f"mutated compiler build: {built.stdout}{built.stderr}")
        deleted = gate()
        require(deleted.returncode == 1 and "EMIT-DIFF FAIL: emission exited 1" in deleted.stderr
                and "unbound: Todo_create" in deleted.stderr,
                f"deleted print rule survived: {deleted}")
        print("LAN-M0-MUTATIONS kill-evidence: " + deleted.stderr.strip())
    print("LAN-M0-MUTATIONS OK byte-drift=KILLED extra-file=KILLED deleted-print-rule=KILLED")


if __name__ == "__main__":
    main()
