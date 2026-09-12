"""Check complete crate output, entry execution, errors and output protection."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "_build/default/bin/lanyard.exe"
FILES = {"Cargo.toml", "src/main.rs"}


def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, text=True,
                          capture_output=True, timeout=120)


def require(condition, message):
    if not condition:
        sys.exit(f"LAN-CRATE FAIL: {message}")


def main():
    with tempfile.TemporaryDirectory(prefix="lanyard-crate-") as temporary:
        work = Path(temporary)
        crate = work / "output with spaces"
        emitted = run(CLI, "emit", "--crate", crate, "test/fixtures/crate.lan")
        require(emitted.returncode == 0 and not emitted.stdout and not emitted.stderr,
                f"crate emission: {emitted.stdout}{emitted.stderr}")
        require({str(path.relative_to(crate)) for path in crate.rglob("*") if path.is_file()} == FILES,
                "crate file set differs")
        for name in sorted(FILES):
            require((crate / name).read_bytes() == (ROOT / "test/goldens/crate" / name).read_bytes(),
                    f"golden drift: {name}")
        manifest = tomllib.loads((crate / "Cargo.toml").read_text())
        require(set(manifest["dependencies"]) == {"serde", "tokio", "toasty", "topcoat"},
                "dependency set differs")
        require(manifest["workspace"] == {} and manifest["package"]["publish"] is False,
                "crate is not isolated from a parent workspace")
        pins = json.loads((ROOT / "target/PIN.json").read_text())["libraries"]
        for name in ("toasty", "topcoat"):
            dependency = manifest["dependencies"][name]
            require(dependency["git"] == f"https://github.com/tokio-rs/{name}"
                    and dependency["rev"] == pins[name]["commit"] and "path" not in dependency,
                    f"dependency pin differs: {name}")
        require("sqlite" in manifest["dependencies"]["toasty"]["features"]
                and "router" in manifest["dependencies"]["topcoat"]["features"]
                and {"rt", "macros"} <= set(manifest["dependencies"]["tokio"]["features"]),
                "required target features are missing")
        source = (crate / "src/main.rs").read_text()
        require('#[tokio::main(flavor = "current_thread")]\nasync fn main()' in source
                and "    f_6d61696e().await?;" in source, "async entry point differs")
        forbidden = r"\b(?:unsafe|unwrap|expect|panic|assert|while|loop|as)\b|\bfor\s+\w+\s+in\b"
        require(re.search(forbidden, source) is None, "generated Rust violates house rules")

        before = {name: (crate / name).read_bytes() for name in FILES}
        refused = run(CLI, "emit", "--crate", crate, "test/fixtures/crate.lan")
        require(refused.returncode == 64 and not refused.stdout and "output path exists" in refused.stderr,
                "existing output directory was accepted")
        require(before == {name: (crate / name).read_bytes() for name in FILES}, "existing files changed")
        occupied = work / "occupied"
        occupied.write_text("keep\n")
        linked = work / "linked"
        linked.symlink_to(crate, target_is_directory=True)
        for destination in (occupied, linked):
            refused = run(CLI, "emit", "--crate", destination, "test/fixtures/crate.lan")
            require(refused.returncode == 64 and not refused.stdout and "output path exists" in refused.stderr,
                    f"existing output path was accepted: {destination}")
        require(occupied.read_text() == "keep\n" and linked.is_symlink(), "occupied path changed")
        refused = run(CLI, "emit", "--crate", work / "missing/output", "test/fixtures/crate.lan")
        require(refused.returncode == 64 and not refused.stdout and "output parent" in refused.stderr
                and not (work / "missing").exists(), "missing parent was accepted")

        fixture = work / "program.lan"
        negatives = [
            ("def other : Nat := 7", "missing runtime entry point main"),
            ("def main : Nat -> Nat := fun (value : Nat) => value", "entry point requires runtime arguments: main"),
            ("def main : Type 0 := Nat", "missing runtime entry point main"),
            ("axiom main : Nat", "missing runtime entry point main"),
            ("def main : Nat := missing", "unbound"),
        ]
        for index, (text, diagnostic) in enumerate(negatives):
            fixture.write_text(text + "\n")
            destination = work / f"refusal-{index}"
            refused = run(CLI, "emit", "--crate", destination, fixture)
            require(refused.returncode == 1 and not refused.stdout and diagnostic in refused.stderr
                    and not destination.exists(), f"semantic refusal failed: {text}: {refused.stderr}")
        usage = [[], ["--crate"], ["--crate", work / "unused"],
                 ["--crate", work / "unused", "test/fixtures/crate.lan", "extra"],
                 ["--crate", work / "unused", "test/fixtures/mu-direct.kan"],
                 ["--native", "--crate", work / "unused", "test/fixtures/crate.lan"]]
        for args in usage:
            refused = run(CLI, "emit", *args)
            require(refused.returncode == 64 and not refused.stdout and "usage:" in refused.stderr,
                    f"usage refusal failed: {args}")

        fixture.write_text("def idle : Db -> prod () := Db.push_schema\ndef main : Nat := 41\n")
        mixed = work / "mixed"
        emitted = run(CLI, "emit", "--crate", mixed, fixture)
        require(emitted.returncode == 0, emitted.stderr)
        mixed_source = (mixed / "src/main.rs").read_text()
        require("fn f_69646c65(" not in mixed_source and "async fn main" not in mixed_source
                and "    f_6d61696e()?;" in mixed_source,
                "unreachable async function was emitted or main changed")

        fixture.write_text("def idle : Db -> prod () := Db.push_schema\n"
                           "def useIdle : (0 f : Db -> prod ()) -> Nat := fun (0 f : Db -> prod ()) => 41\n"
                           "def main : Nat := useIdle idle\n")
        retained = work / "retained"
        emitted = run(CLI, "emit", "--crate", retained, fixture)
        require(emitted.returncode == 0, emitted.stderr)
        retained_source = (retained / "src/main.rs").read_text()
        require("async fn f_69646c65(" in retained_source and "async fn main" not in retained_source
                and "    f_6d61696e()?;" in retained_source,
                "reachable async function changed main")

        fixture.write_text("def main : Nat := 41\n")
        native = work / "native"
        emitted = run(CLI, "emit", "--crate", native, fixture)
        require(emitted.returncode == 0, emitted.stderr)
        rust = (native / "src/main.rs").read_text()
        require("async fn main" not in rust and "    f_6d61696e()?;" in rust,
                "synchronous entry point differs")
        binary = work / "program"

        def execute(text):
            probe = work / "probe.rs"
            probe.write_text(text)
            compiled = run("rustup", "run", "1.98", "rustc", "--edition=2024", "-Dunused_must_use",
                           probe, "-o", binary)
            require(compiled.returncode == 0, compiled.stderr)
            return run(binary)

        observed = execute(rust)
        require(observed.returncode == 0 and not observed.stdout and not observed.stderr,
                "synchronous main did not succeed")
        require(rust.count('Nat::decimal("41")') == 1, "error probe target differs")
        failing = rust.replace('Nat::decimal("41")', 'Nat::decimal("invalid")')
        observed = execute(failing)
        require(observed.returncode != 0 and "Digit" in observed.stderr, "main swallowed a runtime error")
        mutant = failing.replace("    f_6d61696e()?;\n", "")
        require(mutant != failing, "entry deletion mutation target absent")
        observed = execute(mutant)
        require(observed.returncode == 0, "entry deletion control did not distinguish execution")
    print(f"LAN-CRATE OK golden=2 runtime=3 semantic-refusals={len(negatives)} usage-refusals={len(usage)} output-refusals=4 mutants=1")


if __name__ == "__main__":
    main()
