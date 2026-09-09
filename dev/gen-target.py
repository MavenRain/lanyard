#!/usr/bin/env python3
"""Compile the Stage B target metadata, without installing kernel axioms."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


class SignatureError(ValueError):
    pass


FILES = ("toasty-7bd502cb.sig", "topcoat-51caa01.sig")
ATOMS = frozenset(("Db", "Cx", "Uri", "Response", "SeeOther", "Deferred",
                   "Form", "toasty::Error", "topcoat::Error"))
FIELDS = frozenset(("name", "type", "quantities", "effects", "print",
                    "kind", "status"))
QUANTITIES = {"0": "Zero", "1": "One", "w": "Many"}
KINDS = {"type": "Type_constant", "constant": "Constant", "schema": "Schema"}
NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:(?:\.|::)[A-Za-z][A-Za-z0-9_]*)*")
PLACEHOLDER = re.compile(r"#\{([A-Za-z][A-Za-z0-9_]*)\}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SignatureError(f"duplicate field {key}")
        result[key] = value
    return result


def telescope(source):
    """Split only outer arrows, retaining arrows inside argument types."""
    depth = 0
    start = 0
    parts = []
    for pos, char in enumerate(source):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if depth < 0:
            raise SignatureError("unbalanced type parentheses")
        if depth == 0 and source[pos:pos + 2] == "->":
            parts.append(source[start:pos].strip())
            start = pos + 2
    if depth != 0:
        raise SignatureError("unbalanced type parentheses")
    result = source[start:].strip()
    if not result:
        raise SignatureError("missing result type")
    args = []
    for part in parts:
        binder = re.fullmatch(r"\((?:(0|1|w) )?([A-Za-z][A-Za-z0-9_]*) : (.+)\)", part)
        if binder is None:
            raise SignatureError(f"expected a named outer binder: {part}")
        quantity, name, domain = binder.groups()
        if name in [arg[0] for arg in args]:
            raise SignatureError(f"duplicate argument {name}")
        args.append((name, quantity or "w", domain))
    return args, result


def strip_parentheses(source):
    """Drop balanced outer parentheses, so (Type 0) reads as Type 0."""
    result = source.strip()
    while result.startswith("(") and result.endswith(")"):
        depth = 0
        closed_early = False
        for pos, char in enumerate(result):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            if depth == 0 and pos < len(result) - 1:
                closed_early = True
                break
        if closed_early:
            return result
        result = result[1:-1].strip()
    return result


def validate(row):
    if not isinstance(row, dict) or set(row) != FIELDS:
        raise SignatureError("expected exactly name/type/quantities/effects/print/kind/status")
    for field in ("name", "type", "print", "kind", "status"):
        value = row[field]
        if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
            raise SignatureError(f"{field} must be nonempty text without control characters")
    if NAME.fullmatch(row["name"]) is None:
        raise SignatureError("invalid constant name")
    if row["kind"] not in KINDS or row["status"] != "PROPOSED":
        raise SignatureError("Stage B accepts type/constant/schema rows at PROPOSED only")
    args, result = telescope(row["type"])
    if row["quantities"] != [arg[1] for arg in args]:
        raise SignatureError("quantities must match every outer binder in order")
    if not isinstance(row["effects"], list) or any(
        not isinstance(effect, str) or NAME.fullmatch(effect) is None for effect in row["effects"]
    ) or len(set(row["effects"])) != len(row["effects"]):
        raise SignatureError("effects must be distinct names")
    returns_type = re.fullmatch(r"Type [0-9]+", strip_parentheses(result)) is not None
    if returns_type != (row["kind"] == "type"):
        raise SignatureError("universe results must be declared as type constants")
    if returns_type and row["name"] not in ATOMS:
        raise SignatureError(f"foreign type constant outside closed atom list: {row['name']}")
    if returns_type and row["effects"]:
        raise SignatureError("type constants must have an empty effect row")
    placeholders = set(PLACEHOLDER.findall(row["print"]))
    if "#{" in PLACEHOLDER.sub("", row["print"]):
        raise SignatureError("malformed print placeholder")
    available = {arg[0] for arg in args}
    runtime = {arg[0] for arg in args if arg[1] != "0"}
    if not runtime <= placeholders or not placeholders <= available:
        raise SignatureError(f"print placeholders must use runtime arguments {sorted(runtime)} and only declared binders")
    occurrences = PLACEHOLDER.findall(row["print"])
    if any(quantity == "1" and occurrences.count(name) != 1 for name, quantity, domain in args):
        raise SignatureError("a One argument must occur exactly once in its print rule")
    if ("?" in row["print"]) != any(effect.endswith("::Error") for effect in row["effects"]):
        raise SignatureError("question-mark propagation must agree with the error effect row")
    return row


def read_signatures(target):
    rows = []
    names = set()
    for filename in FILES:
        for number, line in enumerate((target / filename).read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                row = validate(json.loads(line, object_pairs_hook=unique_object))
            except (ValueError, TypeError) as error:
                raise SignatureError(f"{filename}:{number}: {error}") from error
            if row["name"] in names:
                raise SignatureError(f"{filename}:{number}: duplicate constant {row['name']}")
            names.add(row["name"])
            rows.append(row)
    actual = {row["name"] for row in rows if row["kind"] == "type"}
    if actual != ATOMS:
        raise SignatureError(f"foreign atom inventory differs: missing={sorted(ATOMS - actual)}")
    return rows


def ocaml_string(value):
    # OCaml decimal escapes quote UTF-8 bytes, including arbitrary non-ASCII text.
    return '"' + "".join(chr(byte) if 32 <= byte < 127 and byte not in (34, 92)
                         else f"\\{byte:03d}" for byte in value.encode("utf-8")) + '"'


def ocaml_list(values):
    return "[ " + "; ".join(values) + " ]"


def generate(rows):
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    lines = [
        "(* Generated by dev/gen-target.py. Edit target/*.sig, never this file. *)",
        "type quantity = Zero | One | Many",
        "type kind = Type_constant | Constant | Schema",
        "type status = Proposed",
        "type entry = {",
        "  name : string; kernel_type : string; quantities : quantity list;",
        "  effects : string list; print_rule : string; kind : kind; status : status;",
        "}",
        f"let signature_sha256 = {ocaml_string(digest)}",
        "let entries : entry list = [",
    ]
    for row in rows:
        lines.extend([
            f"  {{ name = {ocaml_string(row['name'])};",
            f"    kernel_type = {ocaml_string(row['type'])};",
            f"    quantities = {ocaml_list(QUANTITIES[q] for q in row['quantities'])};",
            f"    effects = {ocaml_list(ocaml_string(e) for e in row['effects'])};",
            f"    print_rule = {ocaml_string(row['print'])};",
            f"    kind = {KINDS[row['kind']]}; status = Proposed }};",
        ])
    lines.extend([
        "]",
        "let find name = List.find_opt (fun entry -> String.equal name entry.name) entries",
        "let foreign_types = List.filter (fun entry ->",
        "  match entry.kind with Type_constant -> true | Constant | Schema -> false) entries",
    ])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=Path(__file__).resolve().parent.parent / "target")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        rows = read_signatures(args.target)
        generated = generate(rows)
        if args.check:
            print(f"TARGET-SIG OK rows={len(rows)} foreign_types={len(ATOMS)} generated_lines={len(generated.splitlines())}")
        elif args.output is None:
            sys.stdout.write(generated)
        else:
            args.output.write_text(generated, encoding="utf-8")
    except (OSError, UnicodeError, SignatureError) as error:
        print(f"TARGET-SIG FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
