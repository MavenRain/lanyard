"""Build and run the M0 Todo crate offline against clean local target pins."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("lanyard_m0_checks", ROOT / "dev/m0-gates.py")
CHECKS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKS
SPEC.loader.exec_module(CHECKS)
STEPS = ("BUILD", "PREPARE", "CRATE-INIT", "CRATE-INDEX", "RUSTC", "CARGO-BUILD", "RUN")
LOCK = "dev/validation/stage-e-todo/Cargo.lock"
INPUTS = ("corpus/m0/todo.lan", "corpus/m0/todo.stdout", "target/PIN.json", LOCK,
          "corpus/m0/golden/Cargo.toml", "corpus/m0/golden/src/main.rs")
CRATE_FILES = ("Cargo.toml", "Cargo.git.toml", "Cargo.lock", "src/main.rs")
GOLDEN_FILES = ("Cargo.toml", "src/main.rs")


def hashes(root, names):
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}


def prepared(root, crate):
    """The preparer may relocate dependencies, but cannot change emitted Rust."""
    golden_root = root / "corpus/m0/golden"
    golden_files = {str(path.relative_to(golden_root)) for path in golden_root.rglob("*")
                    if path.is_file()}
    if golden_files != set(GOLDEN_FILES):
        raise ValueError(f"golden crate file set differs: {sorted(golden_files ^ set(GOLDEN_FILES))}")
    files = {str(path.relative_to(crate)) for path in crate.rglob("*") if path.is_file()}
    if files != set(CRATE_FILES):
        raise ValueError(f"prepared crate file set differs: {sorted(files ^ set(CRATE_FILES))}")
    for actual, golden in (("Cargo.git.toml", "Cargo.toml"), ("src/main.rs", "src/main.rs")):
        if (crate / actual).read_bytes() != (golden_root / golden).read_bytes():
            raise ValueError(f"prepared crate differs from golden: {actual}")
    if (crate / "Cargo.lock").read_bytes() != (root / LOCK).read_bytes():
        raise ValueError("prepared crate lock differs")
    return hashes(crate, CRATE_FILES)


def pin_commit(pins, name):
    """The pin file names the commit each library checkout must carry."""
    entry = pins.get(name) or {}
    commit = entry.get("commit")
    if not commit:
        raise ValueError(f"target/PIN.json lacks the {name} commit")
    return commit


def library_state(root, name, path):
    """Measure the checkout itself. The pin file states an intention only."""
    label = name.upper()
    head = CHECKS.invoke(CHECKS.Check(f"{label}-HEAD",
                                      ("git", "-C", str(path), "rev-parse", "HEAD")), root)
    if head[0] != 0:
        raise ValueError(f"{name} HEAD is unreadable")
    status = CHECKS.invoke(CHECKS.Check(f"{label}-STATUS",
                                        ("git", "-C", str(path), "status", "--porcelain",
                                         "--untracked-files=no")), root)
    if status[0] != 0 or status[1]:
        raise ValueError(f"{name} checkout is not clean")
    return {"path": str(path), "commit": head[1].decode(errors="replace").strip()}


def library_unmoved(root, name, path, before):
    """A library may not move or become dirty while its crate builds."""
    try:
        after = library_state(root, name, path)
    except ValueError as problem:
        raise ValueError(f"{name} changed during its build") from problem
    if after != before:
        raise ValueError(f"{name} changed during its build")
    return after


def run(root, output, toasty, topcoat, target, toolchain, jobs):
    rows, artifacts, inputs, executable_info, libraries = [], {}, {}, {}, {}
    error = ""
    crate = output / "crate"

    def step(name, argv, **options):
        row = CHECKS.run_check(CHECKS.Check(name, tuple(map(str, argv)), **options), root, output)
        rows.append(row)
        return row["status"] == "PASS"

    def pipeline():
        inputs.update(hashes(root, INPUTS))
        pins = json.loads((root / "target/PIN.json").read_text()).get("libraries", {})
        checkouts = (("toasty", toasty), ("topcoat", topcoat))
        commits = {name: pin_commit(pins, name) for name, _ in checkouts}
        for name, path in checkouts:
            state = library_state(root, name, path)
            if state["commit"] != commits[name]:
                raise ValueError(f"{name} HEAD differs from its pin")
            libraries[name] = state
        expected = (root / "corpus/m0/todo.stdout").read_bytes()
        (output / "program.expected").write_bytes(expected)
        if not step("BUILD", ("zsh", root / "dev/dunecho.sh", "build"),
                    markers=("OK build: 0 errors, 0 warnings",), timeout=900):
            return
        if not step("PREPARE", (sys.executable, "-P", root / "dev/prepare-crate.py",
                               "--toasty", toasty, "--topcoat", topcoat,
                               "--source", root / "corpus/m0/todo.lan", "--print-model", "Todo",
                               "--lock", root / LOCK, "--output", crate),
                    expected=f"CRATE-PREPARE OK manifest={crate / 'Cargo.toml'}\n".encode(),
                    expected_stderr=b"", timeout=360):
            return
        artifacts.update(prepared(root, crate))
        # The scratch tree is ignored by the compiler repository. Give the
        # compile ledger a local index containing the exact generated inputs.
        # Both steps drop the operator's Git configuration. A stock global
        # config prints branch-name advice, and a global ignore file rejects
        # the generated lock, so an inherited setting fails a correct crate.
        if not step("CRATE-INIT", ("git", "-c", "init.defaultBranch=main",
                                   "-c", "advice.defaultBranchName=false",
                                   "-C", crate, "init", "--quiet"),
                    expected=b"", expected_stderr=b""):
            return
        if not step("CRATE-INDEX", ("git", "-c", "core.excludesFile=/dev/null",
                                    "-C", crate, "add", "--force", "--", *CRATE_FILES),
                    expected=b"", expected_stderr=b""):
            return
        if not step("RUSTC", ("rustup", "run", toolchain, "rustc", "-vV")):
            return
        hosts = re.findall(r"^host: ([A-Za-z0-9_]+(?:-[A-Za-z0-9_]+){2,})$",
                           (output / "RUSTC.stdout").read_text(), re.M)
        if len(hosts) != 1:
            raise ValueError("rustc did not report one host target")
        host = hosts[0]
        # Force Cargo to run for each fresh crate. A cached ledger verdict alone
        # cannot establish that the executable exists. Cargo retains its cache.
        if not step("CARGO-BUILD", (
                "gateledger", "run", "--force", "--ledger", root / ".gatework/gateledger",
                "--dir", crate, "--scope", "Cargo.toml", "--scope", "Cargo.lock",
                "--scope", "src",
                "--toolchain", toolchain, "--", "env", f"RUSTUP_TOOLCHAIN={toolchain}",
                "RUSTC_WRAPPER=", "CARGO_INCREMENTAL=0", "cargocho", "--warn", "build", "--",
                "--offline", "--locked", "--manifest-path", crate / "Cargo.toml",
                "--target-dir", target, "--target", host, "--bin", "lanyard-program",
                "--profile", "dev", "--jobs", jobs), timeout=1200):
            return
        # Detect source or lock changes before executing the build's result.
        if hashes(crate, CRATE_FILES) != artifacts:
            raise ValueError("prepared crate changed during its build")
        # The build lasts minutes. Measure both checkouts again, so that a
        # library edited during that window cannot pass as the pinned source.
        for name, path in checkouts:
            library_unmoved(root, name, path, libraries[name])
        executable = target / host / "debug/lanyard-program"
        executable_info.update(path=str(executable), sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
        step("RUN", (executable,), expected=expected, expected_stderr=b"", timeout=60)
        if hashes(crate, CRATE_FILES) != artifacts:
            raise ValueError("prepared crate changed during its run")
        if hashes(root, INPUTS) != inputs:
            raise ValueError("M0 inputs changed during validation")

    try:
        pipeline()
    except (OSError, ValueError, KeyError, TypeError) as problem:
        error = str(problem)
    complete = tuple(row["name"] for row in rows) == STEPS
    good = complete and not error and all(row["status"] == "PASS" for row in rows)
    state, code = ("PASS", 0) if good else ("FAIL", 1)
    report = {"format": 1, "root": str(root), "summary": {"status": state, "exit_code": code,
              "complete": complete, "error": error}, "checks": rows, "inputs": inputs,
              "crate_sha256": artifacts, "executable": executable_info,
              "libraries": libraries,
              "target_dir": str(target), "toolchain": toolchain, "m0_exit": "not-stamped"}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"M0-E2E {state}" + (f": {error}" if error else ""))
    print(f"M0-E2E-REPORT {output / 'report.json'}")
    return code


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("jobs must be positive")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toasty", type=Path, required=True)
    parser.add_argument("--topcoat", type=Path, required=True)
    parser.add_argument("--output", type=Path,
                        help="new directory for crate, captures and report, taken from the repository root")
    parser.add_argument("--target-dir", type=Path,
                        help="Cargo cache, taken from the repository root (default: .gatework/cargo-target)")
    parser.add_argument("--toolchain", default="1.98", help="installed Rust toolchain (default: 1.98)")
    parser.add_argument("--jobs", type=positive, default=2)
    args = parser.parse_args()
    try:
        work = ROOT / ".gatework"
        work.mkdir(exist_ok=True)
        if args.output is None:
            output = Path(tempfile.mkdtemp(prefix="m0-e2e.", dir=work))
        else:
            output = (ROOT / args.output).resolve()
            output.mkdir()
        target = (ROOT / (args.target_dir or work / "cargo-target")).resolve()
        return run(ROOT, output, args.toasty.resolve(), args.topcoat.resolve(),
                   target, args.toolchain, args.jobs)
    except (OSError, ValueError) as error:
        print(f"M0-E2E ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
