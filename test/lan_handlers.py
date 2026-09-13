"""Check finite handler specialization, scoping, refusals and Rust observations."""
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
        sys.exit(f"LAN-HANDLERS FAIL: {message}")


def function(name):
    return "f_" + name.encode().hex()


def main():
    observations = []
    refusals = []
    fixture = (ROOT / "test/fixtures/handlers.lan").read_text()
    declarations = fixture.split("def run :", 1)[0]
    with tempfile.TemporaryDirectory(prefix="lanyard-handlers-") as temporary:
        work = Path(temporary)

        def emit(name, source):
            path = work / f"{name}.lan"
            path.write_text(source)
            output = work / name
            result = run(CLI, "emit", "--crate", output, path)
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
                    and json.loads(result.stdout) == expected, f"{name}: {result}")
            observations.append(name)

        def refuse(name, source, diagnostic, checked=False):
            path = work / f"{name}.lan"
            path.write_text(source)
            if checked:
                result = run(CLI, "check", path)
                require(result.returncode == 0, f"{name}: unchecked refusal fixture: {result.stderr}")
            output = work / name
            result = run(CLI, "emit", "--crate", output, path)
            require(result.returncode == 1 and not result.stdout and diagnostic in result.stderr
                    and not output.exists() and not Path(str(output) + ".partial").exists(),
                    f"{name}: refusal or atomic output failed: {result}")
            refusals.append(name)

        source = emit("handlers", fixture)
        require(source.encode() == (ROOT / "test/goldens/handlers.rs").read_bytes(), "golden drift")
        for name in ("handle", "finish", "request"):
            require("fn " + function(name) + "(" not in source, f"unfused helper {name}")
        observe("handlers", source, [11])
        observe("pure", emit("pure", declarations + "def main : Nat := handle (App.pure 19)\n"), [19])
        observe("capture", emit("capture", declarations +
            "def run : Nat -> Nat := fun (input : Nat) =>\n"
            "  let offset : Nat := natAdd input 5 in\n"
            "  handle (App.Read offset (fun (answer : Nat) => App.pure (natAdd input answer)))\n"
            "def main : Nat := run 7\n"), [20])
        observe("nested", emit("nested", declarations +
            "def two : App -> Nat := fun (program : App) =>\n"
            "  match program as self in App return Nat with\n"
            "  | App.pure value => value\n"
            "  | App.Read value resume => handle (resume (natAdd value 2))\n"
            "def main : Nat := two (App.Read 4 (fun (a : Nat) =>\n"
            "  App.Read a (fun (b : Nat) => App.pure (natAdd a b))))\n"), [13])
        for tag, expected in ((0, 12), (1, 24)):
            observe(f"branch-{tag}", emit(f"branch-{tag}", declarations +
                "def choose : sum (Nat, Nat) -> Nat := fun (input : sum (Nat, Nat)) =>\n"
                "  case input with\n"
                "  | 0 (x : Nat) => handle (request x)\n"
                "  | 1 (x : Nat) => handle (request (natAdd x x))\n"
                f"def main : Nat := choose (inj {tag} of 2 {8 if tag == 0 else 10})\n"), [expected])
        # A helper chain behind a handler. Every global is specialized once and
        # the specialized body is shared, so a depth that once exhausted the
        # budget now emits. The chain is the identity, so the handler observes
        # the argument.
        chain = "def y0 : Nat -> Nat := fun (x : Nat) => x\n" + "".join(
            f"def y{i} : Nat -> Nat := fun (x : Nat) => y{i-1} (y{i-1} x)\n" for i in range(1, 13))
        observe("shared-chain", emit("shared-chain", declarations + chain +
            "def main : Nat := handle (App.pure (y12 1))\n"), [1])
        observe("one", emit("one", declarations +
            "def take : (1 n : Nat) -> Nat := fun (1 n : Nat) => n\n"
            "def main : Nat := handle (App.pure (take 23))\n"), [23])
        observe("dependent", emit("dependent",
            "mu Mark : (0 n : Nat) -> Type 0 := | mark (0 n : Nat) : Mark n\n"
            "signature Poly : Nat with | Pick (0 n : Nat) (value : Mark n) : Nat end\n"
            "def finish : Poly -> Nat := fun (p : Poly) =>\n"
            "  match p as self in Poly return Nat with\n"
            "  | Poly.pure value => value\n"
            "  | Poly.Pick (0 n : Nat) value resume => 17\n"
            "def main : Nat := finish (Poly.Pick 3 (mark 3) (fun (n : Nat) => Poly.pure n))\n"), [17])
        observe("erased", emit("erased",
            "signature App : Nat with | Pick (0 ignored : Nat) (n : Nat) : Nat end\n"
            "axiom hidden : Nat\n"
            "def finish : App -> Nat := fun (p : App) =>\n"
            "  match p as self in App return Nat with\n"
            "  | App.pure value => value\n"
            "  | App.Pick (0 ignored : Nat) n resume => n\n"
            "def main : Nat := finish (App.Pick hidden 29 (fun (n : Nat) => App.pure n))\n"), [29])
        point = emit("pair-point", declarations +
            "def keepPair : ((n : Nat) * Nat) -> Nat := fun (pair : (n : Nat) * Nat) => 17\n"
            "def run : Nat -> Nat := fun (input : Nat) => handle (App.pure (keepPair (natAdd input 2, 9)))\n"
            "def main : Nat := run 1\n")
        # The SQLite fixture checks this position with a database computation.
        observe("pair-point", point, [17])

        refuse("open", declarations + "def main : App := request 7\n", "not statically fused")
        refuse("dynamic", declarations +
            "def select : sum (Nat, Nat) -> App := fun (input : sum (Nat, Nat)) => case input with\n"
            "| 0 (x : Nat) => App.pure x\n| 1 (x : Nat) => request x\n"
            "def main : Nat := handle (select (inj 0 of 2 7))\n", "not statically fused", checked=True)
        refuse("recursive", "signature App : Nat with | Read (n : Nat) : Nat end\n"
            "def rec handle : App -> Nat := fun (program : App) =>\n"
            "  match program as self in App return Nat with\n"
            "  | App.pure value => value\n"
            "  | App.Read value resume => handle (resume value)\n"
            "def main : Nat := handle (App.pure 1)\n", "structural")
        refuse("bad-unused", fixture + "def broken : Nat := ()\n", "mismatch")
        # Pre-fusion refusal: the elaborator quantity rule rejects the program
        # before Fuse runs, so this case covers no fusion behaviour.
        linear = (declarations +
            "def take : (1 n : Nat) -> Nat := fun (1 n : Nat) => handle (App.pure n)\n"
            "def main : Nat := take 23\n")
        linear_path = work / "linear-quantity-source.lan"
        linear_path.write_text(linear)
        elaborated = run(CLI, "check", linear_path)
        require(elaborated.returncode != 0 and "linear binder" in elaborated.stderr,
                "linear-quantity: the elaborator must refuse this fixture before fusion")
        refuse("linear-quantity", linear, "linear binder")
        # Capture avoidance across a dependent function codomain: the program
        # now reaches the opaque axiom instead of failing the kernel recheck.
        refuse("dependent-codomain",
            "mu Mark : (0 n : Nat) -> Type 0 :=\n| mark (0 n : Nat) : Mark n\n"
            "axiom pick : (k : Nat) -> Mark k\n" + declarations +
            "def aux : Nat -> Nat := fun (x : Nat) =>\n"
            "  let f : (k : Nat) -> Mark k := pick in x\n"
            "def main : Nat := handle (App.pure (aux 5))\n",
            "target metadata missing", checked=True)
        refuse("bad-branch", declarations.replace("| App.pure value => value",
                "| App.pure value => ()", 1) + "def main : Nat := handle (request 7)\n", "mismatch")
        # Expansion exhaustion. Each level duplicates its argument, so the
        # specialized body doubles at every level and the budget stops the
        # expansion. A chain that only calls the level below is shared work and
        # emits, which the shared-chain observation records.
        expansions = "def x0 : Nat -> Nat := fun (x : Nat) => x\n" + "".join(
            f"def x{i} : Nat -> Nat := fun (x : Nat) => natAdd (x{i-1} x) (x{i-1} x)\n"
            for i in range(1, 15))
        refuse("budget", declarations + expansions +
               "def main : Nat := handle (App.pure (x14 1))\n", "budget exhausted")

        database = emit("database", (ROOT / "test/fixtures/handlers-db.lan").read_text())
        for name in ("handle", "handleTwo", "finish", "request"):
            require("fn " + function(name) + "(" not in database, f"database kept {name}")
        require("async fn " + function("run") + "(" in database
                and "f_6d61696e().await?;" in database, "database lost async propagation")
        require(database.count("toasty::create!(") == 4 and database.count(".push_schema()") == 1,
                "database lost or duplicated computations")
        require(re.search(r"\b(?:unsafe|unwrap|expect|panic|assert|while|loop|as)\b", source) is None,
                "golden violates Rust house rules")
        require(re.search(r"\b(?:unsafe|unwrap|expect|panic|assert|while|loop|as)\b", database) is None,
                "database violates Rust house rules")

        # Deleting the fused addition must change the observed result.
        marker = '.add(&(Nat::decimal("1")?))'
        require(marker in source, "addition mutation anchor missing")
        require(source.count(marker) == 1, "addition mutation anchor is not unique")
        changed = source.replace(marker, '.sub(&(Nat::decimal("1")?))', 1)
        rust = work / "changed.rs"
        rust.write_text(changed.replace(ENTRY, '    println!("{:?}", f_6d61696e()?.0);'))
        binary = work / "changed"
        result = run("rustup", "run", "1.98", "rustc", "--edition=2024", rust, "-o", binary)
        require(result.returncode == 0, f"mutation did not compile: {result.stderr}")
        result = run(binary)
        require(result.returncode == 0 and json.loads(result.stdout) != [11], "addition mutation survived")
    print(f"LAN-HANDLERS OK observations={len(observations)} refusals={len(refusals)} database=1 mutants=1")


if __name__ == "__main__":
    main()
