# M0 SQLite execution gate

`M0-E2E` rebuilds the compiler, emits the Todo crate, builds it against
the pinned libraries and checks its exact output:

```sh
zsh dev/gates.sh M0-E2E --toasty /path/to/toasty --topcoat /path/to/topcoat
```

The library paths must be clean tracked checkouts at the commits in
`target/PIN.json`. The gate measures each checkout itself before the
build: it reads `git rev-parse HEAD` and the tracked-file status of both
paths. An unreadable HEAD, a dirty tracked file, a HEAD that differs from
its pin, or a pin file without that library commit stops the run before
the compiler build. The gate measures both checkouts again after the
Cargo build, before it hashes the executable. A library that moves or
becomes dirty during the build fails the run, and the program does not
execute. The existing crate preparer also verifies both pins before
emission. It preserves the original Git manifest as `Cargo.git.toml`
and changes only the dependency locations in `Cargo.toml`. The generated
Rust and original manifest must match the complete M0 golden. The gate
seeds `Cargo.lock` from the saved Stage E Todo validation.

Cargo builds with `--offline --locked`, so the locked registry dependencies
must already be cached. The command uses `dev/dunecho.sh`, `cargocho` and
`gateledger`. Rust 1.98 is the default installed toolchain; `--toolchain`
selects another installed version. `--jobs` defaults to two. The gate
records `rustc -vV` and explicitly builds for that compiler's host target.

The program must exit zero, print exactly `corpus/m0/todo.stdout` and leave
stderr empty:

```text
Todo { id: 1, title: "hi", completed: false }
```

The final newline is part of the comparison. A missing newline, extra
row, diagnostic on stderr or nonzero exit fails the gate. A failed
compiler build, crate preparation or Cargo build stops the dependent
steps. A missing executable fails even if the build command exited zero.
The existing process-group deadline and bounded drain apply to every
child, including the Rust build and program.

The output directory must be new. A default run creates and retains a
fresh `.gatework/m0-e2e.*` directory. An explicit path is useful for a
validation record:

```sh
zsh dev/gates.sh M0-E2E --toasty /path/to/toasty --topcoat /path/to/topcoat \
  --output .gatework/m0-e2e-validation
```

That directory contains the prepared crate, expected stdout, seven pairs
of command logs and `report.json`. A failure retains the checks reached
so far. The report stores command arguments, exit codes, elapsed times,
stream hashes, source and lock hashes, and the executable path and hash.
Its `libraries` block holds the measured HEAD of each checkout, not a
copy of the pin file. The library measurements are not check rows; the
report keeps the seven named steps.
The gate checks that the prepared source and lock remain unchanged during
the build and run, and that its M0 inputs retain their original bytes.

`--target-dir` selects the Cargo cache; the default is
`.gatework/cargo-target`. A relative `--output` or `--target-dir` is
taken from the repository root, not from the caller's directory. An
absolute path is used as given. Every invocation forces the compile-only ledger
to run Cargo for the fresh crate, while Cargo can reuse its build cache.
A prior green ledger entry cannot substitute for an executable.
The generated crate has its own local Git index for the ledger's input
hashing. The gate indexes its four prepared files and creates no commit.
Both Git steps drop the operator's configuration. The init step sets
`init.defaultBranch=main` and silences the branch-name advice, and the
index step sets `core.excludesFile=/dev/null` and passes `--force`. A
stock global configuration, or a global ignore file that covers
`Cargo.lock`, therefore cannot fail a correct crate.
The operator prunes retained output directories and caches when their
evidence is no longer needed.

Exit zero means this execution check passed; exit one means failure.
An invalid flag, a missing library path or `--jobs 0` uses argparse's
exit two and creates no report. An output directory that exists already,
or a path the gate cannot create, prints `M0-E2E ERROR: ...` on stderr
and exits one.
The final `M0-E2E-REPORT` row names the saved report. This check supplements
the seven named M0 legs. Its success does not assign the open trusted-code
allowances or stamp M0-EXIT.

The runner regressions are part of the cumulative Stage F gate:

```sh
python3 -P test/lan_m0_e2e.py
zsh dev/gates.sh --stage F-gates
```

The unit suite exercises failures and artifact drift without rebuilding
Rust. The separate `M0-E2E` command supplies the real pinned SQLite run.
Validation captures for this slice live under
`dev/validation/stage-f-e2e/`.
