#!/usr/bin/env python3
"""Stage B regression and mutation checks. The source checkouts are read only."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = load_module("lanyard_gen_target", ROOT / "dev/gen-target.py")
PIN = load_module("lanyard_target_pin", ROOT / "dev/target-pin.py")


class Signatures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="target-signatures-")
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name)
        for filename in GEN.FILES:
            shutil.copyfile(ROOT / "target" / filename, self.target / filename)

    def change(self, name, edit):
        for filename in GEN.FILES:
            path = self.target / filename
            lines = path.read_text().splitlines()
            for index, line in enumerate(lines):
                if line.startswith("{"):
                    row = json.loads(line)
                    if row["name"] == name:
                        edit(row)
                        lines[index] = json.dumps(row)
                        path.write_text("\n".join(lines) + "\n")
                        return
        self.fail(f"missing test row {name}")

    def rejected(self, text):
        with self.assertRaisesRegex(GEN.SignatureError, text):
            GEN.read_signatures(self.target)

    def test_generate_deterministically_without_source_paths(self):
        rows = GEN.read_signatures(self.target)
        self.assertEqual(len(rows), 15)
        self.assertEqual(sum(row["kind"] == "type" for row in rows), 9)
        self.assertEqual(GEN.generate(rows), GEN.generate(GEN.read_signatures(ROOT / "target")))
        self.assertNotIn(str(ROOT), GEN.generate(rows))
        self.assertNotIn("streaming_ssr", GEN.generate(rows))

    def test_missing_print_rule(self):
        self.change("Model.create", lambda row: row.pop("print"))
        self.rejected("expected exactly")

    def test_tenth_atom(self):
        with (self.target / GEN.FILES[0]).open("a") as out:
            out.write(json.dumps(dict(name="Hidden", type="Type 0", quantities=[], effects=[],
                                      print="Hidden", kind="type", status="PROPOSED")) + "\n")
        self.rejected("outside closed atom list")

    def test_universe_result_mislabelled_as_constant(self):
        self.change("Db", lambda row: row.update(kind="constant"))
        self.rejected("universe results")
        self.change("Db", lambda row: row.update(type="(Type 0)"))
        self.rejected("universe results")

    def test_missing_required_atom(self):
        path = self.target / GEN.FILES[0]
        path.write_text("\n".join(line for line in path.read_text().splitlines()
                                 if not line.startswith('{"name":"Db",')) + "\n")
        self.rejected("inventory differs")

    def test_duplicate_constant_across_files(self):
        first = next(line for line in (self.target / GEN.FILES[0]).read_text().splitlines()
                     if line.startswith("{"))
        with (self.target / GEN.FILES[1]).open("a") as out:
            out.write(first + "\n")
        self.rejected("duplicate constant")

    def test_duplicate_json_key(self):
        path = self.target / GEN.FILES[0]
        path.write_text(path.read_text().replace('"name":"Db"', '"name":"Db","name":"Db"', 1))
        self.rejected("duplicate field")

    def test_quantity_mismatch(self):
        self.change("Model.create", lambda row: row.update(quantities=["0", "w"]))
        self.rejected("quantities must match")

    def test_unknown_print_argument(self):
        self.change("Db.push_schema", lambda row: row.update(print="#{other}.push_schema().await?"))
        self.rejected("print placeholders")

    def test_dropped_runtime_argument(self):
        self.change("Db.push_schema", lambda row: row.update(print="db.push_schema().await?"))
        self.rejected("print placeholders")

    def test_malformed_placeholder(self):
        self.change("Db.push_schema", lambda row: row.update(print="#{db}.push_schema(#{).await?"))
        self.rejected("malformed print placeholder")

    def test_error_effect_cannot_disappear(self):
        self.change("Db.push_schema", lambda row: row.update(effects=[]))
        self.rejected("error effect row")

    def test_one_argument_cannot_duplicate(self):
        self.change("topcoat.db", lambda row: row.update(
            type="(1 cx : Cx) -> Db", quantities=["1"], print="pair(#{cx}, #{cx})"))
        self.rejected("One argument")

    def test_cannot_claim_printed_without_fixture(self):
        self.change("Model.create", lambda row: row.update(status="PRINTED"))
        self.rejected("PROPOSED only")

    def test_higher_order_domain_is_one_outer_argument(self):
        args, result = GEN.telescope("(f : (x : Nat) -> Nat) -> Nat")
        self.assertEqual(args, [("f", "w", "(x : Nat) -> Nat")])
        self.assertEqual(result, "Nat")

    def test_string_escaping_quotes_utf8_bytes(self):
        self.assertEqual(GEN.ocaml_string('"\\é'), '"\\034\\092\\195\\169"')

    def test_valid_print_edit_changes_generated_bytes(self):
        before = GEN.generate(GEN.read_signatures(self.target))
        self.change("Db.push_schema", lambda row: row.update(print="(#{db}).push_schema().await?"))
        after = GEN.generate(GEN.read_signatures(self.target))
        self.assertNotEqual(before, after)
        self.assertIn("(#{db}).push_schema().await?", after)
        self.assertNotEqual(before.splitlines()[8], after.splitlines()[8])

    def test_invalid_cli_input_does_not_overwrite_output(self):
        output = self.target / "target_generated.ml"
        output.write_text("previous output\n")
        self.change("Model.create", lambda row: row.pop("print"))
        result = subprocess.run(
            [sys.executable, "-P", str(ROOT / "dev/gen-target.py"), "--target", str(self.target),
             "--output", str(output)], capture_output=True, text=True, check=False, timeout=15,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("TARGET-SIG FAIL", result.stderr)
        self.assertEqual(output.read_text(), "previous output\n")


class Drift(unittest.TestCase):
    def setUp(self):
        # The scratch copy lives under the repository root, which .gitignore holds.
        self.root = ROOT / ".gatework/target-drift"
        shutil.rmtree(self.root, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.root.mkdir(parents=True)
        self.target = self.root / "target"
        shutil.copytree(ROOT / "target", self.target)
        upstream = Path(os.environ.get("LANYARD_UPSTREAM", "/Users/oobi/Documents"))
        pins = json.loads((self.target / "PIN.json").read_text())["libraries"]
        self.sources = {}
        self.identity = {}
        for library in PIN.LIBRARIES:
            origin = upstream / library
            dest = self.root / library
            paths = [f"crates/{library}/Cargo.toml", "Cargo.toml"]
            if library == "topcoat":
                paths += [path for path, first, last in PIN.ANCHORS]
            for relative in paths:
                (dest / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(origin / relative, dest / relative)
            # The copy holds file bytes only. It links no Git metadata of the source.
            tag = pins[library]["release_tag"]
            self.identity[library] = {
                "commit": PIN.git(origin, "rev-parse", "--verify", "HEAD^{commit}"),
                "release_tag": tag,
                "release_commit": PIN.git(origin, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"),
            }
            self.sources[library] = dest

    def run_pin(self):
        return subprocess.run(
            [sys.executable, "-P", str(ROOT / "dev/target-pin.py"), "--target", str(self.target),
             "--toasty", str(self.sources["toasty"]), "--topcoat", str(self.sources["topcoat"]),
             "--identity", json.dumps(self.identity)],
            capture_output=True, text=True, check=False, timeout=30,
        )

    def rejected(self, leg):
        result = self.run_pin()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(f"TARGET-PIN {leg} FAIL", result.stderr)
        self.assertNotIn("TARGET-PIN OK", result.stdout)

    def test_control(self):
        result = self.run_pin()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("TARGET-PIN OK", result.stdout)

    def test_each_anchor_byte_flip(self):
        for relative, first, last in PIN.ANCHORS:
            with self.subTest(anchor=relative):
                path = self.sources["topcoat"] / relative
                original = path.read_bytes()
                lines = original.splitlines(keepends=True)
                lines[first - 1] = bytes([lines[first - 1][0] ^ 1]) + lines[first - 1][1:]
                path.write_bytes(b"".join(lines))
                self.rejected("DIFF")
                path.write_bytes(original)

    def test_missing_anchor(self):
        (self.sources["topcoat"] / PIN.ANCHORS[0][0]).unlink()
        self.rejected("ANCHOR")

    def test_truncated_anchor(self):
        (self.sources["topcoat"] / PIN.ANCHORS[0][0]).write_text("short\n")
        self.rejected("ANCHOR")

    def test_workspace_version_drift(self):
        path = self.sources["topcoat"] / "Cargo.toml"
        path.write_text(path.read_text().replace('version = "0.6.2"', 'version = "0.6.3"', 1))
        self.rejected("PIN")

    def test_crate_version_drift(self):
        path = self.sources["toasty"] / "crates/toasty/Cargo.toml"
        path.write_text(path.read_text().replace('version = "0.6.1"', 'version = "0.6.2"', 1))
        self.rejected("PIN")

    def test_pin_identity_fields(self):
        path = self.target / "PIN.json"
        original = json.loads(path.read_text())
        for field in ("commit", "release_tag", "release_commit"):
            with self.subTest(field=field):
                changed = copy.deepcopy(original)
                changed["libraries"]["topcoat"][field] = "0" * 40
                path.write_text(json.dumps(changed))
                self.rejected("PIN")

    def test_signature_print_drift(self):
        path = self.target / GEN.FILES[0]
        path.write_text(path.read_text().replace('.push_schema()', '.reset_db()', 1))
        self.rejected("DIFF")

    def test_missing_fingerprint_line(self):
        path = self.target / "pin.sha256"
        path.write_text("\n".join(path.read_text().splitlines()[1:]) + "\n")
        self.rejected("DIFF")


if __name__ == "__main__":
    unittest.main()
