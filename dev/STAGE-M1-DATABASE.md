# M1 persistent HTTP databases

Add `--database PATH` to an HTTP `emit --crate`, `build`, or `serve`
command to keep SQLite rows across process restarts:

```sh
_build/default/bin/lanyard.exe serve --out /tmp/todo-persistent \
  --listen 127.0.0.1:3000 --database ./todo.sqlite3 \
  test/fixtures/todo-session.lan
```

For the Todo fixture, request `/init` once on a new database before
creating rows. Stop the server and restart with a fresh output directory
and the same database path to read the existing rows. Schema creation
remains the handler's responsibility through `Db.push_schema`; startup
does not initialize, reset, or migrate an existing schema.

The option requires `--listen`. Build and serve accept their options in
any order before the source path. Emit accepts `--database` immediately
before or after `--listen`, following `--crate DIR`. Missing, empty,
non-UTF-8, repeated, or incompatible options exit 64 before source or
output I/O. Prefix a path starting with `-` with `./` or use an absolute
path. Scripted sessions and interpreter runs retain their existing modes.

Relative paths are anchored to the invocation's working directory before
Cargo changes directories. That absolute path is embedded in the emitted
Rust, so running the binary from another directory uses the same file.
Emission and compilation do not open the database. The parent directory
must exist when the server starts; SQLite creates the file if absent.
Names containing spaces, Unicode, quotes, backslashes, control characters,
or URI punctuation retain their filename bytes. Paths are passed to the
SQLite driver's file API and never parsed as connection URLs or shell
commands. In particular, `:memory:` names an ordinary file in the invocation
directory when passed to this option.

Opening a database fails with a `server database:` diagnostic and exit 1,
before the readiness marker, if the parent is missing or the path cannot
be opened. Startup may create the database before a later listener bind
failure. Handler failures retain the existing HTTP error behavior. Requests
in one process remain serialized; this option adds no transaction or
rollback around a handler. SIGINT and SIGTERM retain graceful shutdown.

Without `--database`, each HTTP process still uses private in-memory
SQLite. Its emitted source and manifest retain their bytes. File-backed
crates add `toasty-driver-sqlite` at the same revision already pinned for
Toasty. The local preparation helper verifies both dependency revisions
before replacing their manifest entries with paths to the clean checkout.

Run the cumulative gate:

```sh
LANYARD_TOASTY=/path/to/toasty LANYARD_TOPCOAT=/path/to/topcoat \
  zsh dev/gates.sh --stage M1-database
```

The gate preserves `M1-serve` and its preceding checks. Five CLI groups
exercise preflight and byte-identical emission through all three commands.
The native test compiles against checked local pins, verifies serve's
emitted bytes before adapting dependencies, and exercises create, update,
delete, three restarts, changed working directories, exact filename bytes,
both shutdown signals, and a missing-parent startup failure. A compiled
control replaces the file driver with in-memory SQLite and must lose the
existing schema. Receipts are in `validation/stage-m1-database/`.
