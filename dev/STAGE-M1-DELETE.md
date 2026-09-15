# M1 model deletion

Every model now exposes `ModelName.delete_by_id key db : prod ()`.
The operation removes the matching primary key from that model in that
connection. Missing keys and repeated deletion succeed with unit. Other
keys, models and connections retain their rows, and a deleted key can be
created again. The interpreter requires an initialized schema and a
registered model, as create and lookup already do.

```sh
zsh dev/dunecho.sh build
_build/default/bin/lanyard.exe run --print-model Counter test/fixtures/delete.lan
# Counter { id: 7, value: 23 }
zsh dev/gates.sh --stage M1-delete
```

The fixture creates keys 7 and 8, deletes 7 twice, deletes missing key 90,
recreates 7 with value 23, reads the preserved key 8, and returns key 7.
Scripted request handlers can delete through the shared `topcoat.db` handle.
Deletion also works inside a closure that returns a model. Function values
whose unit result has an erased layout retain the existing erasure refusal.

## Checked target contract

The new signature is:

```text
(0 M : Type 0) -> (0 Key : Type 0) -> (key : Key) -> (db : Db) -> prod ()
```

It carries `DbExec` and `toasty::Error`, and prints the pinned Toasty
`M::delete_by_id(&mut db, key).await?` call. The Toasty commit remains
`7bd502cbf44cc47f70db9f2b27ab35d77a096364`. Its generated deletion method
returns `toasty::Result<()>` in
`crates/toasty-macros/src/model/expand/filters.rs`, and the pinned
integration suite calls `User::delete_by_id(&mut db, user.id)`.
The signature digest changes to cover the new row; library identities
and the Topcoat signature and anchors stay at their existing pins.

The emitter validates the schema kind, checked type, quantities, effects,
arity and placeholders before generating the call. Keys use the existing
checked Nat conversion into `0..=i64::MAX`. The result has a runtime unit
representation, so deletion participates in effect sequencing. The crate
entry point retains its `Send` check.

## Validation

The stage gate runs the cumulative M1 request gate, 23 deletion unit checks,
nine CLI tests and four mutation controls. The mutations remove deletion,
ignore the key, ignore the model, and erase the emitted call. Each must
compile and fail its named behavioral assertion. Clean and restored controls
must pass.

The pinned native fixture can be prepared and run offline:

```sh
python3 -P dev/prepare-crate.py --toasty /path/to/toasty --topcoat /path/to/topcoat --source test/fixtures/delete.lan --print-model Counter --lock dev/validation/stage-e-todo/Cargo.lock --output .gatework/delete-pinned
```

Build that prepared manifest with the installed Rust toolchain and cached
dependencies, then run its `lanyard-program` binary. It must print exactly
`Counter { id: 7, value: 23 }` followed by a newline, with no stderr.
Frozen gate and native build/run captures, generated sources, lockfile and
hashes are recorded under `dev/validation/stage-m1-delete/`.

The catalog now has 16 rows and nine foreign types. A checked Todo module
discloses 19 foreign constants: 16 catalog rows and three model instances.
The axiom golden and exact inventory assertions include deletion explicitly.
Generated metadata grows from 104 to 110 lines. The proposed `A_sig` budget
stays 104, the trust policy remains proposed, and M0 remains pending.
