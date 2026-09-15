# M1 ordered model lists

Every declared model exposes `ModelName.all db : ModelName.rows`. It
returns the rows in ascending numeric `id` order. An empty table returns
`ModelName.nil`; each nonempty node is `ModelName.cons head tail`.
The generated family is nominal, so lists of different models cannot be
interchanged even when their fields have identical layouts.

```text
model Counter with | id : Nat | value : Nat end

def first : Db -> Counter := fun (db : Db) =>
  match Counter.all db as self in Counter.rows return Counter with
  | Counter.nil => tuple (0, 0)
  | Counter.cons head tail => head
```

The interpreter requires a registered model and an initialized schema.
Listing preserves the store, sees earlier creates, updates and deletions,
and leaves existing list values unchanged by later writes. Models and
connections have separate rows. Nat, Bool and checked byte-list fields
retain the conversions used by single-row operations. The entire result
is collected in memory; pagination and streaming remain future work.

```sh
zsh dev/gates.sh --stage M1-all
_build/default/bin/lanyard.exe run --print-model Task test/fixtures/all.lan
# Task { title: "updated", id: 3, completed: true, value: 122 }
```

The fixture inserts out of key order, updates a row, deletes another row,
then selects the first remaining row and sums the values of the whole
list through a recursive checked function. It places `id` after the text
field and exercises all three scalar field types.

## Checked target contract

The schema is:

```text
(0 M : Type 0) -> (0 Rows : Type 0) -> (db : Db) -> Rows
```

Model elaboration generates the list family and specializes both erased
type parameters. It checks collisions for the generated `rows`, `nil`,
`cons` and `all` names. The target bridge verifies the list's two
constructors and its element layout before emitting Rust. Call metadata
must match the checked instance, schema, effects, arity and placeholders.

The print rule follows the ordered query in the pinned Topcoat Todo
example at `51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a`, lines 74 through 78.
It uses Toasty at `7bd502cbf44cc47f70db9f2b27ab35d77a096364`:

```rust
Model::all().order_by(Model::fields().id().asc()).exec(&mut db).await?
```

The emitter converts the returned vector into the generated recursive
list using a reverse `try_fold`. Each row uses checked scalar conversions;
errors propagate through the existing async database result. The operation
has `DbExec` and `toasty::Error` effects. It provides no transaction or
concurrent-writer guarantee across separate database operations.

The catalog contains 18 rows and nine foreign types. Todo's axiom report
contains 23 foreign constants, including `Model_all` and `Todo_all`.
Generated Rust goldens gain the model list declarations. The library
source pins and Topcoat anchors retain their original values.

## Validation

The stage gate retains the cumulative M1 update gate and adds 23 unit
checks, 12 CLI tests and five mutations. The mutations reverse key order,
include other models, drop a row, reverse the emitted query order, or
reverse the emitted list. Each must trigger its named failure, and clean
and restored controls must pass.

The emitted fixture builds offline with Rust 1.98.1 against the pinned
libraries and runs on in-memory SQLite. Its stdout matches the interpreter
exactly. The build reports 20 unused-code or unused-variable warnings.
Captures and source hashes are recorded under `dev/validation/stage-m1-all/`.

Trust remains pending. The generated signature module measures 122 lines
against the existing proposed allowance of 104. This slice introduces no
policy ruling or M0 exit stamp.
