# M1 Cargo build command

`lanyard build` checks a `.lan` program, emits the same standalone crate as
`emit --crate`, and runs `cargo build` inside the new directory. This is the
build command planned in M0-PLAN section 8. It starts one M1 slice while
the M0 trust-policy ruling and exit stamp remain pending.

```sh
zsh dev/dunecho.sh build
_build/default/bin/lanyard.exe build --out /tmp/todo-build \
  --offline --print-model Todo corpus/m0/todo.lan
```

`--out DIR` is required. Optional `--release`, `--offline` and
`--print-model MODEL` flags may appear in any order before the final source
path. Duplicate options, unknown options, missing values, extra sources
and non-`.lan` inputs are usage errors (exit 64). A path beginning with a
dash needs a `./` prefix or an absolute path.

The directory must be fresh and its parent must exist. Existing output,
including a dangling symlink or a `.partial` staging path, is refused
without modification. Checking, entry selection and model-output validation
finish before any output is published or Cargo is invoked. Invalid source
exits 1; missing input and invalid output paths exit 64, as with emission.

Cargo is selected through `PATH`. It runs with the emitted directory as its
working directory, so Cargo configuration is discovered from that directory
and its ancestors. Rust toolchain and Cargo environment settings retain
their normal meanings. `--offline` requires cached registry packages and
the pinned Toasty and Topcoat Git sources. A fresh successful build writes
its Cargo.lock. Subsequent Cargo builds can reuse that lock and crate
directly; repeating `lanyard build` requires a fresh output directory.

Cargo stdout and stderr pass through unchanged. The driver then prints one
additional stderr row, including on a Cargo failure:

```text
LANYARD-BUILD REPORTED cargo_exit=0 cargo_ms=123.456
```

The time uses the system wall clock and measures only the Cargo subprocess,
including launch overhead. It is informational. Clock adjustments can
affect it. It is separate from the M0 check timings and the R3 parse-through-
emit numerator. No ratio, threshold or performance verdict is inferred.

Normal Cargo exit codes pass through. Missing Cargo returns 127. Termination
by a signal stays unsuccessful; OCaml's shell runner may return 255 or the
shell's status of 128 plus the signal. The emitted crate remains available
after Cargo fails. The build command never executes the resulting program.
With Cargo's default target directory and profile, the executable is
`DIR/target/debug/lanyard-program` or `DIR/target/release/lanyard-program`.

The process boundary uses only fixed, quoted command arguments. User paths
are passed to the existing emitter and directory API, never interpolated
into shell text. The driver links OCaml's Unix library for its clock. No
kernel, eraser, Rust IR, printer, target signature, pin or golden changes.

The driver grows from 212 to 268 lines, adding 56 measured source lines.
The total source inventory grows from 12766 to 12822. The existing proposed
driver limit remains 212 and the proposed total remains 12766. Therefore
the candidate budget check fails for the driver while the unapproved
TRUSTED-LINES leg retains its pending verdict. This slice neither increases
the proposal nor records approval. The compiler-source inventory continues
to exclude external libraries, including the linked OCaml standard library.

Validation uses the cumulative Stage F gate and 16 build-command tests:

```sh
zsh dev/gates.sh --stage M1-build
```

The new tests run the actual compiler with an explicit Cargo test double.
They compare the files presented to Cargo with the existing crate and Todo
goldens, inspect working directories and flags, and check stream forwarding,
normal failures, signals, missing Cargo, semantic refusals, output protection
and literal paths containing shell metacharacters. They also confirm that
`emit --crate` still invokes no Cargo process and that building never runs
the generated executable. A separate real Cargo probe and retained captures
are recorded under `dev/validation/stage-m1-build/`.
