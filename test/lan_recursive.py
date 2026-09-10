"""Compile nominal recursive families and observe constructor and binder semantics."""
from pathlib import Path
import json
import re
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lan_native import DRIVER, ROOT, FORBIDDEN, OWNERSHIP, function, limbs, run


def require(condition, message):
    if not condition:
        print(f"LAN-RECURSIVE FAIL: {message}", file=sys.stderr)
        sys.exit(1)


def main():
    source = ROOT / "test/fixtures/native-recursive.lan"
    emitted = run(DRIVER, "emit", "--native", source)
    require(emitted.returncode == 0 and not emitted.stderr,
            emitted.stderr or f"emit exit {emitted.returncode}")
    require(emitted.stdout.encode() == (ROOT / "test/goldens/native-recursive.rs").read_bytes(),
            "recursive golden differs")
    require(not re.search(FORBIDDEN, emitted.stdout), "forbidden Rust construct")
    require(not re.search(OWNERSHIP, emitted.stdout), "ownership or public field drift")
    version = run("rustup", "run", "1.98", "rustc", "--version")
    require(version.returncode == 0 and version.stdout.startswith("rustc 1.98.1 "),
            "pinned Rust compiler missing")
    cases = [("total", 31), ("treeTotal", 59), ("orderedTree", 383),
             ("mutualTotal", 4), ("captured", 70), ("repeated", 62),
             ("erasedTotal", 43), ("choiceTotal", 47), ("functionTotal", 12),
             ("wrappedTotal", 72)]
    observations = [f'println!("{{:?}}", {function(name)}()?.0);' for name, _ in cases]
    expected = [limbs(value) for _, value in cases]
    observations += [f'let original = {function("sample")}()?;', 'let copied = original.clone();',
                     'drop(original);',
                     f'println!("{{:?}}", {function("sumList")}(Arc::new({function("owned")}(copied)?))?.0);',
                     f'let shared = Arc::new({function("sample")}()?);',
                     'let another = Arc::clone(&shared);', 'drop(shared);',
                     f'println!("{{:?}}", {function("sumList")}(Arc::clone(&another))?.0);',
                     'send_sync(&another);',
                     'send_future(async move { std::future::ready(()).await; drop(another); });',
                     f'let functions = {function("functions")}()?;', 'let copied_functions = functions.clone();',
                     'drop(functions);',
                     f'println!("{{:?}}", {function("applyFunctions")}(Arc::new(copied_functions))?.0);']
    expected += [limbs(31), limbs(31), limbs(12)]
    harness = ('\nfn send_sync<T: Send + Sync>(_: &T) {}\n'
               'fn send_future<F: std::future::Future + Send>(_: F) {}\n'
               'fn main() -> Result<(), Error> {\n' + '\n'.join(observations) + '\nOk(())\n}\n')
    with tempfile.TemporaryDirectory(prefix="lanyard-recursive-") as directory:
        directory = Path(directory)
        rust, binary = directory / "recursive.rs", directory / "recursive"

        def compile_source(text):
            rust.write_text(text + harness)
            return run("rustup", "run", "1.98", "rustc", "--edition=2024", "-A", "dead_code",
                       "-A", "unused_variables", rust, "-o", binary)

        def observe(text):
            compiled = compile_source(text)
            require(compiled.returncode == 0, compiled.stderr or f"compile exit {compiled.returncode}")
            executed = run(binary)
            require(executed.returncode == 0 and not executed.stderr,
                    executed.stderr or f"run exit {executed.returncode}")
            return [json.loads(line) for line in executed.stdout.splitlines()]

        require(observe(emitted.stdout) == expected, "recursive results differ")
        # Both Tree payload fields have the same type, so only execution finds reversal.
        before = "let (v1, v2,) = *payload1;"
        anchor = "fn " + function("treeScore") + "("
        require(anchor in emitted.stdout, "missing treeScore function anchor")
        start = emitted.stdout.index(anchor)
        prefix, body = emitted.stdout[:start], emitted.stdout[start:]
        require(before in body, "missing binder-order mutation anchor")
        require(observe(prefix + body.replace(before, "let (v2, v1,) = *payload1;", 1)) != expected,
                "binder-order mutant survived")
        # Select the constructor expression in choice, not a declaration or match arm.
        anchor = "fn " + function("choice") + "("
        require(anchor in emitted.stdout, "missing choice function anchor")
        start = emitted.stdout.index(anchor)
        prefix, body = emitted.stdout[:start], emitted.stdout[start:]
        require("::V0(Box::new(" in body, "missing tag mutation anchor")
        require(observe(prefix + body.replace("::V0(Box::new(", "::V1(Box::new(", 1)) != expected,
                "constructor-tag mutant survived")
        # Removing nominal indirection must produce an infinite-size diagnostic.
        mutated = '\n'.join(line.replace("Box<(", "(").replace(",)>", ",)")
                            if line.startswith("enum T") else line for line in emitted.stdout.split('\n'))
        rejected = compile_source(mutated)
        require(rejected.returncode != 0 and "infinite size" in rejected.stderr,
                "unboxed recursive-layout mutant was not rejected for infinite size")
        # No construction or elimination is needed to request a nominal signature.
        identity = directory / "identity.lan"
        identity.write_text("mu N : Type 0 := | z : N | s (n : N) : N\n"
                            "mu A : Type 0 := | a (b : B) : A\n"
                            "and B : Type 0 := | b (n : N) : B\n"
                            "def identity : A -> A := fun (value : A) => value\n")
        result = run(DRIVER, "emit", "--native", identity)
        require(result.returncode == 0 and not result.stderr, "signature-only family metadata is missing")
        rust.write_text(result.stdout + '\nfn main() -> Result<(), Error> { Ok(()) }\n')
        compiled = run("rustup", "run", "1.98", "rustc", "--edition=2024", "-A", "dead_code", rust, "-o", binary)
        require(compiled.returncode == 0, compiled.stderr)
    print(f"LAN-RECURSIVE OK observations={len(expected)} signatures=1 mutants=3 compiler={version.stdout.strip()}")


if __name__ == "__main__":
    main()
