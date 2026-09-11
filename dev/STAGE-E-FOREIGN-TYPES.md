# Applied foreign types

The target printer accepts `Form T` and `Deferred T`, including nested
applications, aliases, native products and recursive native families.
Arguments remain typed from erasure through the Rust printer. A One
binder moves an opaque wrapper. A Many binder uses `Arc` and can stay
live across an await without requiring the wrapper to implement Clone.

```sh
zsh dev/gates.sh --stage E-foreign-types
_build/default/bin/lanyard.exe emit --target test/fixtures/foreign-types.lan
```

The eraser reads zero-quantity type applications from checked neutral
spines, in argument order. Other opaque expressions retain their refusal
path. A runtime-quantity type application checks that path in
`test/lan_foreign_types.py`. `TyForeign` now stores a constructor and a list of representations.
Its textual layout carries the same arguments through aggregate and
closure metadata. Recursive family discovery also traverses arguments.

The target policy checks the type row, universe, quantity list, effect
list and argument count before substituting the print template. The
printer keeps nested argument layouts when collecting declarations and
validating family metadata. The target files and their pin hashes have
not changed.

The cumulative gate retains every async, synchronous foreign and native
leg. New coverage includes:

- Six printer positives and twenty refusals, including malformed
  layouts, mismatched arguments, a closure argument of a foreign type,
  missing family metadata and catalog drift.
- A byte-exact golden for ten functions. It uses both nesting orders, a
  product argument, a recursive Bytes argument, alias normalization,
  moves, shared calls and two async bodies.
- Fifteen runtime observations with opaque wrappers that lack Clone.
  They check payloads, an unloaded Deferred, sharing, lazy start, actual
  suspension, cleanup, error return and both async bodies' Send bounds.
- Three mutations: copying an owned wrapper and changing its type
  argument fail compilation; replacing a moved payload with an unloaded
  Deferred compiles and fails the execution oracle.

The pinned API probe uses the exact same golden with
`test/foreign-types-pinned.rs`. It builds offline, checks both async
bodies as `Future + Send`, and executes seven synchronous observations.
It never constructs a database or polls a database future. Prepare it
with the two pinned checkouts and an existing dependency lockfile:

```sh
python3 -P dev/prepare-foreign-types.py \
  --toasty /path/to/toasty --topcoat /path/to/topcoat \
  --lock /path/to/Cargo.lock
```

The manifest is `.gatework/foreign-types-pinned/Cargo.toml`. Build it
with Rust 1.98.1, Cargo's `--offline --locked` flags and the existing
dependency target directory. The lockfile must resolve the two pinned
path dependencies for package `lanyard-foreign-validation` version
`0.0.0`. The preparation command verifies the checkout commits and
refuses tracked source changes. Validation captures, hashes and the
resolved manifest are in `validation/stage-e-foreign-types/`.

Foreign model schemas, foreign fields in generated aggregates, closure
arguments of a foreign type, runtime foreign closures and shared-to-owned
foreign copies remain refusals.
Form parsing and Deferred loading are library operations; this slice
only transports their opaque values. Model/schema printing, handler
fusion, the Todo crate golden and the M0 driver remain ahead.

The existing TRUSTED-LINES command measures the changed eraser, IR and
printer files. Their numeric allowances remain pending user rulings.
No Stage E completion or M0 exit is claimed.
