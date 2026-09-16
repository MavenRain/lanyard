"""Require HTML escaping and response failures with restored build controls."""
from contextlib import ExitStack
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
MUTATIONS = [
    ("skip-delimiter-escape", "rust/text_ops.ml", "'<' -> \"&lt;\"", "'<' -> \"<\"", "escape delimiters:"),
    ("skip-entity-escape", "rust/text_ops.ml", "'&' -> \"&amp;\"", "'&' -> \"&\"", "escape existing entities:"),
    ("wrong-content-type", "rust/run_http.ml", 'content_response "text/html"', 'content_response "text/plain"', "html raw markup:"),
    ("skip-html-validation", "rust/text_ops.ml", 'not (String.is_valid_utf_8 text) then Error (Error.Mismatch "invalid UTF-8 in HTML text")',
     'false then Error (Error.Mismatch "invalid UTF-8 in HTML text")', "escape public UTF-8 guard:"),
    ("skip-effect-contract", "rust/text_ops.ml", "entry.effects = effects operation && row.effects = entry.effects",
     "true", "Html.text metadata effects:"),
]


def check(root, failure=None):
    build = subprocess.run(["zsh", "dev/dunecho.sh", "build"], cwd=root,
                           text=True, capture_output=True, timeout=900)
    if build.returncode != 0:
        sys.exit(f"LAN-HTML-MUTATIONS build failed: {build.stdout}{build.stderr}")
    result = subprocess.run(["_build/default/test/lan_html.exe"], cwd=root,
                            text=True, capture_output=True, timeout=60)
    if result.returncode != (0 if failure is None else 1) or (failure is not None and failure not in result.stderr):
        sys.exit(f"LAN-HTML-MUTATIONS expected {failure or 'passing control'}: {result.stdout}{result.stderr}")


def main():
    work = ROOT / ".gatework"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="html-mutations-", dir=work) as directory:
        scratch = Path(directory) / "root"
        shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(
            ".git", "_build", ".gatework", ".kanon-exec", ".kanon-wait", "vendor", "__pycache__"))
        (scratch / "dune-workspace").write_text((scratch / "dune-project").read_text().splitlines()[0] + "\n")
        check(scratch)
        print("LAN-HTML-MUTATIONS CONTROL OK", flush=True)
        for name, relative, before, after, failure in MUTATIONS:
            path = scratch / relative
            original = path.read_text()
            if original.count(before) != 1:
                sys.exit(f"LAN-HTML-MUTATIONS {name}: expected exactly one source site")
            with ExitStack() as restore:
                restore.callback(path.write_text, original)
                path.write_text(original.replace(before, after))
                check(scratch, failure)
            print(f"LAN-HTML-MUTATIONS {name} KILLED", flush=True)
        check(scratch)
    print(f"LAN-HTML-MUTATIONS OK killed={len(MUTATIONS)}/{len(MUTATIONS)} restored=GREEN")


if __name__ == "__main__":
    main()
