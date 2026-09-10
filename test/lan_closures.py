"""Execute typed closures, including cloned environments and Send/Sync bounds."""
from pathlib import Path
import json
import re
import sys
import tempfile

# Resolve the shared harness from this checkout under Python's safe-path mode.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lan_native import DRIVER, ROOT, FORBIDDEN, OWNERSHIP, function, limbs, nat, run


def require(condition, message):
    if not condition:
        print(f"LAN-CLOSURES FAIL: {message}", file=sys.stderr)
        sys.exit(1)


def main():
    source = ROOT / "test/fixtures/native-closures.lan"
    emitted = run(DRIVER, "emit", "--native", source)
    require(emitted.returncode == 0 and not emitted.stderr,
            emitted.stderr or f"emit exit {emitted.returncode}")
    require(emitted.stdout.encode() == (ROOT / "test/goldens/native-closures.rs").read_bytes(),
            "closure golden differs")
    require(not re.search(FORBIDDEN, emitted.stdout), "forbidden Rust construct")
    require(not re.search(OWNERSHIP, emitted.stdout), "ownership or public field drift")
    version = run("rustup", "run", "1.98", "rustc", "--version")
    require(version.returncode == 0 and version.stdout.startswith("rustc 1.98.1 "),
            "pinned Rust compiler missing")
    cases = [("captured", 22), ("repeated", 33), ("local", 90), ("noCapture", 42),
             ("captureOrder", 14), ("owned", 23), ("erased", 33), ("nullary", 29),
             ("nestedCapture", 28), ("higherOrder", 41), ("sumClosure", 17)]
    observations = [f'println!("{{:?}}", {function(name)}()?.0);' for name, _ in cases]
    expected = [limbs(value) for _, value in cases]
    observations.append(f'println!("{{:?}}", {function("oneCapture")}({nat(47)})?.0);')
    expected.append(limbs(47))
    # Exercise Clone itself, after the original environment has left scope.
    observations += [f'let owned = {function("pack")}(Arc::new({nat(17)}))?.f0;',
                     'let copied = owned.clone();', 'drop(owned);',
                     f'println!("{{:?}}", (copied.call)(Arc::new({nat(5)}))?.0);',
                     f'println!("{{:?}}", (copied.call)(Arc::new({nat(9)}))?.0);',
                     'let shared = Arc::new(copied);',
                     'let shared_copy = Arc::clone(&shared);', 'drop(shared);',
                     f'println!("{{:?}}", (shared_copy.call)(Arc::new({nat(11)}))?.0);',
                     'send_sync(&shared_copy);',
                     'send_future(async move { std::future::ready(()).await; drop(shared_copy); });']
    expected += [limbs(22), limbs(26), limbs(28)]
    harness = ('\nfn send_sync<T: Send + Sync>(_: &T) {}\n'
               'fn send_future<F: std::future::Future + Send>(_: F) {}\n'
               'fn main() -> Result<(), Error> {\n' + '\n'.join(observations) + '\nOk(())\n}\n')
    with tempfile.TemporaryDirectory(prefix="lanyard-closures-") as directory:
        directory = Path(directory)
        rust, binary = directory / "closures.rs", directory / "closures"

        def compile_source(text):
            rust.write_text(text + harness)
            compiled = run("rustup", "run", "1.98", "rustc", "--edition=2024",
                           "-A", "dead_code", "-A", "unused_variables", rust, "-o", binary)
            require(compiled.returncode == 0,
                    compiled.stderr or f"compile exit {compiled.returncode}")
            executed = run(binary)
            require(executed.returncode == 0 and not executed.stderr,
                    executed.stderr or f"run exit {executed.returncode}")
            return [json.loads(line) for line in executed.stdout.splitlines()]

        require(compile_source(emitted.stdout) == expected, "closure results differ")
        # The order mutation keeps all types valid; only execution can detect it.
        before = "Arc::clone(&(c0)), Arc::clone(&(c1)), p0"
        after = "Arc::clone(&(c1)), Arc::clone(&(c0)), p0"
        require(before in emitted.stdout, "missing capture-order mutation anchor")
        require(compile_source(emitted.stdout.replace(before, after, 1)) != expected,
                "capture-order mutant survived")
        # Drop the stored captured offset without changing the factory's type.
        before = "let saved_c0 = Arc::clone(&(c0));"
        after = "let saved_c0 = Arc::new(Nat(Vec::new()));"
        # pack's factory is selected explicitly because other captures have other types.
        factory = "fn c_" + "pack$0:1".encode().hex() + "("
        require(factory in emitted.stdout, "missing pack factory anchor")
        start = emitted.stdout.index(factory)
        prefix, body = emitted.stdout[:start], emitted.stdout[start:]
        require(before in body, "missing clone mutation anchor")
        require(compile_source(prefix + body.replace(before, after, 1)) != expected,
                "clone-environment mutant survived")
        # Removing Send from the boxed callback must break the async bound.
        rust.write_text(emitted.stdout.replace("+ Send + Sync", "+ Sync") + harness)
        rejected = run("rustup", "run", "1.98", "rustc", "--edition=2024", rust, "-o", binary)
        require(rejected.returncode != 0 and "cannot be sent between threads safely" in rejected.stderr,
                "missing Send mutation was not rejected for thread safety")
    print(f"LAN-CLOSURES OK observations={len(expected)} mutants=3 compiler={version.stdout.strip()}")


if __name__ == "__main__":
    main()
