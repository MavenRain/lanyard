# Database connections

The target printer supports closed aliases of the Db.connect schema:

```text
def Models : Type 0 := prod (Counter, Audit)
def Text : Type 0 := Bytes
def open : Text -> Db := Db.connect Models Text
def connect : Bytes -> Db := fun (url : Bytes) => open url
```

Counter and Audit must be declared models. A single model also works.
Products and aliases retain their declared model identities, even when
two models have the same structural layout. Empty selections, repeated
models and ordinary types that merely resemble models refuse. Product
order becomes the order of the Toasty models macro.

Text must normalize to the checked byte-list shape used by model text
fields. Aliases and different family names work. Conversion borrows the
list, checks every Nat element against 255 and validates UTF-8. It finishes
before the builder opens a connection. URLs reuse ModelByteRange and
ModelUtf8 errors from the text conversion. Empty text, Unicode and zero
bytes reach Toasty unchanged when they are valid UTF-8. Toasty decides
whether the resulting URL is supported.

The kernel checks the alias as an ordinary definition. Lowering retains
the two erased type arguments and resolves Db_connect only inside that
definition. Its wrapper remains a native function. The printer validates
the instance, catalog kind, checked type, quantities, effects, arity and
template slots. It emits the pinned builder template with a borrowed URL
and an awaited result. Callers inherit async execution and database error
propagation. No new axiom or kernel constructor is introduced.

This slice recognizes the exact closed alias form above. Inline generic
applications, eta-expanded aliases and partially supplied type arguments
remain refusals. An accepted alias does not enable a generic Db_connect
call elsewhere in the module. Existing foreign ownership rules apply:
bind a returned Db once and share its handle with subsequent operations.

```sh
zsh dev/gates.sh --stage E-connections
_build/default/bin/lanyard.exe emit --target test/fixtures/connections.lan
```

The cumulative gate keeps the earlier model, foreign and native checks.
Printer tests cover accepted selections, type aliases and metadata
refusals. The byte-exact golden runs with an instrumented library double
that checks lazy start, suspension, Send, cancellation, model selection,
URL contents, sharing and errors. Invalid text causes no connection call.
A complete generated function connects, pushes its schema and creates a
row. Mutations change model selection, replace the URL, remove an await,
truncate a byte or allow lossy UTF-8. Only the lost-await mutation is
expected to fail compilation; the others must fail the execution oracle.
Mutation edits apply to generated code before the harness is attached.

Prepare the same golden for a real SQLite probe:

```sh
python3 -P dev/prepare-models.py --connections \
  --toasty /path/to/toasty --lock dev/validation/stage-e-models/Cargo.lock
```

The preparation command requires the pinned Toasty commit and unchanged
tracked sources. It writes the supplied local path into the manifest at
`.gatework/connections-pinned/Cargo.toml`. The probe keeps the existing
lanyard-model-validation package name and dependency lock. Build with
Rust 1.98.1 and Cargo's offline and locked flags, using cached packages.
The probe opens only in-memory SQLite databases. It checks both selected
models, direct stored columns, lookup, duplicate keys, separate database
instances, shared inputs and rejected URLs. No external database is used.

The printer measurement includes rust/connection.ml. Numeric allowances
remain pending user rulings. Handler fusion, the full Todo crate and the
M0 driver remain ahead. This slice claims neither Stage E completion nor
M0 exit. Captures are recorded under dev/validation/stage-e-connections/.
