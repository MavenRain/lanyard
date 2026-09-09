"""Check tree extraction freshness and runtime agreement with recursion controls.

Run after the normal OCaml build. Complete command output and source hashes
are saved under .gatework/mu-tree-bridge, or the directory passed with --out.
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
    parser.add_argument("--out", type=Path, default=ROOT / ".gatework/mu-tree-bridge")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    exporter = ROOT / "_build/default/dev/mu-bridge/export_mu.exe"
    compiler = ROOT / "_build/default/bin/lanyard.exe"
    fixture = ROOT / "test/meta/mu-tree-bridge.kan"
    generated = ROOT / "meta/test/GeneratedMuTree.lean"
    expected_extraction = generated.read_bytes()
    observations = []

    def run(name, command, expected=None):
        argv = [str(arg) for arg in command]
        result = subprocess.run(argv, cwd=ROOT, capture_output=True,
                                timeout=120, check=False)
        (out / (name + ".stdout")).write_bytes(result.stdout)
        (out / (name + ".stderr")).write_bytes(result.stderr)
        passed = result.returncode == 0 and result.stderr == b""
        if expected is not None:
            passed = passed and result.stdout == expected
        observations.append({"name": name, "command": argv,
                             "exit": result.returncode, "passed": passed})
        return result, passed

    def runtime(name, path, export, expected):
        checks = []
        for host in ("kernel", "both"):
            _, passed = run(name + "-" + host,
                            [compiler, "run", path, "--export", export,
                             "--host", host], expected)
            checks.append(passed)
        return all(checks)

    _, fresh = run("extraction", [exporter, "--tree", fixture], expected_extraction)
    _, axioms = run("axioms", [compiler, "axioms", fixture], b"")
    main_runtime = runtime("main", fixture, "main", b"13\n")
    original_runtime = runtime("original", fixture, "original", b"17\n")

    # Both child order and the second recursive input must affect the answer.
    source = fixture.read_text()
    original = "fork (mirror r) (mirror l)"
    source_count = source.count(original)
    controls = {}
    for name, replacement, expected in (
            ("preserve-order", "fork (mirror l) (mirror r)", b"17\n"),
            ("drop-right", "fork leaf (mirror l)", b"5\n")):
        changed = out / (name + ".kan")
        changed.write_text(source.replace(original, replacement))
        extracted, exported = run(name + "-extraction", [exporter, "--tree", changed])
        detected = source_count == 1 and exported and extracted.stdout != expected_extraction
        _, empty_axioms = run(name + "-axioms", [compiler, "axioms", changed], b"")
        correct = runtime(name, changed, "main", expected)
        controls[name] = {"extraction_changed": detected,
                          "empty_axioms": empty_axioms, "runtime_passed": correct}

    tracked = [fixture, generated, ROOT / "dev/mu-bridge/export_mu.ml",
               ROOT / "dev/mu-bridge/check_tree.py", ROOT / "dev/mu-bridge/dune",
               ROOT / "lib/positivity.ml",
               ROOT / "lib/rules.ml", ROOT / "surface/elab.ml"]
    passed = all([fresh, axioms, main_runtime, original_runtime,
                  all(all(control.values()) for control in controls.values())])
    evidence = {"passed": passed, "controls": controls, "observations": observations,
                "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in tracked}}
    (out / "result.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print("MU-TREE-BRIDGE " + ("OK" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
