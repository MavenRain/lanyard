"""Require disclosure tests to detect omissions, false counts and false classes."""
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lan_m0_mutations import run

ROOT = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        sys.exit(f"LAN-AXIOMS-MUTATIONS FAIL: {message}")


def main():
    source = (ROOT / "surface/axioms.ml").read_text()
    mutations = [
        ("model-metadata", ")) program.instances", ")) (List.filter (fun _instance -> false) program.instances)",
         "cli", "unclassified postulate Todo_create"),
        ("ratio-count", "| Foreign -> total + size", "| Foreign -> total",
         "cli", "class totals or ratio inputs differ"),
        ("postulate-class", 'Option.to_result ~none:(Error.Cannot_infer\n'
         '        ("axiom disclosure: unclassified postulate " ^ name\n'
         '         ^ "; use axioms --names for declaration names"))',
         'Option.value ~default:"unknown" |> Result.ok',
         "cli", "unclassified postulate was hidden or mislabeled"),
        ("partial-marker", "Ok (if definition.Global.partial then", "Ok (if definition.Global.partial && false then",
         "report", "partial marker: report differs"),
    ]
    with tempfile.TemporaryDirectory(prefix="lanyard-axioms-mutants-") as temporary:
        work = Path(temporary)
        for name in ("lib", "surface", "rust", "target", "bin", "test"):
            shutil.copytree(ROOT / name, work / name, ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("dune", "dune-project"):
            shutil.copyfile(ROOT / name, work / name)
        (work / "dev").mkdir()
        for name in ("gen-target.py", "dunecho.sh"):
            shutil.copyfile(ROOT / "dev" / name, work / "dev" / name)

        def build():
            result = run(work, "zsh", "dev/dunecho.sh", "build", timeout=900)
            require(result.returncode == 0 and "OK build" in result.stdout,
                    f"scratch compiler: {result.stdout}{result.stderr}")

        def cli():
            return run(ROOT, sys.executable, "-P", ROOT / "test/lan_axioms.py",
                       "--driver", work / "_build/default/bin/lanyard.exe")

        build()
        baseline = cli()
        require(baseline.returncode == 0 and "LAN-AXIOMS OK" in baseline.stdout,
                f"scratch positive control: {baseline}")
        for name, before, after, gate, diagnostic in mutations:
            require(source.count(before) == 1, f"mutation anchor differs: {name}")
            (work / "surface/axioms.ml").write_text(source.replace(before, after))
            build()
            result = cli() if gate == "cli" else run(work, work / "_build/default/test/lan_axioms_report.exe")
            require(result.returncode == 1 and diagnostic in result.stderr,
                    f"survived or wrong failure: {name}: {result}")
            print(f"LAN-AXIOMS-MUTATIONS {name}=KILLED")
        (work / "surface/axioms.ml").write_text(source)
        build()
        restored = cli()
        report = run(work, work / "_build/default/test/lan_axioms_report.exe")
        require(restored.returncode == 0 and report.returncode == 0, "restored positive control failed")
    print(f"LAN-AXIOMS-MUTATIONS OK killed={len(mutations)} restored=GREEN")


if __name__ == "__main__":
    main()
