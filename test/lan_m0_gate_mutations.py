"""Kill M0 assertion controls; expose the unresolved emitter ceiling control."""
import contextlib
from dataclasses import replace
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lan_m0_gates import GATES
from lan_m0_mutations import run
from target import Drift, PIN

ROOT = Path(__file__).resolve().parent.parent
# The five killed assertion controls, in the order the harness runs them.
ROSTER = ["R0-COUNT", "R0-TARGET", "TARGET-PIN", "KERNEL-CARRY", "EMIT-DIFF"]


def require(condition, message):
    if not condition:
        sys.exit(f"M0-GATE-MUTATIONS FAIL: {message}")


def main():
    killed = []
    with tempfile.TemporaryDirectory(prefix="lanyard-m0-gate-mutants-") as temporary:
        work = Path(temporary) / "repo"
        cloned = run(ROOT, "git", "clone", "--local", "--no-hardlinks", ROOT, work)
        require(cloned.returncode == 0, f"scratch clone: {cloned.stderr}")
        # Overlay current sources so a staged or unstaged fix is tested too.
        for directory in ("lib", "surface", "rust", "target", "bin", "test", "corpus"):
            shutil.rmtree(work / directory)
            shutil.copytree(ROOT / directory, work / directory,
                            ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("dune", "dune-project", "SPEC.md"):
            shutil.copyfile(ROOT / name, work / name)
        # dev subdirectories carry leg inputs, so copy the complete tree.
        # The frozen captures and the caches stay out of the scratch clone.
        shutil.rmtree(work / "dev")
        shutil.copytree(ROOT / "dev", work / "dev",
                        ignore=shutil.ignore_patterns("__pycache__", "validation"))
        spike = "dev/spikes/denominators.json"
        require((work / spike).read_bytes() == (ROOT / spike).read_bytes(),
                "dev overlay missed a subdirectory")
        output = work / ".gatework/controls"
        output.mkdir(parents=True)
        legs = {check.name: check for check in GATES.seven_legs(work, output)}

        def build():
            built = run(work, "zsh", "dev/dunecho.sh", "build", timeout=900)
            require(built.returncode == 0 and "OK build" in built.stdout,
                    f"scratch compiler: {built.stdout}{built.stderr}")

        def check(name, expected, diagnostic=""):
            row = GATES.run_check(legs[name], work, output)
            text = (output / f"{name}.stdout").read_text() + (output / f"{name}.stderr").read_text()
            require(row["status"] == expected and diagnostic in text,
                    f"{name}: expected {expected} {diagnostic!r}, got {row}: {text}")
            return row

        def kill(name, diagnostic):
            row = check(name, "FAIL", diagnostic)
            require(row["exit_code"] == 1, f"{name}: unrelated exit {row['exit_code']}")
            killed.append(name)
            print(f"M0-GATE-MUTATIONS {name}=KILLED diagnostic={diagnostic}")

        build()
        for name in GATES.LEG_NAMES[:-1]:
            check(name, "PENDING" if name == "TRUSTED-LINES" else "PASS")

        census = work / "lib/spec_count.ml"
        original = census.read_text()
        anchor = 'row "formers" Term.formers;'
        require(original.count(anchor) == 1, "census anchor differs")
        census.write_text(original.replace(anchor, 'row "formers" ("Extra" :: Term.formers);'))
        build()
        kill("R0-COUNT", "R0-COUNT FAIL")
        census.write_text(original)
        build()
        check("R0-COUNT", "PASS")

        # A driver can print the right census and still fail. The shell leg
        # must propagate that failure instead of accepting the equal bytes.
        driver = work / "_build/default/bin/lanyard.exe"
        driver_bytes = driver.read_bytes()
        counted = run(work, driver, "spec-count")
        require(counted.returncode == 0, "baseline census command")
        driver.unlink()
        driver.write_text("#!/bin/zsh\ncat <<'M0_CENSUS'\n" + counted.stdout + "M0_CENSUS\nexit 7\n")
        driver.chmod(0o755)
        row = check("R0-COUNT", "FAIL", "spec-count command failed")
        require(row["exit_code"] == 1, "failed driver not propagated")
        driver.write_bytes(driver_bytes)
        check("R0-COUNT", "PASS")
        print("M0-GATE-MUTATIONS failed-census-command=KILLED")

        signature = work / "target/toasty-7bd502cb.sig"
        original = signature.read_text()
        rows = [json.loads(line) for line in original.splitlines() if line.startswith("{")]
        atom = dict(next(row for row in rows if row["kind"] == "type"))
        atom["name"] = "Tenth"
        signature.write_text(original + json.dumps(atom) + "\n")
        kill("R0-TARGET", "outside closed atom list")
        signature.write_text(original)
        check("R0-TARGET", "PASS")

        # The existing drift fixture copies source bytes and reads identities
        # once. It never links Git metadata or writes the two upstream trees.
        with contextlib.ExitStack() as cleanup:
            drift = Drift("test_control")
            drift.setUp()
            cleanup.callback(drift.doCleanups)
            legs["TARGET-PIN"] = replace(legs["TARGET-PIN"], argv=(
                "zsh", str(work / "dev/target-pin.sh"), "--target", str(drift.target),
                "--toasty", str(drift.sources["toasty"]), "--topcoat", str(drift.sources["topcoat"]),
                "--identity", json.dumps(drift.identity)))
            check("TARGET-PIN", "PASS")
            relative, first, _last = PIN.ANCHORS[0]
            anchor_path = drift.sources["topcoat"] / relative
            original_anchor = anchor_path.read_bytes()
            lines = original_anchor.splitlines(keepends=True)
            lines[first - 1] = bytes([lines[first - 1][0] ^ 1]) + lines[first - 1][1:]
            anchor_path.write_bytes(b"".join(lines))
            kill("TARGET-PIN", "TARGET-PIN DIFF FAIL")
            anchor_path.write_bytes(original_anchor)
            check("TARGET-PIN", "PASS")

        kernel = work / "lib/check.ml"
        original = kernel.read_bytes()
        kernel.write_bytes(original + b"\n")
        kill("KERNEL-CARRY", "bytes-differ")
        kernel.write_bytes(original)
        check("KERNEL-CARRY", "PASS")

        emitter = work / "rust/emit.ml"
        original = emitter.read_bytes()
        emitter.write_bytes(original + b"\n" * 50)
        row = check("TRUSTED-LINES", "PENDING")
        require(row["exit_code"] == 0, "emitter control no longer measures the open ceiling")
        emitter.write_bytes(original)
        check("TRUSTED-LINES", "PENDING")
        print("M0-GATE-MUTATIONS TRUSTED-LINES=PENDING added-lines=50 kernel-only-exit=0")

        original = signature.read_text()
        lines = original.splitlines(keepends=True)
        removed = [line for line in lines if line.startswith("{") and json.loads(line)["name"] == "Model.create"]
        require(len(removed) == 1, "print-rule anchor differs")
        signature.write_text("".join(line for line in lines if line not in removed))
        build()
        kill("EMIT-DIFF", "unbound: Todo_create")
        signature.write_text(original)
        build()
        check("EMIT-DIFF", "PASS")
    require(killed == ROSTER, f"control roster changed: {killed}")
    print(f"M0-GATE-MUTATIONS OK killed={len(killed)} pending=1 informational=1 restored=GREEN")


if __name__ == "__main__":
    main()
