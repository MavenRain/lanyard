"""Require named behavioral failures from four isolated request mutations."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
UNIT = ["_build/default/test/lan_request.exe"]
CLI = [sys.executable, "-P", "test/lan_request.py"]
MUTATIONS = [
    ("redirect-status", "rust/run_http.ml", "HTTP/1.1 303 See Other", "HTTP/1.1 307 See Other",
     UNIT, "redirect bytes:"),
    ("header-injection", "rust/run_http.ml", "when uri_character character",
     "when uri_character character || List.mem character ['\\r'; '\\n']",
     UNIT, "header injection refused:"),
    ("context-handle", "rust/run_store.ml", "Ok (Database id, store)",
     "Ok (Database (id + 1), store)", CLI + ["Request.test_context_database_alias"],
     "FAIL: test_context_database_alias"),
    ("foreign-metadata", "rust/run_store.ml", "not (List.mem row catalog.constants)",
     "false && not (List.mem row catalog.constants)", UNIT, "foreign metadata:"),
]


def run(root, command, timeout=120):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=timeout)


def build(root):
    result = run(root, ["zsh", "dev/dunecho.sh", "build"], timeout=None)
    if result.returncode != 0:
        sys.exit(f"LAN-REQUEST-MUTATIONS build failed: {result.stdout}{result.stderr}")


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="request-mutations-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        build(scratch)
        for command in (UNIT, CLI):
            result = run(scratch, command)
            if result.returncode != 0:
                sys.exit(f"LAN-REQUEST-MUTATIONS clean control failed: {result.stdout}{result.stderr}")
        print("LAN-REQUEST-MUTATIONS CONTROL OK", flush=True)
        killed = 0
        for name, relative, before, after, command, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-REQUEST-MUTATIONS {name}: expected exactly one source site")
            path.write_text(original.replace(before, after))
            build(scratch)
            result = run(scratch, command)
            path.write_text(original)
            if result.returncode != 1 or failure not in result.stderr:
                sys.exit(f"LAN-REQUEST-MUTATIONS {name} survived: {result.stdout}{result.stderr}")
            killed += 1
            print(f"LAN-REQUEST-MUTATIONS {name} KILLED", flush=True)
        print(f"LAN-REQUEST-MUTATIONS OK killed={killed}/{len(MUTATIONS)}")


if __name__ == "__main__":
    main()
