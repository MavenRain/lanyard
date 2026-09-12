# Standalone target crates

`lanyard emit --crate DIR FILE.lan` checks the complete source and prints
`Cargo.toml` and `src/main.rs` into a new directory. The source must have a
runtime definition named `main` with no runtime arguments. A missing main,
a type-only main, or a main requiring arguments refuses before any files
are created. Existing module emission through `--target` and `--native`
retains its output bytes.

The Rust entry point calls the generated main exactly once. It discards the
returned Lanyard value, returns `Ok(())` on success and propagates errors
with `?`. An async main uses Tokio's current-thread runtime and awaits the
call. The existing effect analysis determines whether main is async;
unrelated async functions do not make a synchronous main async.

The manifest has four direct dependencies: serde, tokio, toasty and
topcoat. Toasty and Topcoat use the full Git revisions in `target/PIN.json`,
with SQLite and router features respectively. Tokio enables the runtime
and main macro. An empty workspace section makes the output independent
of an enclosing Cargo workspace. Cargo resolves registry dependencies
and creates its lockfile when first invoked.

The destination must not exist, and its parent must already be a directory.
Files, symlinks to existing outputs and dangling symlinks are also
refused, because the guard reads the parent entries by name. Semantic
checking and source printing finish before the first write. The files go
to a staging directory named DIR.partial and one rename publishes them,
so the destination holds either a whole crate or nothing. As with the
driver's existing input I/O, an operating-system failure during creation
is loud. It leaves the staging directory, which must be inspected or
removed, and the destination stays free for the next run. The command
does not invoke Cargo or execute main.

```sh
zsh dev/gates.sh --stage E-crate
_build/default/bin/lanyard.exe emit --crate /tmp/lanyard-todo test/fixtures/crate.lan
cargo run --manifest-path /tmp/lanyard-todo/Cargo.toml
```

The fixture connects to SQLite in memory, pushes a Todo schema, creates
a row with Nat, text and Bool fields, and looks it up. It exercises async
propagation through several function calls. The crate golden is under
`test/goldens/crate/`. This fixture is separate from the frozen M0 Todo
example, whose operation-family handler remains unsupported.

The gate retains all preceding stage checks. Its new checks compare both
golden files, derive the dependency pins from `target/PIN.json`, check the
async entry point, compile and run a synchronous crate source, require a
runtime error to escape main, and exercise semantic and path refusals.
Deleting the call to the Lanyard main makes the error observation fail.

For an offline test with existing library checkouts, prepare a second
crate with local dependency paths. The helper verifies both Git revisions
and clean tracked sources before emitting. It saves the original Git
manifest as `Cargo.git.toml` and changes only the two dependency locations.
It does not modify either library checkout. The registry cache must already
contain the other dependencies.

```sh
mkdir -p .gatework
python3 -P dev/prepare-crate.py \
  --toasty /path/to/toasty --topcoat /path/to/topcoat \
  --output .gatework/crate-pinned
cargo build --offline --manifest-path .gatework/crate-pinned/Cargo.toml
.gatework/crate-pinned/target/debug/lanyard-program
```

Use the installed compact build commands and validation ledger when
running these checks in the development workspace. The preparation output
must be new; `--source FILE.lan` selects another checked program.
Pass `--lock PATH` to seed resolution from an existing validation lockfile
when the offline index cannot resolve every dependency afresh. Cargo may
update its root package and feature dependencies on the first build.

Handler fusion, the complete M0 Todo golden, `build` and `run` commands,
and M0 timing and exit gates remain ahead. Numeric trusted-line allowances
remain pending user rulings. The printer census includes `rust/crate.ml`;
this slice does not change an allowance or the kernel.
