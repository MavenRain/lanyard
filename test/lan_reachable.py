"""Exercise crate dependency selection through the checked source and Rust runtime."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "_build/default/bin/lanyard.exe"
ENTRY = "    f_6d61696e()?;"


def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, text=True,
                          capture_output=True, timeout=120)


def require(condition, message):
    if not condition:
        sys.exit(f"LAN-REACHABLE FAIL: {message}")


def function(name):
    return "f_" + name.encode().hex()


def main():
    observations = []
    refusals = []
    with tempfile.TemporaryDirectory(prefix="lanyard-reachable-") as temporary:
        work = Path(temporary)

        def emit(name, source):
            fixture = work / f"{name}.lan"
            fixture.write_text(source)
            output = work / name
            result = run(CLI, "emit", "--crate", output, fixture)
            require(result.returncode == 0 and not result.stdout and not result.stderr,
                    f"{name}: {result.stderr}")
            return (output / "src/main.rs").read_text()

        def observe(name, source, expected):
            require(source.count(ENTRY) == 1, f"{name}: observation entry missing")
            rust = work / f"{name}.rs"
            rust.write_text(source.replace(ENTRY, '    println!("{:?}", f_6d61696e()?.0);'))
            binary = work / f"{name}-program"
            compiled = run("rustup", "run", "1.98", "rustc", "--edition=2024",
                           "-Adead_code", "-Aunused_variables", "-Dunused_must_use", rust, "-o", binary)
            require(compiled.returncode == 0, f"{name}: {compiled.stderr}")
            result = run(binary)
            require(result.returncode == 0 and not result.stderr
                    and json.loads(result.stdout) == expected, f"{name}: runtime result {result}")
            observations.append(name)

        def refuse(name, source, diagnostic=None):
            fixture = work / f"{name}.lan"
            fixture.write_text(source)
            output = work / name
            result = run(CLI, "emit", "--crate", output, fixture)
            require(result.returncode == 1 and not result.stdout and result.stderr
                    and (diagnostic is None or diagnostic in result.stderr)
                    and not output.exists() and not Path(str(output) + ".partial").exists(),
                    f"{name}: refusal or atomic output failed: {result}")
            refusals.append(name)

        fixture = (ROOT / "test/fixtures/reachable.lan").read_text()
        source = emit("reachable", fixture)
        require(source.encode() == (ROOT / "test/goldens/reachable.rs").read_bytes(), "golden drift")
        for name in ("main", "selected", "pack", "invoke", "offset"):
            require(f"fn {function(name)}(" in source, f"missing dependency {name}")
        for name in ("generic", "idle", "selectedExtra"):
            require(f"fn {function(name)}(" not in source, f"unused definition {name}")
        require("toasty::" not in source and "topcoat::" not in source and "async fn" not in source,
                "unused database metadata reached the pure crate")
        observe("reachable", source, [31])
        module = run(CLI, "emit", "--target", ROOT / "test/fixtures/reachable.lan")
        require(module.returncode == 1 and not module.stdout
                and "connection type arguments must be closed" in module.stderr,
                "module emission silently pruned the generic definition")

        closures = (ROOT / "test/fixtures/native-closures.lan").read_text()
        for name, value in (("sumClosure", 17), ("nestedCapture", 28)):
            generated = emit(name, closures + f"\ndef main : Nat := {name}\n")
            observe(name, generated, [value])
        recursive = (ROOT / "test/fixtures/native-recursive.lan").read_text()
        for name, value in (("mutualTotal", 4), ("wrappedTotal", 72)):
            generated = emit(name, recursive + f"\ndef main : Nat := {name}\n")
            observe(name, generated, [value])
        alias = emit("aliases", "def base : Nat := 23\ndef alias : Nat := base\ndef main : Nat := alias\n")
        observe("aliases", alias, [23])

        # A model operation's quoted type can have the same layout as another
        # model. Schema arguments must preserve both names, plus schema-only use.
        models = emit("models", (ROOT / "test/fixtures/reachable-models.lan").read_text())
        for name in ("First", "Second", "SchemaOnly"):
            require("struct LanModel" + name.encode().hex() + " {" in models,
                    f"lost model identity {name}")
        require("struct LanModel" + "Unused".encode().hex() not in models,
                "unused model schema was printed")
        require("async fn main()" in models and "f_6d61696e().await?;" in models,
                "retained database calls lost async propagation")
        declarations = (ROOT / "test/fixtures/reachable-models.lan").read_text().split("def main :", 1)[0]
        metadata = emit("metadata", declarations + 'def main : Nat :=\n'
                        '  (First.get_by_id 1 (Db.connect SchemaOnly Bytes b"sqlite::memory:")).0\n')
        require("struct LanModel" + "First".encode().hex() + " {" in metadata
                and "struct LanModel" + "Second".encode().hex() + " {" not in metadata,
                "operation schema arguments lost the model behind its quoted type")

        # Restore unsupported definitions to the root graph. Every case must
        # fail before the output directory is created, including untaken branches.
        refuse("used-postulate", "axiom hidden : Nat\ndef main : Nat := hidden\n")
        refuse("bad-unused-body", "def broken : Nat := ()\ndef main : Nat := 1\n", "mismatch")
        refuse("used-generic", fixture.replace("def main : Nat := selected",
               'def main : Db := generic Unused b"sqlite::memory:"'), "must be closed")
        refuse("used-model", "model Bad with | id : Nat | extra : prod () end\n"
               "def main : Bad := tuple (1, ())\n", "model field Bad.extra")
        refuse("branch-postulate", "axiom hidden : Nat\n"
               "def pick : sum (Nat, Nat) -> Nat := fun (value : sum (Nat, Nat)) => case value with\n"
               "| 0 (x : Nat) => x\n| 1 (x : Nat) => hidden\n"
               "def main : Nat := pick (inj 0 of 2 7)\n")
        refuse("nested-postulate", "axiom hidden : Nat\n"
               "def apply : (Nat -> Nat) -> Nat := fun (f : Nat -> Nat) => f 0\n"
               "def main : Nat := apply (fun (x : Nat) => hidden)\n")

        # Retaining every source row restores the unsupported helper and must
        # fail the positive fixture. Dropping a transitive dependency must also
        # be detectable at compilation, rather than producing a wrong program.
        missing = source.replace("fn " + function("offset") + "(", "fn removed_offset(", 1)
        require(missing != source, "dependency deletion mutation anchor missing")
        rust = work / "missing.rs"
        rust.write_text(missing)
        rejected = run("rustup", "run", "1.98", "rustc", "--edition=2024", rust, "-o", work / "missing")
        require(rejected.returncode != 0 and "cannot find function" in rejected.stderr,
                "transitive dependency deletion survived")
        require(re.search(r"\b(?:unsafe|unwrap|expect|panic|assert|while|loop|as)\b", source) is None,
                "golden violates Rust house rules")
    print(f"LAN-REACHABLE OK observations={len(observations)} refusals={len(refusals)} models=3 metadata=1 mutants=1")


if __name__ == "__main__":
    main()
