"""Run the seven M0 legs and retain their outputs, including pending rulings."""
import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
TRUST_SPEC = importlib.util.spec_from_file_location("trusted_inventory", ROOT / "dev/trusted-inventory.py")
TRUST = importlib.util.module_from_spec(TRUST_SPEC)
TRUST_SPEC.loader.exec_module(TRUST)
PENDING_TRUST = "A_rir, A_emit, A_sig and trusted-file scope require user rulings"
LEG_NAMES = ("R0-COUNT", "R0-TARGET", "TARGET-PIN", "TRUSTED-LINES",
             "KERNEL-CARRY", "EMIT-DIFF", "M0-TIME")
# The eraser prints one line for each erased foreign type. These two lines
# pin the corpus result, so a driver that erases wrongly cannot pass.
ERASE_MARKERS = ("erased Db", "erased Todo")
# The pending M0 verdict a stage runner accepts, read from report.json only.
PENDING_SUMMARY = {"status": "PENDING", "exit_code": 2, "passed_legs": 6,
                   "pending_legs": 1, "failed_checks": 0}


@dataclass(frozen=True)
class Check:
    name: str
    argv: tuple
    markers: tuple = ()
    timeout: int = 120
    expected: bytes | Path | None = None
    expected_stderr: bytes | None = None
    inventory: Path | None = None


def drain(child, grace):
    """Read what a killed child left. A surviving descendant holds the pipes
    open, so this read has its own bound. The leg then reports the deadline."""
    try:
        return child.communicate(timeout=grace)
    except subprocess.TimeoutExpired as expired:
        child.kill()
        for stream in (child.stdout, child.stderr):
            if stream is not None:
                stream.close()
        return getattr(expired, "stdout", None) or b"", getattr(expired, "stderr", None) or b""


def invoke(check, root, grace=30):
    """A deadline stops the complete child process group, including compilers."""
    try:
        child = subprocess.Popen(check.argv, cwd=root, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True)
    except OSError as error:
        return 127, b"", str(error).encode(), "launch failed"
    try:
        stdout, stderr = child.communicate(timeout=check.timeout)
        return child.returncode, stdout, stderr, ""
    except subprocess.TimeoutExpired:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        stdout, stderr = drain(child, grace)
        return 124, stdout, stderr, "deadline exceeded"


def run_check(check, root, output):
    started = time.monotonic()
    try:
        if check.inventory is not None:
            # Repeated mutation checks reuse their output directory. Remove only
            # this check's prior report, so a silent child cannot reuse old evidence.
            check.inventory.unlink(missing_ok=True)
    except OSError as error:
        code, stdout, stderr, reason = 1, b"", str(error).encode(), "inventory cleanup failed"
    else:
        code, stdout, stderr, reason = invoke(check, root)
    markers = all(marker.encode() in stdout.splitlines() for marker in check.markers)
    try:
        expected = check.expected.read_bytes() if isinstance(check.expected, Path) else check.expected
        exact = ((expected is None or stdout == expected)
                 and (check.expected_stderr is None or stderr == check.expected_stderr))
    except OSError as error:
        exact, reason = False, f"golden unavailable: {error}"
    good = code == 0 and markers and exact
    inventory_record = None
    if good and check.inventory is not None:
        try:
            data = TRUST.regular_bytes(check.inventory.parent, check.inventory.name)
            measured = json.loads(data)
            current = TRUST.inventory(root)
            digest = hashlib.sha256(data).hexdigest()
            marker = f"TRUSTED-INVENTORY files={len(current['files'])} sha256={digest}".encode()
            if measured != current or current["status"] != "PENDING" or marker not in stdout.splitlines():
                raise ValueError("inventory differs from the measured compiler sources or stdout hash")
            inventory_record = {"path": check.inventory.name, "sha256": digest}
        except (OSError, ValueError) as error:
            good, reason = False, f"trusted inventory unavailable: {error}"
    if not reason and not good:
        reason = "child failed" if code else "required output differs"
    state = "PASS" if good else "FAIL"
    if good and check.name == "TRUSTED-LINES":
        # Complete measurements cannot discharge the unruled whole-base ceiling.
        state, reason = "PENDING", PENDING_TRUST
    streams = {}
    for name, content in (("stdout", stdout), ("stderr", stderr)):
        filename = f"{check.name}.{name}"
        (output / filename).write_bytes(content)
        streams[name] = {"path": filename, "sha256": hashlib.sha256(content).hexdigest()}
    row = {"name": check.name, "status": state, "exit_code": code,
           "command": list(check.argv), "reason": reason, "streams": streams,
           "elapsed_ms": (time.monotonic() - started) * 1000}
    if inventory_record is not None:
        row["inventory"] = inventory_record
    print(f"M0 {check.name} {state}" + (f": {reason}" if reason else ""), flush=True)
    if check.name in ("TRUSTED-LINES", "M0-TIME"):
        print(stdout.decode(errors="replace"), end="", flush=True)
    if not good:
        print(f"M0-DETAIL {output / (check.name + '.stdout')} "
              f"{output / (check.name + '.stderr')}", flush=True)
    return row


