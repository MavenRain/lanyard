# Kernel carried files

Each file below comes from kanon at the fork point
046689a78ef6708404bd190dc86845cbee0bb36f, short form 046689a.  The fork
carries 27 commits of history, so the fork point is a commit inside this
repository and `git show 046689a:PATH` reads the kanon bytes here.

The format is D-M0-5: one row per file with the path, the kanon commit,
VERBATIM or EDITED, and the reason for an EDITED row.  A VERBATIM row
carries `-` in the reason column, because a file that keeps its bytes
needs no reason.  dev/kernel-carry.sh reads this table and re-diffs every
row against the commit the row names.  It fails when a VERBATIM row
differs by one byte, when an EDITED row is identical to the fork point,
when an EDITED row gives no reason, or when a file of the trusted kernel
bucket has no row here.

| file | kanon commit | state | reason |
| --- | --- | --- | --- |
| lib/shape.ml | 046689a | VERBATIM | - |
| lib/term.ml | 046689a | VERBATIM | - |
| lib/rules.ml | 046689a | VERBATIM | - |
| lib/check.ml | 046689a | VERBATIM | - |
| lib/value.ml | 046689a | VERBATIM | - |
| lib/eval.ml | 046689a | VERBATIM | - |
| lib/conv.ml | 046689a | VERBATIM | - |
| lib/totality.ml | 046689a | VERBATIM | - |
| lib/positivity.ml | 046689a | VERBATIM | - |
| lib/global.ml | 046689a | VERBATIM | - |
| lib/order.ml | 046689a | VERBATIM | - |
| lib/bignum.ml | 046689a | VERBATIM | - |
| lib/erase.ml | 046689a | EDITED | Stage D: Rust IR, retained binder quantities, explicit runtime unit and foreign type identities. Stage E: typed closure signatures. quantity_runtime is unchanged. |

## 1 The row set

The first twelve rows are the kernel bucket that dev/trusted-lines.sh
reads.  Correction S1-F1 of spike S1 gives the count: the bucket holds
TWELVE files under lib/, not the eight the script header names.  The
eight named members shape.ml 60, term.ml 133, rules.ml 1481, check.ml
538, value.ml 137, eval.ml 297, conv.ml 396 and totality.ml 146 sum to
3188.  The four unnamed members positivity.ml 118, global.ml 130,
order.ml 510 and bignum.ml 51 add 809.  The total is 3997 of the 4000
bound, so the headroom is 3 (spikes/dev/SPIKE-TRUSTED.md section 3,
M0-PLAN.md:243-252).

The thirteenth row is lib/erase.ml at 1484 lines.  The pin gate does not
count it, and the honest M0 base counts it (S0-D1, RATIFICATIONS.md
block (e)).  3997 plus 1484 is 5481.

## 2 The state of each row at Stage A

Every one of the thirteen rows is VERBATIM at Stage A.  Stage A writes no
language code, so no kernel file changes here.  The leg proves the state,
row by row, against the fork point.

Two rows carry a named invariant of M0-PLAN.md:121-125:

- lib/shape.ml stays at 60 lines, so the shape rows of the R0 fenced
block keep their bytes.
- lib/rules.ml keeps `spar_word = "SPar arrives at M1"` at rules.ml:20,
which the SPar refusal reads at rules.ml:218 and rules.ml:247.

S1-F2 binds lib/order.ml.  Its 510 lines sit INSIDE the 3997, so every
Order.translate line spends the headroom of 3.  R-Q3 keeps responses
first order at M0, so the headroom stays unspent and no agent edits
lib/order.ml.

## 3 The rows that change after Stage A

lib/erase.ml is EDITED at Stage D and emits lib/rir.ml while retaining
`quantity_runtime` (M0-PLAN.md section 3). The other twelve rows stay
VERBATIM through M0. lib/erase_kan.ml preserves the original eraser for
the carried `.kan` driver and regression suite. Stage D checks its bytes
against `046689a:lib/erase.ml`; it is outside the Rust compilation path.

The trusted base is a separate ledger from this one.  The M0
TRUSTED-LINES ceiling is the formula `5481 + A_rir + A_emit + A_sig`
with no total, because the three allowances are OPEN user rulings
(S0-D1, D-M0-3, RATIFICATIONS.md Pending stamps).  A_rir is lib/rir.ml
at Stage D, A_emit is rust/emit.ml at Stage E and A_sig is the generated
signature module at Stage B.  The stage that writes each file puts its
number to the user.  No agent guesses one.

## 4 The source extension

The source extension of lanyard is `.lan` (R-Q1).  It enters the tree at
Stage A as this written rule and as no file, because the M0 fixture is a
Stage B to Stage E deliverable.  The carried kanon corpus keeps `.kan`,
so one glob separates the two.  A `.lan` file at Stage A is a stage
overrun.

## 5 The other carry ledger

dev/CARRIED.md and dev/carry-check.sh hold the vendored tot pin of the
fork.  They are carried kanon bytes and Stage A does not edit them.  This
file and dev/kernel-carry.sh are the kanon carry, and the two ledgers do
not overlap: CARRIED.md rows carry a tot origin sha and a diff count,
and the rows here carry the kanon fork point and demand zero difference.

## 6 The leg

`zsh dev/kernel-carry.sh` prints one row per file, then the row count,
then `KERNEL-CARRY OK` on exit 0, or the differing rows and
`KERNEL-CARRY FAIL` on exit 1.  The script takes its root from its own
path, so a copy of this repository under a scratch directory checks
itself.  It reads with rg and awk, and it calls no grep and no sed.

## 7 Native printer slice (2026-09-10)

rust/emit.ml is new trusted output code, including its generated Nat runtime.
It measured 335 lines at that slice. Section 10 records the current
measurement, and A_emit remains pending the user's numeric ruling.
bin/lanyard.ml adds emit --native and bin/dune links the printer library.
The kernel, the two erasers, the IR and surface lowering retain their Stage D
bytes. The native slice does not change the carry bucket or its ceiling.

## 8 Typed closure slice (2026-09-10)

lib/erase.ml now shares its typed function-chain traversal between closure
layouts and eta expansion. It measured 1479 lines. The twelve-file kernel
bucket, quantity_runtime, lib/erase_kan.ml and lib/rir.ml keep their bytes.
rust/emit.ml measured 437 lines with boxed closure and capture printing.
A_emit remains pending; the symbolic ceiling has not been ratified as a
numeric total. See STAGE-E-CLOSURES.md for behavior and validation.

## 9 Recursive family slice (2026-09-10)

lib/erase.ml measures 1500 lines after completing constructor metadata over
families referenced in signatures and nested fields. rust/emit.ml measured
535 lines with nominal enums, boxed payloads and family metadata validation.
The twelve-file kernel bucket, quantity_runtime, lib/erase_kan.ml, lib/rir.ml
and surface/lower.ml retain their previous bytes. A_emit remains pending;
no numeric total is ratified. See STAGE-E-RECURSIVE.md for behavior and tests.

## 10 Synchronous foreign slice (2026-09-10)

rust/emit.ml now shares the typed printer through an OCaml functor. Its
native policy refuses foreign types and calls; rust/foreign.ml supplies
the checked synchronous target policy. rust/template.ml tokenizes print
rules and binds arguments in telescope order. All three decide emitted
Rust and are measured together under A_emit: 575 + 52 + 71 = 698 lines.
The allowance and total ceiling remain pending numeric rulings.
The kernel, erasers, IR, surface lowering and target signature bytes retain
their previous values. See STAGE-E-FOREIGN.md for the supported boundary.
