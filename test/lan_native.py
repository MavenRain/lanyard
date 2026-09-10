"""Compile the emitted source and compare native arithmetic with Python integers."""
from pathlib import Path
import json
import random
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
FORBIDDEN = (r"\b(?:unsafe|unwrap|expect|panic|assert|assert_eq|debug_assert|unreachable|todo)\w*"
             r"|\b(?:loop|while|return|break|continue|as)\b|\bfor\s+\w+\s+in\b|\w\[")
OWNERSHIP = r"\bRc\b|\bpub\b"
# Each compile and each run stays bounded.  The bound is 600 s, because a
# loaded machine needs more than 120 s.
TIMEOUT = 600


def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, text=True,
                          capture_output=True, timeout=TIMEOUT)


def require(condition, message):
    if not condition:
        print(f"LAN-NATIVE FAIL: {message}", file=sys.stderr)
        sys.exit(1)


def function(name):
    return "f_" + name.encode().hex()


def nat(number):
    return f'Nat::decimal("{number}")?'


def limbs(number):
    return list(number.to_bytes((number.bit_length() + 7) // 8, "little"))


def main():
    source = ROOT / "test/fixtures/native.lan"
    emitted = run(DRIVER, "emit", "--native", source)
    require(emitted.returncode == 0 and not emitted.stderr, emitted.stderr)
    golden = ROOT / "test/goldens/native.rs"
    require(emitted.stdout.encode() == golden.read_bytes(), "native golden differs")
    require(not re.search(FORBIDDEN, emitted.stdout), "forbidden Rust construct")
    require(not re.search(OWNERSHIP, emitted.stdout), "ownership or public field drift")
    # Each static rule rejects a construct the printer must never emit.
    for probe in ["let n = other.unwrap_or_default();", "debug_assert!(n == m);",
                  "unreachable!();", "todo!();", "struct Nat(pub Vec<u8>);",
                  "let byte = other.0[i];"]:
        require(re.search(FORBIDDEN, probe) or re.search(OWNERSHIP, probe),
                f"static rule misses {probe}")
    version = run("rustup", "run", "1.98", "rustc", "--version")
    require(version.returncode == 0 and version.stdout.startswith("rustc 1.98.1 "),
            f"pinned compiler missing: {version.stdout} {version.stderr}")
    statements, expected = [], []

    def observe(expression, value):
        statements.append(f'println!("{{:?}}", ({expression}).0);')
        expected.append(limbs(value))

    for name, value in [("projection", 5), ("branch", 29), ("both", 38),
                        ("nested", 2), ("huge", 2 ** 256), ("zero", 7)]:
        observe(f"{function(name)}()?", value)
    observe(f"{function('many')}(Arc::new({nat(123)}))?", 123)
    observe(f"{function('one')}({nat(321)})?", 321)
    statements.append(f"{function('unit')}()?;")
    rng = random.Random(20260910)
    boundaries = [0, 1, 255, 256, 257, 65535, 65536, 2 ** 31 - 1,
                  2 ** 64, 2 ** 128 - 1, 2 ** 256, 2 ** 1024 - 1]
    pairs = [(a, b) for a in boundaries for b in boundaries]
    pairs += [(rng.getrandbits(384), rng.getrandbits(384)) for _ in range(40)]
    for left, right in pairs:
        args = f"Arc::new({nat(left)}), Arc::new({nat(right)})"
        for operation, value in [("add", left + right), ("subtract", max(0, left - right)),
                                 ("multiply", left * right)]:
            observe(f"{function(operation)}({args})?", value)
        for operation, value in [("equal", left == right), ("less", left < right)]:
            observe(f"{function('choose')}(Arc::new({function(operation)}({args})?))?",
                    29 if value else 11)

    with tempfile.TemporaryDirectory(prefix="lanyard-native-") as directory:
        directory = Path(directory)
        rust = directory / "native.rs"
        binary = directory / "native"
        # A single compiler invocation covers all observations and ownership paths.
        rust.write_text(emitted.stdout + "\nfn main() -> Result<(), Error> {\n"
                        + "\n".join(statements) + "\nOk(())\n}\n")
        compiled = run("rustup", "run", "1.98", "rustc", "--edition=2024", "-A", "dead_code",
                       "-A", "unused_variables", rust, "-o", binary)
        require(compiled.returncode == 0, compiled.stderr)
        executed = run(binary)
        require(executed.returncode == 0 and not executed.stderr, executed.stderr)
        actual = [json.loads(line) for line in executed.stdout.splitlines()]
        require(actual == expected, "native results differ from Python integer oracle")
        # Both mutants must compile, then disagree with the same independent oracle.
        mutants = [
            ("arithmetic", ").add(&(", ").sub(&("),
            ("boolean", "::V1(()) } else", "::V0(()) } else"),
        ]
        for label, before, after in mutants:
            require(before in emitted.stdout, f"missing {label} mutation anchor")
            rust.write_text(emitted.stdout.replace(before, after, 1)
                            + "\nfn main() -> Result<(), Error> {\n"
                            + "\n".join(statements) + "\nOk(())\n}\n")
            compiled = run("rustup", "run", "1.98", "rustc", "--edition=2024", "-A", "dead_code",
                           "-A", "unused_variables", rust, "-o", binary)
            require(compiled.returncode == 0, f"{label} mutant did not compile: {compiled.stderr}")
            executed = run(binary)
            require(executed.returncode == 0 and not executed.stderr, f"{label} mutant crashed")
            require([json.loads(line) for line in executed.stdout.splitlines()] != expected,
                    f"{label} mutant survived")
        surface_cases = [
            ("foreign", "def main : Db -> prod () := fun (db : Db) => Db.push_schema db", "foreign type Db"),
            ("recursive", "mu N : Type 0 := | z : N | s (n : N) : N def main : N := s z", "layout mu<N>"),
        ]
        for label, text, diagnostic in surface_cases:
            fixture = directory / f"{label}.lan"
            fixture.write_text(text)
            checked = run(DRIVER, "check", fixture)
            result = run(DRIVER, "emit", "--native", fixture)
            require(checked.returncode == 0, f"{label} refusal fixture does not check")
            require(result.returncode == 1 and not result.stdout and diagnostic in result.stderr,
                    f"{label} refusal: {result.stderr}")
        usage_forms = [[], [str(source)], ["--native"], ["--native", str(source), "extra"],
                       ["--native", "examples/m0-spine.kan"]]
        for args in usage_forms:
            result = run(DRIVER, "emit", *args)
            require(result.returncode == 64 and not result.stdout, f"usage accepted {args}")
    print(f"LAN-NATIVE OK observations={len(expected)} refusals={len(surface_cases)} "
          f"usage={len(usage_forms)} mutants={len(mutants)} compiler={version.stdout.strip()}")


if __name__ == "__main__":
    main()
