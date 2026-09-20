# M1 compile and serve command

`lanyard serve` checks an HTTP handler, emits its crate into a fresh
directory and invokes `cargo run` there. The generated server starts as
soon as compilation succeeds:

```sh
_build/default/bin/lanyard.exe serve --out /tmp/todo-serve \
  --listen 127.0.0.1:3000 test/fixtures/todo-session.lan
```

Both `--out` and `--listen` are required. `--release` and `--offline`
retain their Cargo meanings. These options may appear in any order
before the final `.lan` source path. Duplicate flags, invalid addresses,
missing arguments and the interpreter or transcript options exit 64
before source I/O. Invalid source or a non-HTTP entry point exits 1.
Preflight failures publish no crate and never invoke Cargo. An existing
output directory, symlink or `.partial` path is preserved and refused.

The emitted crate is identical to `emit --crate DIR --listen ADDRESS`.
The listener accepts numeric IPv4 loopback addresses, including port 0,
and reports `LANYARD-LISTEN http://127.0.0.1:PORT` on stderr when ready.
Requests, forms, errors and database lifetime follow the
[HTTP slice](STAGE-M1-HTTP.md). For the Todo fixture, request `/init`
before creating or listing rows. By default each process starts with an
empty in-memory database. Add [--database PATH](STAGE-M1-DATABASE.md) to
reuse a SQLite file across restarts. This command does not watch files or
rebuild on edits.

Cargo is selected through `PATH`. Its working directory is the emitted
crate, so Cargo configuration, `CARGO_TARGET_DIR`, toolchain selection
and configured target runners keep their normal meanings. The driver
replaces itself with Cargo through a shell `exec` containing only fixed,
quoted arguments. Source and output paths never become shell commands.
Stdin, stdout and stderr are inherited. Native Cargo execution hands the
process to the server, which supports graceful Ctrl+C and SIGTERM.
Custom target runners retain their own process and signal behavior.

Cargo diagnostics and exit status pass through. Missing Cargo exits 127;
an unexecutable Cargo exits 126. Cargo or server failure leaves the
emitted crate available for inspection. `serve` prints no build-time
measurement because `cargo run` includes the server's lifetime. The
separate `build` command retains its compilation-only timing report.

Run the cumulative gate with pinned local dependencies:

```sh
LANYARD_TOASTY=/path/to/toasty LANYARD_TOPCOAT=/path/to/topcoat \
  zsh dev/gates.sh --stage M1-serve
```

The gate retains the HTTP and preceding slice checks. Eight process
test groups cover preflight, byte-identical emission, Cargo arguments,
environment and stdin inheritance, failures, shell metacharacters in
paths and signal delivery to the same process ID. The native test uses
real offline Cargo with checked local target pins, verifies emitted
source and manifest bytes before adapting dependency paths, and checks
Todo requests, fresh state on restart, SIGINT and SIGTERM shutdown.
