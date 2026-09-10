"""Prove that the Rust erasure tests detect ownership and quantity loss."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / ".gatework"
WORK.mkdir(exist_ok=True)
MUTATIONS = [
    ("clone", "lib/rir.ml", "| Quantity.Many -> RClone term",
     "| Quantity.Many -> term", "LAN-ERASE many FAIL"),
    ("zero", "lib/erase.ml", "not (Quantity.equal q Quantity.Zero)",
     "let _ = q in true", "LAN-ERASE zero FAIL"),
    ("unit-effect", "lib/erase.ml", "| PColl 0 -> Ok true",
     "| PColl 0 -> Ok false", "LAN-ERASE unit-effect FAIL"),
]
REVIEW_MUTATIONS = [
    ("owned", "lib/rir.ml", "| Quantity.Many -> TyArc ty",
     "| Quantity.Many -> ty", "LAN-ERASE many FAIL"),
    ("native-arity", "lib/rir.ml",
     "let fits count declared = Option.fold ~none:true ~some:(Int.equal count) declared in",
     "let fits _count _declared = true in", "LAN-ERASE partial-application FAIL"),
    ("erased-binder", "lib/erase.ml",
     "| LDrop -> Error (Error.Mismatch \"Rust erasure: runtime use of an erased binder\")",
     "| LDrop -> Ok (Rir.RUnit, ac)", "LAN-ERASE erased-binder FAIL"),
    ("prim-arity", "surface/lower.ml",
     "|> Result.map (fun (count : int) -> (name, Some count)))",
     "|> Result.map (fun (_count : int) -> (name, None)))",
     "LAN-ERASE prim-partial-application FAIL"),
]

def run(root, *command):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=120)

def build(root):
    result = run(root, "zsh", "dev/dunecho.sh", "build")
    if result.returncode != 0:
        sys.exit(f"MUTATION build failed: {result.stdout}{result.stderr}")

def kill_all(scratch, mutations):
    for name, relative, before, after, failure in mutations:
        source = scratch / relative
        original = source.read_text()
        if original.count(before) != 1:
            sys.exit(f"MUTATION {name}: expected exactly one source site")
        source.write_text(original.replace(before, after))
        build(scratch)
        result = run(scratch, "_build/default/test/lan_erase.exe")
        source.write_text(original)
        if result.returncode != 1 or failure not in result.stderr:
            sys.exit(f"MUTATION {name} survived: {result.stdout}{result.stderr}")
        print(f"LAN-ERASE-MUTATIONS {name} KILLED", flush=True)

with tempfile.TemporaryDirectory(prefix="rir-mutations-", dir=WORK) as directory:
    scratch = Path(directory) / "root"
    shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
        ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
    (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
    build(scratch)
    baseline = run(scratch, "_build/default/test/lan_erase.exe")
    if baseline.returncode != 0:
        sys.exit(f"MUTATION clean control failed: {baseline.stdout}{baseline.stderr}")
    print("LAN-ERASE-MUTATIONS CONTROL OK", flush=True)
    kill_all(scratch, MUTATIONS)
    print(f"LAN-ERASE-MUTATIONS OK killed={len(MUTATIONS)}/{len(MUTATIONS)}", flush=True)
    kill_all(scratch, REVIEW_MUTATIONS)
    review = len(REVIEW_MUTATIONS)
    print(f"LAN-ERASE-MUTATIONS REVIEW OK killed={review}/{review}")
