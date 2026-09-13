"""Prepare the S4 copied-package experiment without writing into GOROOT."""

import hashlib
import json
import os
from pathlib import Path


def hidden(package):
    return package.startswith(("internal/", "cmd/")) or "/internal/" in package


def name(package):
    # Hex encoding cannot alias two import paths.
    return "pkg_" + package.encode("utf-8").hex()


def module_file(version):
    # `go version go1.24.0 darwin/arm64` gives the directive `go 1.24`, so the
    # scratch module follows the frozen toolchain instead of a second pin.
    release = version.split()[2].removeprefix("go").split(".")
    return "module lanyardbench\n\ngo " + ".".join(release[:2]) + "\n"


def prepare(root, frozen, execute):
    root.mkdir()
    env = dict(os.environ, GOCACHE=str(root / "cache"), GOPATH=str(root / "path"),
               GOMODCACHE=str(root / "modcache"), GOTOOLCHAIN="local", GOENV="off",
               GOWORK="off", GOFLAGS="-mod=mod", GOPROXY="off", GOSUMDB="off")
    version = execute(["go", "version"], root, env, capture=True).strip()
    if version != frozen["tools"]["go"]:
        raise ValueError("Go version/platform differs from the frozen S4 input")
    target_os, target_arch = version.split()[-1].split("/")
    env.update(GOOS=target_os, GOARCH=target_arch, GO111MODULE="on", GOEXPERIMENT="")
    # Query standard packages outside the scratch module before writing go.mod.
    def listed(package):
        row = json.loads(execute(["go", "list", "-json", package], root, env, capture=True))
        if (row["ImportPath"] != package or not row.get("Standard")
                or row.get("CgoFiles") or row.get("EmbedFiles")):
            raise ValueError("unsupported Go package: " + package)
        return row

    tables = {}
    for frozen_row in frozen["rows"]:
        package = frozen_row["package"]
        table, pending = {}, [package]
        while pending:
            current = pending.pop()
            if current not in table:
                row = listed(current)
                table[current] = row
                pending.extend(dep for dep in row.get("Imports", []) if hidden(dep) and dep not in table)
        tables[package] = table
    (root / "go.mod").write_text(module_file(version), encoding="utf-8")
    copied = set()
    commands = []
    for frozen_row in frozen["rows"]:
        package = frozen_row["package"]
        table = tables[package]
        for current, row in table.items():
            # A target gets its own copy; dependencies use separate directories.
            destination = root / ("dep_" + name(current) if current != package else name(current))
            if destination in copied:
                continue
            destination.mkdir()
            copied.add(destination)
            replacements = {dep: "lanyardbench/dep_" + name(dep)
                            for dep in row.get("Imports", []) if hidden(dep)}
            for filename in row.get("GoFiles", []):
                body = (Path(row["Dir"]) / filename).read_text(encoding="utf-8")
                # This is the S4 exact quoted import-path replacement method.
                for old, new in replacements.items():
                    body = body.replace('"' + old + '"', '"' + new + '"')
                (destination / filename).write_text(body, encoding="utf-8")
            for filename in row.get("SFiles", []) + row.get("HFiles", []):
                (destination / filename).write_bytes((Path(row["Dir"]) / filename).read_bytes())
        row = table[package]
        files = sorted(row.get("GoFiles", []))
        lines = sum(len((Path(row["Dir"]) / filename).read_bytes().splitlines()) for filename in files)
        if not files or len(files) != frozen_row["files"] or lines != round(frozen_row["kloc"] * 1000):
            raise ValueError("Go input size differs from frozen S4: " + package)
        first = root / name(package) / files[0]
        source_hashes = {filename: hashlib.sha256(
            (root / name(package) / filename).read_bytes()).hexdigest() for filename in files}
        commands.append({
            "argv": ["go", "build", "./" + name(package)], "cwd": root, "env": env,
            "prepare": touch(first),
            "metadata": {"name": package, "mode": "go", "kloc": lines / 1000,
                         "lines": lines, "files": len(files), "source_sha256": source_hashes},
        })
    return commands, version


def touch(path):
    # Each invocation changes the package content, including between identical runs.
    count = 0

    def append():
        nonlocal count
        count += 1
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n// lanyard-bench-touch {count}\n")

    return append
