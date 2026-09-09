"""Check the indexed vector extraction, payload observations and index rejection.

Run after the OCaml and Lean builds. Command output and source hashes are saved
under .gatework/mu-vector-bridge, or the directory supplied with --out.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def control_certificate(name, baseline):
    """Check changed extracts against an independently specified raw edit.

    The unmodified copy template is certified in meta/test/MuVector.lean.
    A control certificate also references every exported declaration, so
    an empty or incomplete exporter response cannot pass Lean elaboration.
    """
    copy_body = baseline.split("def copy : Term :=\n", 1)[1].split("\n\ndef copyType", 1)[0]
    if name == "zero-payload":
        old = "[(.var 2), (.var 1), (.out"
        new = "[(.var 2), (.lit 0), (.out"
    elif name == "replace-recursion":
        old = ('(.out (.SPi .many "_" (.lan (.SMu "V" [(.var 2)]) (.sec (.SColl 0) []))) '
               '(.apt .many (.var 0)) (.out (.SPi .zero "i" (.lan (.SMu "N" []) '
               '(.sec (.SColl 0) []))) (.apt .zero (.var 2)) (.global "copy")))')
        new = "(.var 0)"
    elif name == "reverse-payloads":
        old = new = None
    else:
        return None
    if old is not None:
        if copy_body.count(old) != 1:
            return None
        copy_body = copy_body.replace(old, new)
    payloads = (25, 17) if name == "reverse-payloads" else (17, 25)
    recursion = "none" if name == "replace-recursion" else "some 1"
    return f'''
namespace KanonMeta.MuVector.Control
example : Generated.naturalDeclaration = MuNat.expectedDeclaration := rfl
example : Generated.declaration = expectedDeclaration := rfl
def sample : Value 2 := .cons {payloads[0]} (.cons {payloads[1]} .nil)
example : Generated.sample = sample.encode := rfl
example : Generated.sampleType = familyType (indexTerm 2) := rfl
example : Generated.sampleRecArg = none := rfl
example : Generated.samplePartial = false := rfl
example : Generated.sampleReducible = true := rfl
example : Generated.copy = {copy_body} := rfl
example : Generated.copyType = copyType := rfl
example : Generated.copyRecArg = {recursion} := rfl
example : Generated.copyPartial = false := rfl
example : Generated.copyReducible = true := rfl
end KanonMeta.MuVector.Control
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / ".gatework/mu-vector-bridge")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    exporter = ROOT / "_build/default/dev/mu-bridge/export_mu.exe"
    compiler = ROOT / "_build/default/bin/lanyard.exe"
    fixture = ROOT / "test/meta/mu-vector-bridge.kan"
    generated = ROOT / "meta/test/GeneratedMuVector.lean"
    expected_extraction = generated.read_bytes()
    observations = []

    def run(name, command, expected=None, rejected=False):
        argv = [str(arg) for arg in command]
        result = subprocess.run(argv, cwd=ROOT, capture_output=True,
                                timeout=120, check=False)
        (out / (name + ".stdout")).write_bytes(result.stdout)
        (out / (name + ".stderr")).write_bytes(result.stderr)
        if rejected:
            passed = (result.returncode == 1 and result.stdout == b""
                      and b"gives the index" in result.stderr
                      and b"the type asks for" in result.stderr)
        else:
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

    _, fresh = run("extraction", [exporter, "--vector", fixture], expected_extraction)
    _, axioms = run("axioms", [compiler, "axioms", fixture], b"")
    main_runtime = runtime("main", fixture, "main", b"67\n")
    original_runtime = runtime("original", fixture, "original", b"67\n")

    source = fixture.read_text()
    controls = {}
    for name, original, replacement, expected in (
            ("zero-payload", "vs j a (copy j w)", "vs j 0 (copy j w)", b"0\n"),
            ("replace-recursion", "vs j a (copy j w)", "vs j a w", b"67\n"),
            ("reverse-payloads", "17 (vs zero 25 vz)", "25 (vs zero 17 vz)", b"59\n")):
        changed = out / (name + ".kan")
        changed.write_text(source.replace(original, replacement))
        extracted, exported = run(name + "-extraction", [exporter, "--vector", changed])
        detected = (source.count(original) == 1 and exported
                    and extracted.stdout != expected_extraction)
        certificate = control_certificate(name, expected_extraction.decode())
        certified = False
        if detected and certificate is not None:
            lean_source = out / (name + ".lean")
            lean_source.write_bytes(extracted.stdout + certificate.encode())
            _, certified = run(name + "-certificate",
                               ["lake", "+leanprover/lean4:v4.33.0-rc1", "--dir", ROOT / "meta",
                                "env", "lean", lean_source], b"")
        _, empty_axioms = run(name + "-axioms", [compiler, "axioms", changed], b"")
        correct = runtime(name, changed, "main", expected)
        controls[name] = {"extraction_changed": detected,
                          "extraction_certified": certified,
                          "empty_axioms": empty_axioms, "runtime_passed": correct}

    # These invalid declarations must fail both checking and extraction.
    rejections = {}
    for name, original, replacement in (
            ("wrong-result-index", "| vz => vz |", "| vz => vs zero 0 vz |"),
            ("wrong-tail-index", "17 (vs zero 25 vz)", "17 vz")):
        changed = out / (name + ".kan")
        changed.write_text(source.replace(original, replacement))
        _, checked = run(name + "-check", [compiler, "check", changed], rejected=True)
        _, extracted = run(name + "-extraction", [exporter, "--vector", changed], rejected=True)
        rejections[name] = source.count(original) == 1 and checked and extracted

    tracked = [fixture, generated, ROOT / "dev/mu-bridge/export_mu.ml",
               ROOT / "dev/mu-bridge/check_vector.py", ROOT / "dev/mu-bridge/dune",
               ROOT / "meta/KanonMeta/MuVector.lean", ROOT / "meta/test/MuVector.lean",
               ROOT / "lib/positivity.ml", ROOT / "lib/rules.ml", ROOT / "surface/elab.ml"]
    passed = all([fresh, axioms, main_runtime, original_runtime,
                  all(all(control.values()) for control in controls.values()),
                  all(rejections.values())])
    evidence = {"passed": passed, "controls": controls, "rejections": rejections,
                "observations": observations,
                "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in tracked}}
    (out / "result.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print("MU-VECTOR-BRIDGE " + ("OK" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
