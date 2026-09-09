#!/usr/bin/env python3
"""Exercise the installed driver boundary and the census gate's refusal."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"


def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, text=True,
                          capture_output=True, timeout=30)


def require(condition, message):
    if not condition:
        print(message, file=sys.stderr)
        sys.exit(1)


checked = run(DRIVER, "check", "examples/m0-todo.lan")
require(checked.returncode == 0 and checked.stdout == "" and checked.stderr == "",
        f"Todo check failed: {checked.stderr}")
printed = run(DRIVER, "check", "--print", "examples/m0-todo.lan")
require(printed.returncode == 0 and "def Todo :" in printed.stdout
        and "axiom Todo_create :" in printed.stdout and printed.stderr == "",
        "checked form omitted the model or its foreign operation")
disclosed = run(DRIVER, "axioms", "examples/m0-todo.lan")
require(disclosed.returncode == 0 and "Todo_create" in disclosed.stdout.splitlines()
        and "Todo_get_by_id" in disclosed.stdout.splitlines()
        and "Todo" not in disclosed.stdout.splitlines(),
        "axiom disclosure omitted model operations or treated the product as an axiom")
refused = run(DRIVER, "check", "test/lanyard/exponent-response.lan")
require(refused.returncode == 1 and refused.stdout == ""
        and "operation Bad: response must be first order" in refused.stderr,
        "exponent-response refusal did not name Bad or use exit 1")
legacy = run(DRIVER, "check", "examples/m0-spine.kan")
require(legacy.returncode == 0 and legacy.stdout == "" and legacy.stderr == "",
        "the carried .kan entry point changed")

with tempfile.TemporaryDirectory(prefix="lanyard-census-") as directory:
    scratch = Path(directory)
    (scratch / "dev").mkdir()
    (scratch / "_build/default/bin").mkdir(parents=True)
    shutil.copy2(ROOT / "dev/r0-count.sh", scratch / "dev/r0-count.sh")
    (scratch / "_build/default/bin/lanyard.exe").symlink_to(DRIVER)
    spec = (ROOT / "SPEC.md").read_text()
    (scratch / "SPEC.md").write_text(spec)
    baseline = run("zsh", scratch / "dev/r0-count.sh")
    require(baseline.returncode == 0 and "R0-COUNT OK" in baseline.stdout,
            "census scratch baseline failed")
    (scratch / "SPEC.md").write_text(spec.replace("foreign type constants: 9",
                                                 "foreign type constants: 10"))
    mutant = run("zsh", scratch / "dev/r0-count.sh")
    require(mutant.returncode == 1 and "R0-COUNT FAIL" in mutant.stdout,
            "foreign census mutant survived")

print("LANYARD-CLI OK checks=7 census-mutant=KILLED")
