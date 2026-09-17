# M1 decimal text parsing

`Text.to_nat Bytes text` parses a nonempty sequence of ASCII decimal digits.
Leading zeros are accepted. The result is an arbitrary-precision natural,
including values beyond `u64`. Signs, surrounding whitespace, separators,
fractions, exponents, non-ASCII digits and embedded NUL bytes fail. Existing
byte-range and UTF-8 checks apply before parsing.

```text
Text.to_nat Bytes (Form.field Bytes body b"id")
```

The `text-nat.lan` fixture parses a form value and adds one. The
`todo-form-id.lan` fixture creates and fetches a Todo using a supplied ID,
then renders its title through `Html.text`:

```sh
_build/default/bin/lanyard.exe run --request / --form 'value=18446744073709551616' test/fixtures/text-nat.lan
_build/default/bin/lanyard.exe run --request /todos --form 'id=000257&title=%3Chello%3E' test/fixtures/todo-form-id.lan
zsh dev/gates.sh --stage M1-text-nat
```

The schema is `(0 Text : Type 0) -> (text : Text) -> Nat`. The text family
must be a closed checked byte list. The type argument is erased and the
text argument has shared quantity. Parsing is synchronous and records
the existing `topcoat::Error` effect used by fallible text adapters.
The interpreter uses `Bignum.of_decimal`. Emitted Rust uses `Nat::decimal`
with an explicit empty-input check and the existing `Error::Digit` case.
The helper is emitted only for programs that use the operation.

Arguments are evaluated once, including database writes. Unused parsed
results retain their effects and failures. Conversion does not widen the
SQL key range: model keys must still fit `0..=i64::MAX`. Existing recursive
byte-list and interpreter reduction limits remain in force. This slice
adds no library dependency or foreign type.

The cumulative gate retains the natural-number formatting checks and
adds 53 OCaml metadata and interpreter checks, nine CLI groups, 736 native
observations, seven interpreter database scenarios, and four native
mutations. Decimal cases cover byte boundaries through 1024 bits and
deterministic values below 2048 bits. Mutations change the radix, empty
input, plus-sign handling and zero acceptance, with clean and restored
controls. Dune's default test alias includes the new unit suite.
The stage creates and cleans a private temporary Git root outside the
Dune project for native ledger scopes and isolated mutation builds.

The separate native database harness checks create, update and delete
with parsed form IDs, once-only argument evaluation, retained unused
effects, the SQL range limit and retained parsing failures:

```sh
python3 -P test/lan_text_nat_database.py --prepare NEW-DIR --toasty TOASTY --topcoat TOPCOAT --lock LOCK
python3 -P test/lan_text_nat_database.py --check PATH-TO-LANYARD-PROGRAM
```

Validation captures, generated native sources and source hashes are in
`validation/stage-m1-text-nat/`. The receipt includes a separate axiom
capture and the full capture schema. The native database build reports
26 generated unused-variable and dead-code warnings.

The catalog has 28 proposed declarations and nine foreign types. Todo
reports 33 foreign constants. The generated catalog has 182 lines,
exceeding the proposed 104-line allowance by 78. Trust approval and the
M0 exit stamp remain pending; library revisions are unchanged.
