# Nat model schemas

The target command prints Toasty models whose fields normalize to Nat.
Each model requires an `id` field, used as a supplied primary key. Type
aliases normalize before validation. Field order follows the checked
model declaration, including models whose key is not the first field.

```sh
zsh dev/gates.sh --stage E-models
_build/default/bin/lanyard.exe emit --target test/fixtures/models.lan
```

`Model.create` and `Model.get_by_id` specialize to the checked model
instances. The printer verifies instance metadata, schema kind, kernel
type, quantities, effects, arity and template placeholders. It evaluates
arguments once in telescope order, clones the shared database handle
and prints an awaited call using the pinned template. The result returns
to the native structural record layout. Callers inherit async effects
and database error propagation.

The database carrier is i64. Writes and lookup keys reject Nat values
above `i64::MAX`; reads reject negative stored values. These errors use
`Error::ModelRange`. Native arithmetic keeps its arbitrary precision.
Every field is checked, including the key, and no truncating cast is
emitted. Rust model and field identifiers encode source names; `id`
retains the name needed by Toasty's generated lookup method. Fields are
private. Separate models retain separate Toasty types even when their
native structural layouts coincide. The printer pins the model of the
callee, not the model of the value. A value of any model with the same
native layout is accepted. Its slots map by position into the declared
column order of the callee model.

The `emit --native` command erases model declarations. It applies no
model field rule, so a bad field type refuses only on `--target`. A
model call still refuses on the native arm, because the Db foreign
type has no native printer. That refusal names no model rule.

The cumulative gate keeps every prior stage leg. It adds printer
positives and metadata refusals, a byte-exact golden, and compiled
observations for field order, ownership, lazy start, actual suspension,
Send bounds, error propagation and range checks. Four mutations remove
the negative guard, wrap an overflowing conversion, read the wrong
result field, or omit an await. The first three compile and fail the
execution oracle; the fourth fails compilation.

The default compiled test uses an explicit library double. Its derive
only registers the `key` attribute, and it does not implement storage.
The separate pinned probe compiles the same golden against the real
Toasty derive and runs create/lookup against an in-memory SQLite database.
It checks duplicate and missing keys, two models with the same native
layout, a non-leading key, a rejected write leaving no row, and rejection
of a negative value inserted through the Rust API.

Prepare that probe with the pinned checkout and an existing dependency
lockfile:

```sh
python3 -P dev/prepare-models.py \
  --toasty /path/to/toasty --lock /path/to/Cargo.lock
```

The manifest is `.gatework/models-pinned/Cargo.toml`. Resolve its lockfile
with Cargo, then build using Rust 1.98.1 and `--offline --locked`.
Dependencies must be cached first. The preparation command checks the
Toasty commit and refuses tracked source changes. If using gateledger,
initialize a Git repository in the probe directory so the parent's
ignored `.gatework` directory does not hide its inputs. The executable
is `lanyard-model-validation`; it opens only `sqlite::memory:`.
Validation captures and the resolved lockfile are recorded under
`dev/validation/stage-e-models/`.

Other model field types, Db.connect specialization, handler fusion,
the full Todo crate and the M0 driver remain ahead. This slice changes
no kernel, eraser, IR, target signature or pin bytes. The printer bucket
includes rust/model.ml; all numeric allowances remain pending rulings.
No Stage E completion or M0 exit is claimed.
