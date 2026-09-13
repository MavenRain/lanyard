#!/usr/bin/env python3
"""Timing instrument observations, independent of wall-clock speed."""

import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "dev" / (name + ".py"))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


bench = module("bench")
go = module("bench_go")


class Statistics(unittest.TestCase):
    def test_fit_known_line(self):
        rows = [{"kloc": x, "median_ms": 7 + 3 * x} for x in (1, 2, 8, 16)]
        self.assertEqual(bench.fit(rows), {
            "F_ms": 7, "m_ms_per_kloc": 3, "r_squared": 1, "points": 4})

    def test_invalid_fit(self):
        for rows in ([], [{"kloc": 1, "median_ms": 1}] * 2,
                     [{"kloc": float("nan"), "median_ms": 1}] * 2):
            with self.assertRaises(ValueError):
                bench.fit(rows)

    def test_constant_fit(self):
        result = bench.fit([{"kloc": x, "median_ms": 9} for x in (1, 2, 3)])
        self.assertEqual(result["m_ms_per_kloc"], 0)
        self.assertIsNone(result["r_squared"])

    def test_median_retains_outliers(self):
        row = bench.summary([1000, 2, 5, 1, 3])
        self.assertEqual(row["median_ms"], 3)
        self.assertEqual(row["max_ms"], 1000)
        self.assertEqual(row["samples_ms"], [1000, 2, 5, 1, 3])

    def test_ratios_use_same_size(self):
        value = bench.ratios({"F_ms": 2, "m_ms_per_kloc": 3},
                             {"F_ms": 4, "m_ms_per_kloc": 6}, 8)
        self.assertEqual(value, {"kloc": 8, "total": .5, "slope": .5})

    def test_nonpositive_denominator(self):
        value = bench.ratios({"F_ms": 2, "m_ms_per_kloc": 3},
                             {"F_ms": -4, "m_ms_per_kloc": 0}, 8)
        self.assertIsNone(value["total"])
        self.assertIsNone(value["slope"])

    def test_corpus_has_no_padding(self):
        lines = bench.corpus(100).splitlines()
        self.assertEqual(len(lines), 100)
        self.assertTrue(all(line.startswith("def bench") for line in lines))
        self.assertEqual(len(set(lines)), 100)

    def test_frozen_input(self):
        frozen = bench.load_denominator()
        self.assertEqual(frozen["points"], 13)
        self.assertEqual(len(frozen["rows"]), 13)
        with patch.object(bench, "DENOMINATOR_SHA256", "0" * 64):
            with self.assertRaisesRegex(ValueError, "digest"):
                bench.load_denominator()

    def test_arc_sentence_matches_spike(self):
        sentences = [line for line in (ROOT / "dev/spikes/SPIKE-ARC.md").read_text().splitlines()
                     if line.startswith("REPORTED: ")]
        self.assertEqual(sentences, [bench.ARC])

    def test_timer_excludes_preparation(self):
        events, loads = [], []
        command = {"prepare": lambda: events.append("prepare"),
                   "argv": ["compiler"], "cwd": ROOT, "metadata": {"name": "timed"}}

        def tick():
            events.append("clock")
            return 0 if events.count("clock") % 2 else 3_000_000

        with patch.object(bench.time, "perf_counter_ns", side_effect=tick):
            with patch.object(bench, "execute", side_effect=lambda *args: events.append("run")):
                with patch.object(bench.os, "getloadavg", return_value=(5, 3, 2)):
                    row = bench.measure(command, loads)
        self.assertEqual(events, ["prepare", "clock", "run", "clock"] * 5)
        self.assertEqual(row["samples_ms"], [3] * 5)
        self.assertEqual(len(loads), 10)


