"""Compare the complete M0 crate with its golden, without normalization."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
FILES = {"Cargo.toml", "src/main.rs"}


def require(condition, message):
    if not condition:
        sys.exit(f"EMIT-DIFF FAIL: {message}")


def run(root, command, timeout):
    """Run the emitter under a deadline without a catch site: poll, then kill."""
    with tempfile.TemporaryFile(mode="w+") as out, tempfile.TemporaryFile(mode="w+") as err:
        child = subprocess.Popen(command, cwd=root, text=True, stdout=out, stderr=err)
        deadline = time.monotonic() + timeout
        while child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.25)
        if child.poll() is None:
            child.kill()
            child.wait()
            sys.exit(f"EMIT-DIFF FAIL: emission timed out after {timeout}s")
        out.seek(0)
        err.seek(0)
        return subprocess.CompletedProcess(command, child.returncode, out.read(), err.read())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    root = parser.parse_args().root.resolve()
    golden = root / "corpus/m0/golden"
    require({str(path.relative_to(golden)) for path in golden.rglob("*") if path.is_file()} == FILES,
            "golden file set differs")
    with tempfile.TemporaryDirectory(prefix="lanyard-emit-diff-") as temporary:
        output = Path(temporary) / "crate"
        command = [str(root / "_build/default/bin/lanyard.exe"), "emit", "--crate",
            str(output), "--print-model", "Todo", str(root / "corpus/m0/todo.lan")]
        result = run(root, command, 300)
        unexpected = f" unexpected stdout: {result.stdout}" if result.stdout else ""
        require(result.returncode == 0 and not result.stdout and not result.stderr,
                f"emission exited {result.returncode}: {result.stderr}{unexpected}")
        require({str(path.relative_to(output)) for path in output.rglob("*") if path.is_file()} == FILES,
                "emitted file set differs")
        for name in sorted(FILES):
            require((output / name).read_bytes() == (golden / name).read_bytes(), f"golden drift: {name}")
    print(f"EMIT-DIFF OK files={len(FILES)} normalization=none")


if __name__ == "__main__":
    main()
