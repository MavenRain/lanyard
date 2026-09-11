# Target signatures

Stage B provides 15 proposed foreign declarations: nine type constants and
six constant or model schemas. The target layer builds as `lanyard_target`;
its `Target_generated` module exposes immutable metadata and total lookup.
Stage C instantiates schemas and checks their types before adding axioms.
The synchronous Stage E slice applies constant print rules through
`emit --target`, with `topcoat.db` and `topcoat.see_other` in its fixture.
Schema and async printing remain ahead. Stage B does not establish Rust
compilation or kernel soundness for a schema merely by generating metadata.

Run `zsh dev/gates.sh --stage B` from the repository. It builds the compiler
and generated library, checks the target pins, runs the mutation suite and
OCaml client, verifies kernel carry and the existing census, and measures the
trusted source. The external libraries are only read. To check source copies:

```sh
zsh dev/target-pin.sh --toasty /path/to/toasty --topcoat /path/to/topcoat
```

## Row format

Each non-comment line of a `.sig` file is a JSON object with five semantic
fields and two metadata fields. Duplicate keys and unknown fields are errors.

| Field | Meaning |
| --- | --- |
| `name` | Canonical foreign name, shared across both files. |
| `type` | Kernel type source or schema telescope, with named outer binders. |
| `quantities` | One of `0`, `1`, `w` per outer argument, in binder order. |
| `effects` | Distinct operation and error names; an empty list means pure. |
| `print` | Rust template with `#{argument}` placeholders. |
| `kind` | `type`, `constant`, or `schema`. |
| `status` | `PROPOSED` throughout Stage B. |

Runtime arguments must appear in the print rule; a `1` argument appears once.
Erased schema parameters may appear as compile-time type or model names, or
be absent from the printed code. A `?` requires an error in the effect row.
These are structural checks. Stage C checks every row with the kernel and
elaborates declared operation families. The generator does not parse the full kernel
grammar or certify arbitrary Rust templates.

`Model.create` is one schema, not a declaration for every model. Its `M` and
field syntax are instantiated by model elaboration. `Db.connect` similarly
receives a model inventory and a text representation. The text representation
is a schema parameter because the carried kernel refuses string literals;
The Stage C Todo example supplies a checked byte-list representation without
adding a tenth foreign atom. `prod ()` denotes the kernel's unit type.

The nine closed type names are `Db`, `Cx`, `Uri`, `Response`, `SeeOther`,
`Deferred`, `Form`, `toasty::Error` and `topcoat::Error`. `Deferred` and `Form`
each take one erased type argument. The generator checks this inventory, but
Stage C adds a kernel-backed R0-TARGET check and the ninth census line.

The six roadmap rows at the top of the Topcoat file are comments with
PROPOSED status. They create no usable constant and no acceptance claim.
Promotion requires an emitted fixture or a user-ratified NEVER decision;
Stage B deliberately rejects status changes in semantic rows.

## Pin checks

`PIN.json` records each HEAD, crate version, release tag and peeled release
commit, plus the digest of its signature file. Topcoat inherits its crate
version from the workspace; Toasty declares its version in its crate manifest.
`pin.sha256` contains the four byte-exact S3 fingerprints, including line
endings. The gate extracts the specified spans again before hashing them.

PIN compares the identity tuple. ANCHOR reads all four source spans. DIFF
compares all fingerprint bytes and both signature digests. It never updates a
baseline. Missing inputs, changed signatures, changed anchors, missing tags
and mismatched versions or revisions fail with the leg named.

The earlier plan described Topcoat as `v0.7.0` plus one commit. The current
local tag peels to `8ef6d803bf8bc4e269c4566a959d190a9ae21896`, while the pinned
HEAD remains `51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a` and the crate version
is `0.6.2`. Its checkout is shallow; `git describe --tags --long --match 'v*'`
reports `v0.6.2-9-g51caa01`. The gate records and verifies the independent
identities and makes no ancestor or distance claim about `v0.7.0`.
Toasty is `7bd502cbf44cc47f70db9f2b27ab35d77a096364`, version `0.6.1`, with
release tag `toasty-v0.6.1` at `c2e8cfbc163bab76cf27309f1a92eea4eaf91834`.

A future re-pin needs the reviewed signature edits, source fingerprint diff,
new identity tuple and affected emitted fixtures together. These four anchors
cover the selected Topcoat grammar sites, not every API in both libraries.

## Generated source and allowance

Dune generates `_build/default/target/target_generated.ml` from both `.sig`
files and `dev/gen-target.py`. It is deterministic, records a semantic digest,
and carries no absolute source paths. It is compiled into an OCaml library,
so a consumer does not parse signature files at runtime.

The generated module has 104 lines. S0-D1 requires the user to rule the
numeric `A_sig` allowance; the proposed allowance is exactly 104, without
margin. `dev/trusted-lines.sh` reports that measurement and keeps the ruled
formula `5481 + A_rir + A_emit + A_sig`. It does not claim an approved total.