class Driver(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="lan bench '")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.binary = self.root / "compiler ' $(false).py"
        self.calls = self.root / "calls.jsonl"
        self.binary.write_text(
            f"#!{sys.executable}\n"
            "import json, os, pathlib, sys\n"
            f"log = pathlib.Path({str(self.calls)!r})\n"
            "count = len(log.read_text().splitlines()) if log.exists() else 0\n"
            "with log.open('a') as handle:\n"
            "    handle.write(json.dumps(sys.argv[1:]) + '\\n')\n"
            "if count == int(os.environ.get('LANYARD_BENCH_FAIL_AT', '-1')):\n"
            "    sys.exit(7)\n"
            "if '--crate' in sys.argv:\n"
            "    pathlib.Path(sys.argv[sys.argv.index('--crate') + 1]).mkdir()\n",
            encoding="utf-8")
        self.binary.chmod(0o755)

    def test_complete_run_and_noisy_boundary(self):
        with patch.object(bench.os, "getloadavg", return_value=(4, 2, 1)):
            quiet = bench.run(self.binary, False)
        calls = [json.loads(line) for line in self.calls.read_text().splitlines()]
        self.assertEqual(len(calls), 8 * 6)
        self.assertEqual(sum("--crate" in args for args in calls), 6)
        self.assertFalse(quiet["noisy"])
        self.assertFalse(quiet["binding"])
        self.assertFalse(quiet["window"]["same_minute"])
        self.assertEqual(quiet["denominator"]["source"], "frozen-S4")
        self.assertTrue(quiet["denominator"]["noisy"])
        self.assertEqual(len(quiet["observations"]), 8)
        self.assertTrue(all(row["runs"] == 5 for row in quiet["observations"]))
        text = bench.report(quiet)
        self.assertIn("M0-TIME status=REPORTED binding=false", text)
        self.assertIn("RATIO check kloc=1.000", text)
        self.assertIn("emit=check+target-module", text)
        self.assertTrue(text.endswith(bench.ARC))
        with patch.object(bench.os, "getloadavg", return_value=(4.01, 2, 1)):
            noisy = bench.run(self.binary, False)
        self.assertTrue(noisy["noisy"])
        self.assertIn("LOAD max_1m=4.01 status=NOISY", bench.report(noisy))

    def test_warmup_and_timed_failures_have_no_success_report(self):
        for at in (0, 8):
            self.calls.unlink(missing_ok=True)
            output = self.root / "result.json"
            proc = subprocess.run(
                [sys.executable, "-P", ROOT / "dev/bench.py", "--compiler", self.binary,
                 "--output", output], capture_output=True, text=True,
                env=dict(os.environ, LANYARD_BENCH_FAIL_AT=str(at)), timeout=30)
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(proc.stdout, "")
            self.assertIn("child exit=7", proc.stderr)
            self.assertFalse(output.exists())
            self.assertEqual(len(self.calls.read_text().splitlines()), at + 1)

    def test_json_and_existing_output(self):
        output = self.root / "raw.json"
        command = [sys.executable, "-P", ROOT / "dev/bench.py", "--compiler", self.binary,
                   "--output", output]
        proc = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        contents = output.read_bytes()
        doc = json.loads(contents)
        self.assertEqual(doc["method"]["warmups"], 1)
        self.assertEqual(doc["compiler_sha256"], bench.digest(self.binary))
        proc = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("output must be a new file", proc.stderr)
        self.assertEqual(output.read_bytes(), contents)
        self.assertEqual(len(self.calls.read_text().splitlines()), 48)

    def test_missing_output_directory_refuses_before_any_call(self):
        output = self.root / "absent" / "raw.json"
        proc = subprocess.run(
            [sys.executable, "-P", ROOT / "dev/bench.py", "--compiler", self.binary,
             "--output", output], capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertIn("M0-TIME ERROR: output directory must exist and be writable",
                      proc.stderr)
        self.assertFalse(output.exists())
        self.assertFalse(self.calls.exists())

    def test_unserializable_document_leaves_no_output(self):
        output = self.root / "nan.json"
        stderr = io.StringIO()
        argv = ["bench.py", "--compiler", str(self.binary), "--output", str(output)]
        with patch.object(bench, "run", return_value={"arc": float("nan")}), \
                patch.object(bench.sys, "argv", argv), \
                patch.object(bench.sys, "stderr", stderr):
            code = bench.main()
        self.assertEqual(code, 1)
        self.assertIn("M0-TIME ERROR: ", stderr.getvalue())
        self.assertFalse(output.exists())

    def test_compiler_change_refuses(self):
        original = bench.digest

        def edited(path):
            return "changed" if path == self.binary and self.calls.exists() else original(path)

        with patch.object(bench, "digest", side_effect=edited):
            with self.assertRaisesRegex(ValueError, "compiler changed"):
                bench.run(self.binary, False)

    def test_todo_input_is_snapshotted(self):
        source = self.root / "corpus/m0/todo.lan"
        source.parent.mkdir(parents=True)
        source.write_text("def main : Nat := 1\n")
        scratch = self.root / "scratch"
        scratch.mkdir()
        with patch.object(bench, "ROOT", self.root):
            commands = bench.compiler_commands(self.binary, scratch)
        source.write_text("def main : Nat := 2\n")
        self.assertEqual((scratch / "todo.lan").read_text(), "def main : Nat := 1\n")
        self.assertEqual(commands[-1]["metadata"]["source_sha256"],
                         bench.digest(scratch / "todo.lan"))


class GoInputs(unittest.TestCase):
    def test_distinct_paths(self):
        self.assertNotEqual(go.name("a/b_c"), go.name("a_b/c"))

    def test_package_touch_changes_content(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "x.go"
            source.write_text("package x\n")
            change = go.touch(source)
            hashes = [bench.digest(source)]
            for _ in range(6):
                change()
                hashes.append(bench.digest(source))
            self.assertEqual(len(set(hashes)), 7)

    def test_version_drift_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Go version"):
                go.prepare(Path(directory) / "go", bench.load_denominator(),
                           lambda *args, **kwargs: "go version different")

    def test_module_file_follows_frozen_version(self):
        frozen = bench.load_denominator()
        self.assertEqual(go.module_file(frozen["tools"]["go"]),
                         "module lanyardbench\n\ngo 1.24\n")
        self.assertEqual(go.module_file("go version go1.25.3 linux/amd64"),
                         "module lanyardbench\n\ngo 1.25\n")

    def test_embedded_files_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frozen = {"tools": {"go": "go version go1.24.0 darwin/arm64"},
                      "rows": [{"package": "x", "files": 1, "kloc": .001}]}

            def execute(argv, cwd, env, capture):
                if argv[1] == "version":
                    return frozen["tools"]["go"]
                return json.dumps({"ImportPath": "x", "Standard": True,
                                   "Dir": str(root), "GoFiles": ["x.go"],
                                   "EmbedFiles": ["table.txt"]})

            with self.assertRaisesRegex(ValueError, "unsupported Go package"):
                go.prepare(root / "go", frozen, execute)

    def test_size_drift_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input"
            source.mkdir()
            (source / "x.go").write_text("package x\n")
            frozen = {"tools": {"go": "go version go1.24.0 darwin/arm64"},
                      "rows": [{"package": "x", "files": 1, "kloc": .002}]}

            def execute(argv, cwd, env, capture):
                if argv[1] == "version":
                    return frozen["tools"]["go"]
                return json.dumps({"ImportPath": "x", "Standard": True,
                                   "Dir": str(source), "GoFiles": ["x.go"]})

            with self.assertRaisesRegex(ValueError, "input size"):
                go.prepare(root / "go", frozen, execute)


if __name__ == "__main__":
    unittest.main()
