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
types, async database calls, and model create/lookup for Nat fields.
Db.connect, other model field types and the complete M0 driver remain ahead.
The generated signature allowance is proposed at 104 lines and awaits the
user's ruling. See [target documentation](target/README.md), the
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
The Todo crate golden is still pending.

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

Validate [Nat model schemas](dev/STAGE-E-MODELS.md):

```sh
zsh dev/gates.sh --stage E-models
_build/default/bin/lanyard.exe emit --target test/fixtures/models.lan
```

`Counter.create` and `Counter.get_by_id` print awaited Toasty operations.
The `id` field is the supplied primary key. Database fields use checked
integer conversions; overflow and negative stored values return an error.

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
