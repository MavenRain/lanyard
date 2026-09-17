# M1 natural-number text

`Text.from_nat Bytes value` renders a natural number as decimal text.
Zero becomes `b"0"`; other values have no leading zeros. Values beyond
`u64` work in both the interpreter and emitted Rust, including computed
values, aliases, and captured arguments.

```text
Text.concat Bytes b"/todos/" (Text.from_nat Bytes id)
```

The `todo-list.lan` fixture reads sorted Todo rows, uses decimal IDs in
links, escapes titles with `Html.text`, and constructs an HTML list.
Its seeded response contains ID 3 before ID 20:

```html
<ul><li><a href='/todos/3'>&lt;write&gt; &amp; test</a></li><li><a href='/todos/20'>café</a></li></ul>
```

```sh
_build/default/bin/lanyard.exe run --request /todos test/fixtures/todo-list.lan
_build/default/bin/lanyard.exe run --request / test/fixtures/nat-text.lan
zsh dev/gates.sh --stage M1-nat-text
```

The schema is `(0 Text : Type 0) -> (value : Nat) -> Text`. Its output
must be a closed, checked byte-list family. The type argument is erased;
the natural has shared quantity. The operation is synchronous and pure.
An effectful argument is evaluated once, and its effects are retained
when the formatted result is unused.

The interpreter uses its arbitrary-precision natural representation.
The Rust adapter reads the existing little-endian base-256 limbs and
accumulates decimal digits without narrowing the input. Each digit is
in `0..9`; each multiply-and-carry value is at most 2559 and fits in
`u16`. The helper is emitted only when the program uses this operation.
It adds no library dependency or foreign type. The existing SQL integer
range checks and recursive byte-list resource limits still apply.

The cumulative gate retains every concat-stage check and adds 45 OCaml
checks, seven CLI groups, 970 native decimal observations, and five
database observations in the interpreter. Decimal checks cover byte
boundaries through 1024 bits, deterministic larger values below 2048
bits, zero, leading zeros, arithmetic, closures, and link composition.
Four native mutations alter radix, limb order, zero, and carry behavior;
clean and restored controls must pass. The default Dune test alias also
includes the adapter unit suite.

The additional database harness checks empty, single-row, and sorted
multi-row pages against pinned Toasty/Topcoat. It also checks a database
write inside the natural argument and an unused formatted result.
Prepare a fresh native crate, build with Rust 1.98, and check its binary:

```sh
python3 -P test/lan_nat_text_database.py --prepare NEW-DIR --toasty TOASTY --topcoat TOPCOAT --lock LOCK
python3 -P test/lan_nat_text_database.py --check PATH-TO-LANYARD-PROGRAM
```

Captures, the generated native harness, and source hashes are retained
under `validation/stage-m1-nat-text/`. Native database compilation reports
15 generated unused-variable and dead-code warnings.

The staged captures stay frozen. The staged `receipt.json` keeps the
reduced schema of the capture round, with the keys `base`, `captures`,
`files`, `recorded_at`, `stage`, and `status`. It holds no axioms
capture, although the stage log records seven `LAN-AXIOMS` rows. The
stage script starts no capture, thus the full schema and the axioms
trio stay with the capture harness. A recapture with the full schema
and the axioms trio is deferred to the next capture round.

The catalog contains 27 proposed declarations and nine foreign types.
Todo reports 32 foreign constants. The generated catalog has 176 lines,
exceeding the pending proposed 104-line allowance by 72. This stage adds
no trust approval, library pin change, or M0 exit stamp.