def seven_legs(root, output):
    def shell(name, script, *markers):
        return Check(name, ("zsh", str(root / "dev" / script)), markers)

    return (
        shell("R0-COUNT", "r0-count.sh", "R0-COUNT OK"),
        shell("R0-TARGET", "r0-target.sh", "R0-TARGET OK"),
        shell("TARGET-PIN", "target-pin.sh", "TARGET-PIN PIN OK libraries=2",
              "TARGET-PIN ANCHOR OK sites=4", "TARGET-PIN DIFF OK signatures=2 anchors=4",
              "TARGET-PIN OK"),
        Check("TRUSTED-LINES", ("zsh", str(root / "dev/trusted-lines.sh"), str(root),
                                "--output", str(output / "trusted-inventory.json")),
              ("TRUSTED-LINES OK", "TRUSTED-INVENTORY PENDING"), expected_stderr=b"",
              inventory=output / "trusted-inventory.json"),
        shell("KERNEL-CARRY", "kernel-carry.sh", "KERNEL-CARRY OK"),
        Check("EMIT-DIFF", (sys.executable, "-P", str(root / "dev/emit-diff.py")),
              ("EMIT-DIFF OK files=2 normalization=none",), 360),
        Check("M0-TIME", (sys.executable, "-P", str(root / "dev/bench.py"),
                          "--refit-go", "--output", str(output / "timings.json")),
              ("M0-TIME status=REPORTED binding=false",), 1200),
    )


def summarize(legs, support):
    failed = sum(row["status"] == "FAIL" for row in legs + support)
    pending = sum(row["status"] == "PENDING" for row in legs + support)
    complete = tuple(row["name"] for row in legs) == LEG_NAMES
    state = "FAIL" if failed or not complete else "PENDING" if pending else "PASS"
    return {"status": state, "exit_code": 1 if state == "FAIL" else 2 if pending else 0,
            "complete": complete,
            "passed_legs": sum(row["status"] == "PASS" for row in legs),
            "pending_legs": sum(row["status"] == "PENDING" for row in legs),
            "failed_checks": failed}


def run(root, output):
    build = Check("BUILD", ("zsh", str(root / "dev/dunecho.sh"), "build"),
                  ("OK build: 0 errors, 0 warnings",), 900)
    support = [run_check(build, root, output)]
    legs = []
    if support[0]["status"] == "PASS":
        driver = str(root / "_build/default/bin/lanyard.exe")
        fixture = str(root / "corpus/m0/todo.lan")
        support.append(run_check(Check("M0-CHECK", (driver, "check", fixture),
                                       expected=b""), root, output))
        support.append(run_check(Check("M0-ERASE", (driver, "check", "--erased", fixture),
                                       ERASE_MARKERS), root, output))
        axioms = root / "corpus/m0/axioms.txt"
        support.append(run_check(Check("M0-AXIOMS", (driver, "axioms", fixture), expected=axioms), root, output))
        support.append(run_check(Check("HOUSE", ("zsh", str(root / "dev/house.sh")),
                                       ("HOUSE OK",)), root, output))
        # Every independent leg runs after a successful build, including when
        # an earlier assertion fails or the trust allowance is pending.
        legs = [run_check(check, root, output) for check in seven_legs(root, output)]
    summary = summarize(legs, support)
    report = {"format": 1, "root": str(root), "summary": summary,
              "legs": legs, "support": support, "m0_exit": "not-stamped",
              "pending_rulings": [PENDING_TRUST]}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"M0-GATES {summary['status']} passed={summary['passed_legs']}/7 "
          f"pending={summary['pending_legs']} failed={summary['failed_checks']}")
    print("M0-EXIT not-stamped")
    print(f"M0-REPORT {output / 'report.json'}")
    return summary["exit_code"]


def verify_stage_log(log):
    """Confirm the pending M0 ruling from report.json, never from a stdout row.

    A child stream is replayed into the gate's stdout, so a marker row can be
    forged. The report path is the LAST `M0-REPORT ` row: that row is always
    the gate's own final row. Return a pair of a verdict and a message."""
    try:
        text = Path(log).read_text(errors="replace")
    except OSError as error:
        return False, f"unreadable gate log: {error}"
    rows = [line for line in text.splitlines() if line.startswith("M0-REPORT ")]
    if not rows:
        return False, "the gate log holds no M0-REPORT row"
    report = Path(rows[-1][len("M0-REPORT "):].strip())
    try:
        summary = json.loads(report.read_text())["summary"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        return False, f"unreadable report {report}: {error}"
    found = {key: summary.get(key) for key in PENDING_SUMMARY}
    if found != PENDING_SUMMARY:
        return False, f"report {report} is not the pending ruling: {found}"
    return True, str(report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new directory for per-check logs and JSON")
    parser.add_argument("--verify-stage-log", type=Path,
                        help="read a saved gate log and confirm the pending report")
    args = parser.parse_args()
    if args.verify_stage_log is not None:
        good, message = verify_stage_log(args.verify_stage_log)
        if not good:
            print(f"M0-VERIFY FAIL: {message}", file=sys.stderr)
        return 0 if good else 1
    try:
        if args.output is None:
            work = ROOT / ".gatework"
            work.mkdir(exist_ok=True)
            output = Path(tempfile.mkdtemp(prefix="m0.", dir=work))
        else:
            output = args.output.resolve()
            output.mkdir()
        return run(ROOT, output)
    except (OSError, ValueError) as error:
        print(f"M0-GATES ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
