"""Check the Rust erasure boundary and its carried compatibility path."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"

def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT,
                          text=True, capture_output=True, timeout=30)

def require(condition, message):
    if not condition:
        print(f"LAN-ERASE-CLI FAIL: {message}", file=sys.stderr)
        sys.exit(1)

todo = run(DRIVER, "check", "--erased", "examples/m0-todo.lan")
require(todo.returncode == 0 and not todo.stderr,
        f"erased driver rc={todo.returncode}: {todo.stderr}")
require("RForeign Todo_create [RCall item []; RClone (RVar 0)]" in todo.stdout,
        "Todo create or its arguments disappeared")
require("RLam request$0" in todo.stdout and "RTag mu<Cli>" in todo.stdout,
        "signature construction or continuation disappeared")
require(not re.search(r"\b(?:KErased|KApp|KTail|KClos)\b", todo.stdout),
        "legacy runtime nodes reached Rust IR")

original = run("git", "show", "046689a:lib/erase.ml")
require(original.returncode == 0 and original.stdout == (ROOT / "lib/erase_kan.ml").read_text(),
        "carried eraser differs from the fork")
quantity = re.compile(r"let quantity_runtime\b.*?(?=\n\n)", re.S)
fork_quantity = quantity.search(original.stdout)
current_quantity = quantity.search((ROOT / "lib/erase.ml").read_text())
require(fork_quantity is not None and current_quantity is not None,
        "quantity_runtime missing")
require(fork_quantity.group() == current_quantity.group(), "quantity_runtime changed")
legacy = run(DRIVER, "check", "--erased", "examples/m0-spine.kan")
require(legacy.returncode == 0 and not legacy.stderr
        and re.search(r"\b(?:KErased|KApp|KTail|KClos)\b", legacy.stdout),
        "carried erasure command failed")

with tempfile.TemporaryDirectory(prefix="lanyard-rir-") as directory:
    source = Path(directory) / "unknown.lan"
    source.write_text("axiom mystery : Nat -> Nat def main : Nat := mystery 1\n")
    check = run(DRIVER, "check", source)
    erased = run(DRIVER, "check", "--erased", source)
    require(check.returncode == 0 and erased.returncode == 1 and not erased.stdout
            and "Rust target metadata missing: mystery" in erased.stderr,
            "missing print metadata did not refuse after successful checking")

nodes = re.search(r"type rtm =(.*?)\nand rbranch", (ROOT / "lib/rir.ml").read_text(), re.S)
require(nodes is not None and len(re.findall(r"^  \| R", nodes.group(1), re.M)) == 14,
        "Rust IR node count differs from fourteen")
print("LAN-ERASE-CLI OK")
