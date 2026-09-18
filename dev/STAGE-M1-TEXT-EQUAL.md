# M1 exact text comparison

`Text.equal Bytes left right` compares two checked UTF-8 byte lists and
returns a Boolean: sum arm 0 means different, and arm 1 means equal.
Comparison preserves case, whitespace, embedded NULs and Unicode encoding.
It performs no trimming, case folding or Unicode normalization. Empty
inputs compare equal. Both inputs must pass byte-range and UTF-8 checks,
including identical malformed inputs and unused comparison results.

The form fixture chooses a response from the submitted action:

```sh
_build/default/bin/lanyard.exe run --request / --form 'action=save' test/fixtures/text-equal.lan
zsh dev/gates.sh --stage M1-text-equal
```

The schema is `(0 Text : Type 0) -> (left : Text) -> (right : Text) ->
sum ((prod () : Type 0), (prod () : Type 0))`. The type argument is a
closed checked byte-list family and is erased; both values have shared
quantity. The interpreter uses `String.equal`. Emitted Rust compares the
validated strings and converts the result to the existing Boolean sum.
The operation is synchronous and declares no library effect. Existing
adapter errors still propagate. No library dependency or foreign type is
added.

Arguments are evaluated once, from left to right, before byte-list
validation. Database argument effects and validation failures remain
observable when the comparison result is unused. Named aliases, captured
inputs and alternate byte-list families use the existing specialization
path. Function aliases are fully applied; a captured argument can be
passed through an explicit lambda under the existing calling convention.

The cumulative gate retains decimal parsing and adds 49 OCaml checks,
eight CLI groups, 256 interpreter text pairs, 266 native observations,
five interpreter database scenarios and five native mutations. Mutations
invert equality, compare lengths, accept prefixes, trim inputs or suppress
right-input validation. Clean and restored controls must pass.

The separate native database harness exercises equal and unequal values,
once-only ordered writes, retained unused effects, invalid UTF-8 and
argument evaluation before validation:

```sh
python3 -P test/lan_text_equal_database.py --prepare NEW-DIR --toasty TOASTY --topcoat TOPCOAT --lock LOCK
python3 -P test/lan_text_equal_database.py --check PATH-TO-LANYARD-PROGRAM
```

The recorded capture used LOCK =
dev/validation/stage-m1-text-nat/native/Cargo.lock, whose bytes are
identical to this stage lock.

The native database build reports 25 generated unused-variable and
dead-code warnings. The unused-result scenario reads back a row written
by the comparison; a control that omits the comparison must fail.

Validation captures, generated native sources and source hashes are in
`validation/stage-m1-text-equal/`. The catalog has 29 proposed declarations
and nine foreign types. Todo reports 34 foreign constants. The generated
catalog has 188 lines, exceeding the proposed 104-line allowance by 84.
Trust approval and the M0 exit stamp remain pending. The signature digest
changes for the new row; pinned library revisions and source anchors stay
the same.
