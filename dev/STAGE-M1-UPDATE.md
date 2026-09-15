# M1 model updates

Every model exposes `ModelName.update fields db : ModelName`. The fields
value has the model's full checked layout. Its `id` selects an existing
row in the supplied connection, and all fields replace that row's values.
The operation returns the updated model. Missing or deleted rows fail.
Repeated updates with the same values succeed. Other keys, models and
connections retain their rows.

```sh
zsh dev/dunecho.sh build
_build/default/bin/lanyard.exe run --print-model Task test/fixtures/update.lan
# Task { title: "updated", id: 7, completed: true, value: 23 }
zsh dev/gates.sh --stage M1-update
```

The fixture places `id` after the text field, updates text, Bool and Nat
fields, repeats the update, and reloads the row. Updates also work in
closures, with unused results, and through a scripted request's shared
`topcoat.db` handle. Key-only models are supported. The interpreter requires
a registered model and an initialized schema, as the other operations do.
It validates the complete replacement before changing the immutable store.

## Checked target contract

The new schema is:

```text
(0 M : Type 0) -> (fields : M) -> (db : Db) -> M
```

It carries `DbExec` and `toasty::Error`. The emitted code validates fields
using the existing i64, Boolean and UTF-8 conversions, obtains the existing
row with `get_by_id`, and applies Toasty's instance `update!` macro. The
macro assigns the same primary key and replaces every other scalar field.
The lookup and update are separate database operations; this slice provides
no transaction or concurrent-writer guarantee. The native update instance
returns the values used by Lanyard's checked result conversion.

The print rule follows the pinned Toasty implementation at
`7bd502cbf44cc47f70db9f2b27ab35d77a096364`, specifically
`crates/toasty-macros/src/update/expand.rs`,
`crates/toasty-macros/src/model/expand/update.rs`, and the instance-update
examples in `crates/toasty-driver-integration-suite/src/tests/crud_update_macro.rs`.
The source pin and Topcoat anchors stay unchanged. The signature digest
includes the new schema. The generated catalog grows to 17 rows, still
with nine foreign types, and Todo's axiom report includes 21 foreign
constants, including `Model_update` and `Todo_update`.

The print rule expands `#{fields}` two times. The first expansion builds
`__lan_fields`, whose `id` selects the row. The second expansion occurs
inside `update!`. The emitted block thus repeats each field conversion.
The conversions are pure, so the behavior does not change. A later
signature change can bind the converted key one time and expand the field
list only inside `update!`. That change moves the emitter slot set, the
digest in `target/PIN.json` and the needles in `test/lan_update.ml`. This
slice thus keeps the rule as pinned.

## Validation

The stage gate retains the cumulative M1 deletion gate, then runs 28 update
unit checks, 11 CLI tests and five mutations. Mutations remove the stored
update, broaden its key or model selection, accept a missing row, or erase
the emitted update call. Each must trigger its named behavioral failure;
the clean and restored controls must pass.

The emitted fixture builds offline with Rust 1.98.1 against the pinned
Toasty and Topcoat sources and runs on real in-memory SQLite. Its stdout
matches the interpreter exactly, with exit 0 and empty stderr. Cargo
reports five unused-code or unused-variable warnings. Captures, the emitted
crate, lockfile, inventory and source hashes are recorded under
`dev/validation/stage-m1-update/`.

Trust remains pending. The generated signature module measures 116 lines
against the existing proposed allowance of 104. This slice adds no policy
ruling or M0 exit stamp.
