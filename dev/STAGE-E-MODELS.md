# Scalar model schemas

The target command prints Toasty models whose fields normalize to Nat,
a sum of two units (Bool), or a checked byte list (text).
Each model requires a Nat `id` field, used as
a supplied primary key. Type aliases normalize before validation. Field
order follows the checked model declaration, including models whose key
is not the first field.

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

The database carrier for Nat is i64. Writes and lookup keys reject Nat
values above `i64::MAX`; reads reject negative stored values. These
errors use `Error::ModelRange`. Native arithmetic keeps its arbitrary
precision. Every field is checked, including the key, and no truncating
cast is emitted. Rust model and field identifiers encode source names;
`id` retains the name needed by Toasty's generated lookup method. Fields
are private. Separate models retain separate Toasty types even when
their native structural layouts coincide. The printer pins the model of
the callee, not the model of the value. A value of any model with the
same native layout is accepted. Its slots map by position into the
declared column order of the callee model.

Bool fields use Rust `bool` columns. Tag 0 maps to false and tag 1 maps
to true, matching `natEq` and `natLt`. Conversion uses exhaustive sum
matches on writes and Boolean conditionals on reads. The field's
normalized representation selects its carrier, so aliases work and a
type named `Bool` with a different layout receives that layout's rule.
Other sums, including sums with payloads or three unit legs, refuse.
Keys remain Nat; a Boolean key refuses before Rust is printed.

Text fields use Rust String columns. Their normalized family must have
two constructors in order: an empty constructor and a constructor with
a Nat head and a tail of the same family. The printer checks the erased
constructor metadata, including field order. Aliases and other family
names work; a type merely named Bytes receives no special treatment.
Other recursive shapes and text keys refuse before Rust is printed.

Writes traverse the borrowed list without consuming shared input. Each
Nat element must fit one byte, otherwise `Error::ModelByteRange` is
returned. `Error::ModelUtf8` rejects invalid UTF-8 without replacement.
Both checks finish before the database call, including checks of later
text columns. Reads reconstruct the native list in byte order. Empty
strings, Unicode and embedded zero bytes retain their exact contents.
Conversion uses iterator traversal; it adds no recursive Rust calls.
Unused model declarations still emit the family metadata needed by their
conversion functions. Native list representation and ownership rules
are unchanged.

The read path builds one linked node for each stored byte. The recursion
depth of the generated Drop, Clone and Debug glue is equal to the stored
byte length. The tested size is about 1 KB. A read bound is a numeric
allowance. An iterative Drop changes the native recursive representation
of every family. Both options stay a pending decision.

The fixture's `Flag` model mixes two Boolean columns and a Nat counter,
with its key in the second slot. Its creation functions cover shared
records and fresh values. Both true/false combinations are checked on
create and lookup, preserving column order and shared ownership.

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
Four further mutations corrupt false writes, true writes, Boolean reads,
or the selected Boolean result column. Each compiles and fails execution.

The default compiled test uses an explicit library double. Its derive
only registers the `key` attribute, and it does not implement storage.
The separate pinned probe compiles the same golden against the real
Toasty derive and runs create/lookup against an in-memory SQLite database.
It checks duplicate and missing keys, two models with the same native
layout, a non-leading key, a rejected write leaving no row, and rejection
of a negative value inserted through the Rust API.
For the mixed model it also inspects stored Boolean columns directly,
independently of the native conversion, and checks both lookup results,
duplicate keys and a rejected overflowing Nat write leaving no row.
The text model has two text columns, a Boolean column and a non-leading
key. Both probes cover shared and fresh rows, errors, column order and
Unicode contents. The pinned probe reads stored String columns directly,
checks empty values and native reads of externally inserted Unicode,
and verifies that invalid-byte and invalid-UTF-8 writes leave no row.
Five text mutations truncate a byte, allow lossy UTF-8, reverse a read,
select the wrong text column, or corrupt a zero byte. Each must compile
and fail the execution oracle. The oracle is added after mutation and
does not use the generated text conversions to check returned lists.

Prepare that probe with the pinned checkout and an existing dependency
lockfile:

```sh
python3 -P dev/prepare-models.py \
  --toasty /path/to/toasty --lock /path/to/Cargo.lock
```

dev/prepare-models.py writes the local Toasty checkout path given by
`--toasty` into the manifest, so the recorded manifest holds a local
path. That checkout must be at Toasty commit 7bd502cb, the revision
named in dev/M0-BUILD-LOG.md. The manifest is
`.gatework/models-pinned/Cargo.toml`. Resolve its lockfile with Cargo,
then build using Rust 1.98.1 and `--offline --locked`. Dependencies must
be cached first. The preparation command checks the Toasty commit and
refuses tracked source changes. If using gateledger, initialize a Git
repository in the probe directory so the parent's ignored `.gatework`
directory does not hide its inputs. The executable is
`lanyard-model-validation`; it opens only `sqlite::memory:`. Validation
captures and the resolved lockfile are recorded under
`dev/validation/stage-e-models/`.

Other model field types, Db.connect specialization, handler fusion,
the full Todo crate and the M0 driver remain ahead. This slice changes
no kernel, eraser, IR, target signature or pin bytes. The printer bucket
includes rust/model.ml; all numeric allowances remain pending rulings.
No Stage E completion or M0 exit is claimed.
The Todo example now passes its title-field check and still refuses its
handler's foreign aggregate layout. Handler fusion remains separate work.
