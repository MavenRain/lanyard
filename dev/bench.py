#!/usr/bin/env python3
"""M0 timing: the S2 timer, the S4 denominator, and informational R3 reports."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
RUNS = 5
SIZES = (100, 500, 1000)
DENOMINATOR_SHA256 = "ba1293a3f8970531ab32490fc20d55fd8a04cb16ca7f45d2ca0956075f4bf03d"
ARC = (
    "REPORTED: one Arc clone and its matching drop costs 22.4209 ns and one Rc "
    "clone and its matching drop costs 4.1950 ns, so the price of the atomic is "
    "18.2259 ns per clone, median of five runs at 20000000 clones, NOISY at "
    "load average 16.85;  this number is reported at M0 and it binds at no milestone."
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit(rows):
    """Unrounded ordinary least squares; a constant response has no R squared."""
    xs = [row["kloc"] for row in rows]
    ys = [row["median_ms"] for row in rows]
    if len(xs) < 2 or not all(math.isfinite(v) for v in xs + ys):
        raise ValueError("fit needs at least two finite observations")
    xmean, ymean = statistics.mean(xs), statistics.mean(ys)
    sxx = sum((x - xmean) ** 2 for x in xs)
    if sxx == 0:
        raise ValueError("fit needs distinct input sizes")
    slope = sum((x - xmean) * (y - ymean) for x, y in zip(xs, ys)) / sxx
    fixed = ymean - slope * xmean
    sst = sum((y - ymean) ** 2 for y in ys)
    sse = sum((y - fixed - slope * x) ** 2 for x, y in zip(xs, ys))
    return {"F_ms": fixed, "m_ms_per_kloc": slope,
            "r_squared": None if sst == 0 else 1 - sse / sst,
            "points": len(xs)}


def ratios(numerator, denominator, kloc):
    total = denominator["F_ms"] + denominator["m_ms_per_kloc"] * kloc
    slope = denominator["m_ms_per_kloc"]
    return {
        "kloc": kloc,
        "total": ((numerator["F_ms"] + numerator["m_ms_per_kloc"] * kloc)
                  / total if total > 0 else None),
        "slope": numerator["m_ms_per_kloc"] / slope if slope > 0 else None,
    }


def summary(samples):
    return {"samples_ms": samples, "median_ms": statistics.median(samples),
            "min_ms": min(samples), "max_ms": max(samples), "runs": len(samples)}


def execute(argv, cwd, env=None, capture=False):
    # A timeout with discarded pipes uses polling in Popen.wait and biases
    # short samples. Timed commands use the blocking wait of the S2 timer.
    proc = subprocess.run(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                          stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
                          text=True, timeout=120 if capture else None)
    if proc.returncode != 0:
        raise ValueError(f"child exit={proc.returncode}: {shlex.join(argv)}: "
                         + (proc.stderr or "")[-1200:].strip())
    return proc.stdout


def shell_command(argv):
    # Preserve the S2 shell startup and quoting, including paths with spaces.
    return ["/bin/zsh", "-f", "-c", shlex.join([str(arg) for arg in argv])]


def sample(command, loads):
    """Preparation and load sampling are outside the perf_counter interval."""
    command["prepare"]()
    loads.append(list(os.getloadavg()))
    start = time.perf_counter_ns()
    execute(command["argv"], command["cwd"], command.get("env"))
    elapsed = (time.perf_counter_ns() - start) / 1_000_000.0
    loads.append(list(os.getloadavg()))
    return elapsed


def measure(command, loads):
    return {**command["metadata"],
            **summary([sample(command, loads) for _ in range(RUNS)])}


def corpus(lines):
    # Every line is a checked declaration printed by --target, with no padding.
    return "".join(f"def bench{i} : Nat -> Nat := fun (x : Nat) => natAdd x {i}\n"
                   for i in range(lines))


def compiler_commands(binary, scratch):
    commands = []
    for lines in SIZES:
        source = scratch / f"native-{lines}.lan"
        source.write_text(corpus(lines), encoding="utf-8")
        for mode, args in (("check", ["check"]), ("emit-target", ["emit", "--target"])):
            commands.append({
                "argv": shell_command([binary, *args, source]), "cwd": ROOT,
                "prepare": lambda: None,
                "metadata": {"name": f"{mode}-{lines}", "mode": mode,
                             "lines": lines, "kloc": lines / 1000,
                             "source_sha256": digest(source)},
            })
    todo = scratch / "todo.lan"
    todo.write_bytes((ROOT / "corpus/m0/todo.lan").read_bytes())
    output = scratch / "todo-crate"

    def clean_crate():
        if output.exists():
            shutil.rmtree(output)

    for mode, args, prepare in (
        ("todo-check", ["check"], lambda: None),
        ("todo-crate", ["emit", "--crate", output, "--print-model", "Todo"], clean_crate),
    ):
        commands.append({
            "argv": shell_command([binary, *args, todo]), "cwd": ROOT,
            "prepare": prepare,
            "metadata": {"name": mode, "mode": mode,
                         "lines": len(todo.read_bytes().splitlines()),
                         "source_sha256": digest(todo)},
        })
    return commands


def load_denominator():
    path = ROOT / "dev/spikes/denominators.json"
    contents = path.read_bytes()
    if hashlib.sha256(contents).hexdigest() != DENOMINATOR_SHA256:
        raise ValueError("frozen denominator digest differs from S4")
    return json.loads(contents)


def run(binary, refit_go):
    frozen = load_denominator()
    binary_hash = digest(binary)
    with tempfile.TemporaryDirectory(prefix="lanyard-bench-") as directory:
        scratch = Path(directory)
        compiler = compiler_commands(binary, scratch)
        go_commands, go_version = [], frozen["tools"]["go"]
        if refit_go:
            # -P omits the script directory; load this sibling by its exact path.
            import importlib.util
            spec = importlib.util.spec_from_file_location("lanyard_bench_go", ROOT / "dev/bench_go.py")
            go = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(go)
            go_commands, go_version = go.prepare(scratch / "go", frozen, execute)
        commands = compiler + go_commands
        # One untimed warm-up per command, including the Go dependency builds.
        for command in commands:
            command["prepare"]()
            execute(command["argv"], command["cwd"], command.get("env"))
        loads = [list(os.getloadavg())]
        started = time.time()
        start = time.perf_counter()
        observations = [measure(command, loads) for command in commands]
        elapsed = time.perf_counter() - start
        finished = time.time()
        if digest(binary) != binary_hash:
            raise ValueError("compiler changed during the benchmark")
    rows = observations[:len(compiler)]
    fits = {mode: fit([row for row in rows if row["mode"] == mode])
            for mode in ("check", "emit-target")}
    go_rows = observations[len(compiler):]
    denominator = fit(go_rows) if refit_go else {
        key: frozen[key] for key in ("F_ms", "m_ms_per_kloc", "r_squared", "points")}
    noisy = any(load[0] > 4 for load in loads)
    return {
        "version": 1, "status": "REPORTED", "binding": False,
        "method": {"timer": "perf_counter_ns", "warmups": 1, "runs": RUNS,
                   "compiler_shell": "/bin/zsh -f -c",
                   "emit_scope": "check plus complete native target module; no Cargo"},
        "compiler_sha256": binary_hash,
        "host": {"platform": platform.platform(), "cpu_count": os.cpu_count()},
        "window": {"started_unix": started, "finished_unix": finished,
                   "elapsed_seconds": elapsed,
                   "same_minute": refit_go and elapsed <= 60},
        "loadavg": loads, "noisy": noisy,
        "observations": rows, "fits": fits,
        "denominator": {"source": "same-run-refit" if refit_go else "frozen-S4",
                        "sha256": DENOMINATOR_SHA256, "go": go_version,
                        "fit": denominator, "observations": go_rows,
                        "noisy": noisy if refit_go else frozen["noisy"]},
        "ratios": {mode: ratios(value, denominator, 1.0) for mode, value in fits.items()},
        "arc": ARC,
    }


def number(value):
    return "UNAVAILABLE" if value is None else f"{value:.6f}"


def report(doc):
    lines = ["M0-TIME status=REPORTED binding=false",
             "METHOD warmups=1 runs=5 timer=perf_counter_ns emit=check+target-module",
             f"LOAD max_1m={max(row[0] for row in doc['loadavg']):.2f} "
             f"status={'NOISY' if doc['noisy'] else 'QUIET'}",
             f"WINDOW seconds={doc['window']['elapsed_seconds']:.3f} "
             f"same_minute={str(doc['window']['same_minute']).lower()}"]
    for row in doc["observations"]:
        lines.append(f"BENCH {row['name']} lines={row['lines']} "
                     f"median_ms={row['median_ms']:.3f} min_ms={row['min_ms']:.3f} "
                     f"max_ms={row['max_ms']:.3f} runs={row['runs']}")
    denominator = doc["denominator"]
    for name, value in {**doc["fits"], "go": denominator["fit"]}.items():
        lines.append(f"FIT {name} F_ms={number(value['F_ms'])} "
                     f"m_ms_per_kloc={number(value['m_ms_per_kloc'])} "
                     f"r_squared={number(value['r_squared'])} points={value['points']}")
    lines.append(f"DENOMINATOR source={denominator['source']} sha256={denominator['sha256']} "
                 f"status={'NOISY' if denominator['noisy'] else 'QUIET'}")
    for name, value in doc["ratios"].items():
        lines.append(f"RATIO {name} kloc={value['kloc']:.3f} total={number(value['total'])} "
                     f"slope={number(value['slope'])} status=REPORTED")
    return "\n".join([*lines, doc["arc"]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, default=ROOT / "_build/default/bin/lanyard.exe")
    parser.add_argument("--refit-go", action="store_true", help="remeasure all 13 frozen Go packages")
    parser.add_argument("--output", type=Path, help="write raw samples and provenance to a new JSON file")
    args = parser.parse_args()
    try:
        if args.output is not None:
            if args.output.exists() or args.output.is_symlink():
                raise ValueError("output must be a new file")
            # The destination is checked before the window, not after it.
            if not (args.output.parent.is_dir() and os.access(args.output.parent, os.W_OK)):
                raise ValueError("output directory must exist and be writable")
        doc = run(args.compiler.resolve(), args.refit_go)
        if args.output is not None:
            # Serialize first: a rejected value leaves no partial file behind.
            contents = json.dumps(doc, indent=2, allow_nan=False) + "\n"
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(contents)
        print(report(doc))
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"M0-TIME ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
