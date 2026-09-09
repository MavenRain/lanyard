"""Check extraction freshness, runtime agreement, and a changed-recursion control.

Run after the normal OCaml build. Complete command output and source hashes
are saved under .gatework/mu-bridge, or the directory passed with --out.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / ".gatework/mu-bridge")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    exporter = ROOT / "_build/default/dev/mu-bridge/export_mu.exe"
    compiler = ROOT / "_build/default/bin/lanyard.exe"
    fixture = ROOT / "test/meta/mu-nat-bridge.kan"
    generated = ROOT / "meta/test/GeneratedMuNat.lean"
    observations = []

    def run(name, command, expected=None):
        result = subprocess.run([str(arg) for arg in command], cwd=ROOT,
                                capture_output=True, timeout=120, check=False)
        (out / (name + ".stdout")).write_bytes(result.stdout)
        (out / (name + ".stderr")).write_bytes(result.stderr)
        passed = result.returncode == 0 and result.stderr == b""
        if expected is not None:
            passed = passed and result.stdout == expected
        observations.append({"name": name, "command": [str(x) for x in command],
                             "exit": result.returncode, "passed": passed})
        return result, passed

    _, fresh = run("extraction", [exporter, fixture], generated.read_bytes())
    _, kernel = run("kernel", [compiler, "run", fixture, "--export", "main",
                               "--host", "kernel"], b"6\n")
    _, hosts = run("hosts", [compiler, "run", fixture, "--export", "main",
                             "--host", "both"], b"6\n")
    _, axioms = run("axioms", [compiler, "axioms", fixture], b"")

    # A valid source change must alter both the exported recursion and its answer.
    source = fixture.read_text()
    original = "succ (succ (double m))"
    count = source.count(original)
    changed = out / "single-step.kan"
    changed.write_text(source.replace(original, "succ (double m)"))
    exported, mutant_export = run("changed-extraction", [exporter, changed])
    mutation_detected = count == 1 and mutant_export and exported.stdout != generated.read_bytes()
    _, mutant_kernel = run("changed-kernel", [compiler, "run", changed,
                                             "--export", "main", "--host", "kernel"], b"3\n")
    _, mutant_hosts = run("changed-hosts", [compiler, "run", changed,
                                           "--export", "main", "--host", "both"], b"3\n")
    tracked = [fixture, generated, ROOT / "dev/mu-bridge/export_mu.ml",
               ROOT / "lib/positivity.ml", ROOT / "lib/rules.ml",
               ROOT / "surface/elab.ml"]
    passed = all([fresh, kernel, hosts, axioms, mutation_detected, mutant_kernel, mutant_hosts])
    evidence = {"passed": passed, "changed_recursion_detected": mutation_detected,
                "observations": observations,
                "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in tracked}}
    (out / "result.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print("MU-BRIDGE " + ("OK" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
