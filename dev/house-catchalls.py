#!/usr/bin/env python3
"""Check every simple OCaml catch-all against the two ruled function sites."""

from pathlib import Path
import re
import subprocess
import sys

OPENERS = "([{"
CLOSERS = ")]}"
# A pattern that can fail to match names a constructor, a literal, a list or
# record bracket, a cons, a module path, unit or a polymorphic variant tag.
# A pattern with none of those is built from binders alone, so it matches
# every remaining value.  The lookbehind keeps the tail of a binder name
# such as x2 or aB out of the constructor and literal forms.  A backtick
# opens a tag, and a tag with a lowercase name is selective all the same.
SELECTIVE = re.compile(r"(?<![A-Za-z0-9_'])[A-Z0-9]|[\[\]{}]|::|\.|\(\s*\)|`")
# One colon opens a type annotation, two colons are a cons pattern, so the
# two lookarounds keep a list pattern out of the annotation form.
ANNOTATION = re.compile(r"(?<!:):(?!:)[^)]*")
NAME = re.compile(r"[a-z_][A-Za-z0-9_']*")
GUARD = re.compile(r"\bwhen\b")
DECLARATION = re.compile(r"^let\s+(?:rec\s+)?([a-z_][A-Za-z0-9_']*)\b", re.MULTILINE)
# A bar next to an operator character belongs to that operator, not to an
# arm:  the two bars of a boolean or, the bar of |> and <|, and the array
# and quoted string brackets all open no pattern.
BAR = re.compile(r"(?<![!$%&*+\-./:<=>?@^|~\[])\|(?![!$%&*+\-./:<=>?@^|~\]}])")
LITERAL = re.compile(r"\{([a-z_]*)\|.*?\|\1\}"
                     r"|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^\\'])'", re.DOTALL)


def blanked(source):
    """The source with every comment and literal turned into blanks.

    Offsets and line breaks stay as they are, so a report still names the
    right line.  A bar inside a comment, a string or a char literal is text,
    not the start of an arm.
    """
    out = list(source)
    index, depth = 0, 0
    while index < len(source):
        head = source[index:index + 2]
        found = LITERAL.match(source, index) if depth == 0 else None
        if head == "(*":
            depth += 1
            width = 2
        elif head == "*)" and depth > 0:
            depth -= 1
            width = 2
        elif found is not None:
            width = found.end() - index
        elif depth > 0:
            width = 1
        else:
            index += 1
            continue
        for position in range(index, index + width):
            if out[position] != "\n":
                out[position] = " "
        index += width
    return "".join(out)


def arm(source, start):
    """The pattern text of the arm whose bar sits at start, or None.

    The scan counts brackets, so an arrow inside a type annotation and a bar
    inside a nested pattern cannot close the arm.  A bar that meets a closing
    bracket first belongs to no arm at all.  A guarded arm yields None too:
    its guard can fail, so the arm matches no more than the arms after it.
    """
    depth, index = 0, start + 1
    while index < len(source):
        char = source[index]
        if char in OPENERS:
            depth += 1
        elif char in CLOSERS:
            if depth == 0:
                return None
            depth -= 1
        elif depth == 0 and source[index:index + 2] == "->":
            text = source[start + 1:index]
            return None if GUARD.search(text) else text
        index += 1
    return None


def check(root):
    allowed = {}
    for row in (root / "dev/house-allow.txt").read_text().splitlines():
        fields = row.split("\t")
        if len(fields) != 4 or not all(fields):
            raise ValueError("HOUSE allow entries need path, function, arm and reason")
        path, function, arm_text, reason = fields
        key = (path, function)
        if key in allowed:
            raise ValueError("HOUSE allow entry is duplicated")
        allowed[key] = arm_text
    if set(allowed) != {("bin/lanyard.ml", "dispatch")}:
        raise ValueError("HOUSE allowlist must contain exactly the one D-M1-10 site")
    result = subprocess.run(
        ["rg", "--files", "lib", "surface", "bin", "test", "dev",
         *(["rust"] if (root / "rust").is_dir() else []),
         "--glob", "*.ml", "--glob", "*.mli"], cwd=root,
        capture_output=True, text=True, check=True)
    used = set()
    bad = []
    for relative in result.stdout.splitlines():
        source = (root / relative).read_text()
        scan = blanked(source)
        declarations = list(DECLARATION.finditer(scan))
        for opening in BAR.finditer(scan):
            text = arm(scan, opening.start())
            if text is None:
                continue
            stripped = ANNOTATION.sub("", text)
            names = set(NAME.findall(stripped)) - {"as"}
            if SELECTIVE.search(stripped) or not names or names <= {"true", "false"}:
                continue
            preceding = [found for found in declarations if found.start() < opening.start()]
            function = preceding[-1].group(1) if preceding else None
            start = source.rfind("\n", 0, opening.start()) + 1
            stop = source.find("\n", opening.start())
            line = source[start:stop if stop >= 0 else len(source)]
            number = source.count("\n", 0, start) + 1
            key = (relative, function)
            entry = f"{relative}:{number}:{line}"
            # An or-pattern holds one bar per branch and every branch names
            # the same arm, so one line is reported once.
            if key in allowed and line.strip() == allowed[key] and key not in used:
                used.add(key)
            elif entry not in bad:
                bad.append(entry)
    for key in allowed.keys() - used:
        bad.append(f"HOUSE stale allow entry: {key[0]}:{key[1]}")
    print("\n".join(bad), end="\n" if bad else "")
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        raise SystemExit(check(Path(sys.argv[1]).resolve()))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"HOUSE named catch-all scan failed: {error}")
        raise SystemExit(1)
