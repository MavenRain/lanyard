"""Check classified disclosure, counts, provenance and refusal boundaries."""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        sys.exit(f"LAN-AXIOMS FAIL: {message}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--driver", type=Path, default=ROOT / "_build/default/bin/lanyard.exe")
    args = parser.parse_args()
    observations, refusals = [], []

    def run(*arguments):
        command = [str(args.driver), *map(str, arguments)]
        child = subprocess.Popen(command, cwd=ROOT, text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deadline = time.monotonic() + 120
        while child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        expired = child.poll() is None
        if expired:
            child.kill()
        stdout, stderr = child.communicate()
        require(not expired, f"timeout: {arguments}")
        return subprocess.CompletedProcess(command, child.returncode, stdout, stderr)

    def report(path, foreign, definitions):
        result = run("axioms", path)
        require(result.returncode == 0 and result.stderr == "", f"{path}: {result}")
        text = result.stdout
        require(re.match(r"AXIOMS scope=checked-module target-sha256=[0-9a-f]{64}\n", text),
                "missing compiled catalog identity")
        entries = re.findall(r"^(Framework|Foreign|Classical|Div) (\S+) : (.+)$", text, re.M)
        require(len(entries) == foreign + 1, "unexpected class members")
        require(entries[0] == ("Framework", "imax_zero", "imax l zero = zero"),
                "framework assumption differs")
        names = [name for class_, name, _statement in entries if class_ == "Foreign"]
        require(len(names) == foreign and names == sorted(set(names)),
                f"foreign membership or ordering: {names}")
        require("Nat" not in names and "natAdd" not in names, "ambient primitive leaked into count")
        require(text.endswith(f"COUNT Framework=1\nCOUNT Foreign={foreign}\n"
                              "COUNT Classical=0\nCOUNT Div=0\n"
                              f"AXIOMS total={foreign + 1}\n"
                              f"AXIOM-RATIO constants={foreign} definitions={definitions} status=REPORTED\n"),
                "class totals or ratio inputs differ")
        observations.append(str(path))
        return text, names

    todo = ROOT / "corpus/m0/todo.lan"
    text, names = report(todo, 17, 3)
    require(text == (ROOT / "corpus/m0/axioms.txt").read_text(), "Todo report golden drift")
    require("Todo_create" in names and "Todo_get_by_id" in names and "Todo" not in names,
            "model operations or product classification differs")
    require("[schema=Model.create]" in text and "[schema=Model.get_by_id]" in text,
            "missing model schema provenance")
    require(run("axioms", todo).stdout == text, "repeated report differs")
    legacy = run("axioms", "--names", todo)
    require(legacy.returncode == 0 and legacy.stderr == ""
            and legacy.stdout.splitlines() == [
                "Db", "Deferred", "toasty_Error", "Cx", "Uri", "Response", "SeeOther",
                "Form", "topcoat_Error", "Db_connect", "Db_push_schema", "Model_create",
                "Model_get_by_id", "topcoat_db", "topcoat_see_other", "Todo_create", "Todo_get_by_id"],
            "legacy names or declaration order differ")
    observations.append("legacy Todo names")

    with tempfile.TemporaryDirectory(prefix="lanyard-axioms-") as directory:
        source = Path(directory) / "module.lan"
        for content, foreign, definitions in [
            ("", 15, 0),
            ("def main : Nat := 1\n", 15, 1),
            ("model Zed with | id : Nat end\nmodel Alpha with | id : Nat end\n"
             "def Alias : Type 0 := Zed\n", 19, 3),
            ("def ghost_create : Nat := 7\ndef propext : Nat := 9\n", 15, 2),
            ("signature Ops : Nat with | Ping : Nat end\n", 15, 0),
            ("mu Tree : Type 0 := | leaf : Tree\n"
             "def rec size : Tree -> Nat := fun (t : Tree) => "
             "match t as self in Tree return Nat with | leaf => 1\n", 15, 1),
        ]:
            source.write_text(content)
            report(source, foreign, definitions)
        for name in ("unknown", "Ghost_create", "propext", "Classical_choice"):
            source.write_text(f"axiom {name} : Prop\n")
            result = run("axioms", source)
            require(result.returncode == 1 and result.stdout == ""
                    and f"axiom disclosure: unclassified postulate {name}" in result.stderr,
                    f"unclassified postulate was hidden or mislabeled: {result}")
            names_result = run("axioms", "--names", source)
            require(names_result.returncode == 0 and names_result.stderr == ""
                    and name in names_result.stdout.splitlines(), "source postulate names unavailable")
            refusals.append(name)
        source.write_text("def bad : Nat := ()\n")
        result = run("axioms", source)
        require(result.returncode == 1 and result.stdout == "" and result.stderr != "",
                "unchecked source produced a report")
        refusals.append("type error")
        missing = run("axioms", Path(directory) / "missing.lan")
        require(missing.returncode == 64 and missing.stdout == "" and "cannot read" in missing.stderr,
                "missing-file boundary differs")
        refusals.append("missing file")

    for arguments in ((), ("--names",), ("--unknown",), (todo, todo), ("--names", todo, todo)):
        result = run("axioms", *arguments)
        require(result.returncode == 64 and result.stdout == "" and "usage:" in result.stderr,
                f"malformed arguments accepted: {arguments}")
        refusals.append(str(arguments))
    for path, expected in (("test/fixtures/b08-axiom-disclosure.kan", "Bit\n"),
                           ("examples/m0-spine.kan", "")):
        result = run("axioms", path)
        require(result.returncode == 0 and result.stdout == expected and result.stderr == "",
                f"carried .kan disclosure changed: {path}")
        observations.append(path)
    print(f"LAN-AXIOMS OK observations={len(observations)} refusals={len(refusals)}")


if __name__ == "__main__":
    main()
