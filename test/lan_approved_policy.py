"""Exercise the approved mutation path in a disposable checkout only.

The probe is manual. It clones the repository and runs the gate mutation
harness, so its bound is the sum of the harness allowances, not a guess. A
subprocess.TimeoutExpired traceback means the machine is too slow for the
probe. It is not a policy failure. Run the probe again on an idle machine.
"""
from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
POLICY = "dev/trusted-policy.json"
# The mutation harness builds the scratch compiler at five sites and allows
# 900 s for each build. The budget holds six builds, one spare, and adds
# 1200 s for the gate legs and the suites that run between the builds:
# 6 * 900 + 1200 = 6600 s.
BUDGET = 6 * 900 + 1200


def git(*arguments):
    return subprocess.run(["git", "-C", str(ROOT), *arguments],
                          check=True, capture_output=True, timeout=60).stdout


def main():
    original = (ROOT / POLICY).read_bytes()
    with tempfile.TemporaryDirectory(prefix="lanyard-approved-policy-") as temporary:
        work = Path(temporary) / "repo"
        subprocess.run(["git", "clone", "--shared", str(ROOT), str(work)],
                       check=True, timeout=60)
        changes = git("diff", "HEAD", "--binary")
        if changes:
            subprocess.run(["git", "-C", str(work), "apply", "-"],
                           input=changes, check=True, timeout=60)
        for raw in git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
            if raw:
                name = raw.decode()
                destination = work / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                # copy2 keeps the mode. A tracked change arrives through
                # git apply with its mode, so an untracked file keeps its
                # executable bit too.
                shutil.copy2(ROOT / name, destination)
        # Populate the generated signature before measuring the disposable tree.
        # Preparation has its own 900 s build bound, outside the harness budget.
        subprocess.run(["zsh", "dev/dunecho.sh", "build"], cwd=work,
                       check=True, timeout=900)
        spec = importlib.util.spec_from_file_location("approved_inventory", work / "dev/trusted-inventory.py")
        inventory = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inventory)
        measured = {group["name"]: group for group in inventory.inventory(work)["groups"]}
        proposal = json.loads(original)
        # The fixture approves exactly these copied bytes. The real proposal
        # keeps its original limits, source roster, status and ruling.
        for group in proposal["groups"]:
            group["files"] = measured[group["name"]]["files"]
            group["limit"] = measured[group["name"]]["lines"] if group["scope"] == "included" else None
        proposal.update(status="APPROVED", ruling="temporary test fixture, not a user ruling")
        (work / POLICY).write_text(json.dumps(proposal, indent=2) + "\n")
        subprocess.run([sys.executable, "-P", "test/lan_m0_gate_mutations.py"],
                       cwd=work, check=True, timeout=BUDGET)
    if (ROOT / POLICY).read_bytes() != original:
        sys.exit("LAN-APPROVED-POLICY FAIL: source policy changed")
    print("LAN-APPROVED-POLICY OK temporary-approval=1 source-policy=unchanged")


if __name__ == "__main__":
    main()
