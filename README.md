# Lanyard

Lanyard is a language under construction that retains Kanon's kernel and
will emit Rust using Toasty and Topcoat. Its source extension is `.lan`.

Stage A is committed at `52eb5a7`. Stage B adds pinned target signatures,
a generated OCaml metadata library, and source drift checks. Stage C checks
those signatures, elaborates models and operation families, and derives the
foreign-type census. Stage D adds Rust IR, quantity-aware erasure and checked
foreign-call metadata. The Stage E native command prints Rust for pure
programs, including typed closures, captures and recursive data. The target
command adds synchronous foreign constants, concrete and applied foreign
types, async database calls, and model create/lookup for Nat, Bool and text
fields. Direct Db.connect calls and aliases select model schemas and check
URL text. The crate command writes a standalone program with pinned
dependencies and a synchronous or async entry point.
Crate emission specializes finite checked handlers into direct operation
bodies. The M0 Todo corpus emits a complete crate that creates and prints
a row. Stage F adds classified axiom reports and the AXIOM-RATIO inputs.
Other model field types, general recursive handlers, timing and the M0
close remain ahead. The generated signature allowance is proposed at
104 lines and awaits the user's ruling. See
[target documentation](target/README.md), the
[Stage B build log](dev/M0-BUILD-LOG.md#lanyard-m0-stage-b-2026-09-09) and
the [Stage C build log](dev/spikes/M0-BUILD-LOG.md#stage-c-2026-09-09) with
its [Stage C mutation log](dev/spikes/MUTATION-LOG.md#stage-c-2026-09-09).
The two stages record their work in separate log families.

Build and validate through Stage D:

```sh
zsh dev/gates.sh --stage D
_build/default/bin/lanyard.exe check --erased examples/m0-todo.lan
```

Validate and use the native Rust printer:

```sh
zsh dev/gates.sh --stage E-native
_build/default/bin/lanyard.exe emit --native test/fixtures/native.lan
```

The [native printer slice](dev/STAGE-E-NATIVE.md) supports arithmetic,
products, sums, native calls, [typed closures](dev/STAGE-E-CLOSURES.md), and
[recursive families](dev/STAGE-E-RECURSIVE.md).
It reports unsupported foreign and polymorphic field layouts explicitly.
The complete M0 Todo crate golden is under `corpus/m0/golden/`.

Validate and use the [synchronous foreign printer](dev/STAGE-E-FOREIGN.md):

```sh
zsh dev/gates.sh --stage E-foreign
_build/default/bin/lanyard.exe emit --target test/fixtures/foreign.lan
```

This prints a Rust source module using the pinned target paths, including
`topcoat.db` and `topcoat.see_other`.

Validate and use the [async database printer](dev/STAGE-E-ASYNC.md):

```sh
zsh dev/gates.sh --stage E-async
_build/default/bin/lanyard.exe emit --target test/fixtures/async.lan
```

`Db.push_schema` prints an awaited call. Its callers become async functions
and propagate database errors. Async closures and recursive async calls
remain explicit refusals. Model schemas are described below.

Validate [applied foreign types](dev/STAGE-E-FOREIGN-TYPES.md):

```sh
zsh dev/gates.sh --stage E-foreign-types
_build/default/bin/lanyard.exe emit --target test/fixtures/foreign-types.lan
```

`Form T` and `Deferred T` retain their checked type arguments, including
nested wrappers and native data layouts. A One binder moves its wrapper;
a Many binder shares it through `Arc`.

Validate [scalar model schemas](dev/STAGE-E-MODELS.md):

```sh
zsh dev/gates.sh --stage E-models
_build/default/bin/lanyard.exe emit --target test/fixtures/models.lan
```

`Counter.create` and `Counter.get_by_id` print awaited Toasty operations.
The `id` field is the supplied primary key. Database fields use checked
integer conversions; overflow and negative stored values return an error.
Two-unit sums, including aliases, use Boolean columns with tag 0 as false
and tag 1 as true. Keys remain Nat.
Checked byte lists, including the Todo title type, use String columns.
Writes reject elements above 255 and invalid UTF-8 before the database call.

Validate [database connections](dev/STAGE-E-CONNECTIONS.md):

```sh
zsh dev/gates.sh --stage E-connections
_build/default/bin/lanyard.exe emit --target test/fixtures/connections.lan
```

A checked alias such as `def open : Bytes -> Db := Db.connect Todo Bytes`
prints an async connection function. A product of declared model types
selects several schemas. Callers can connect, push the schema and create
rows in one generated program. URL conversion rejects invalid bytes and
UTF-8 before opening a connection.

Direct calls such as `Db.connect Todo Bytes url` work inside functions,
let bodies and case branches. Several calls in one body can select different
models and URLs. Model and text type arguments must be closed; generic
connection functions and stored connection function values still refuse.

Emit a [standalone target crate](dev/STAGE-E-CRATE.md):

```sh
zsh dev/gates.sh --stage E-crate
_build/default/bin/lanyard.exe emit --crate /tmp/lanyard-todo test/fixtures/crate.lan
cargo run --manifest-path /tmp/lanyard-todo/Cargo.toml
```

The output directory must be new and its parent must exist. The generated
entry point runs a zero-argument `main`, discards its returned value and
propagates errors through Rust's `Result`. This fixture connects to SQLite
in memory, creates a Todo and looks it up. Emission does not run Cargo.

Crates now keep the [dependencies of main](dev/STAGE-E-REACHABLE.md).
Unused functions and model schemas are omitted before lowering. The full
source still typechecks; references in types and untaken branches are
retained. Module emission continues to print every definition.

```sh
zsh dev/gates.sh --stage E-reachable
```

Crates also specialize [finite checked handlers](dev/STAGE-E-HANDLERS.md).
Known signature constructors and their continuations reduce to direct
code. Database operations keep their order and execute once, including
calls whose results are unused. Remaining runtime signature programs
refuse before output is created.

```sh
zsh dev/gates.sh --stage E-handlers
_build/default/bin/lanyard.exe emit --crate /tmp/lanyard-handlers test/fixtures/handlers-db.lan
```

Emit and validate the [M0 Todo crate](dev/STAGE-E-TODO.md):

```sh
zsh dev/gates.sh --stage E-todo
_build/default/bin/lanyard.exe emit --crate /tmp/lanyard-m0 --print-model Todo corpus/m0/todo.lan
```

The generated program creates one row and prints
`Todo { id: 1, title: "hi", completed: false }`.
The optional model formatter checks scalar conversions and propagates
output errors. EMIT-DIFF compares the whole crate without normalization.

Inspect the [classified axioms](dev/STAGE-F-AXIOMS.md):

```sh
zsh dev/gates.sh --stage F-axioms
_build/default/bin/lanyard.exe axioms corpus/m0/todo.lan
_build/default/bin/lanyard.exe axioms --names examples/m0-todo.lan
```

The report lists Framework, Foreign, Classical and Div, sorted by class
and name, with class totals and the compiled target catalog's SHA-256.
Todo reports 17 foreign constants and 3 definitions of the checked
module (Bool, Todo and main). These are informational inputs, with no
ratio bound. The scope is the whole checked module, including unused
catalog rows and model operations.
Source postulates without an M0 class produce a diagnostic; `--names`
prints their declaration names. The carried `.kan` output stays unchanged.

See [Stage C](dev/STAGE-C.md) for the `.lan` declaration grammar and checked
Todo example, and [Stage D](dev/STAGE-D.md) for Rust erasure, its current
limits and the proposed IR allowance. The carried `.kan` checker is also available:

```sh
_build/default/bin/lanyard.exe check test/fixtures/b01-function-eta.kan
_build/default/bin/lanyard.exe axioms test/fixtures/b08-axiom-disclosure.kan
_build/default/bin/lanyard.exe spec-count
```

Use an existing file under `test/fixtures` for `check`. The driver also
supports `check --print FILE` and `check --erased FILE`. The fork removed
the Wasm backend and runtime commands.

The kernel and its foundation documents are inherited from Kanon at
`046689a`. [SPEC.md](SPEC.md) and the older build-log sections record that
history. [KERNEL-CARRIED.md](dev/KERNEL-CARRIED.md) records the fork's carry
contract. Lanyard's current plan is in the sibling `lanyard-m0` directory.

Licensed under MIT OR Apache-2.0.
