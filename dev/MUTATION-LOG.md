# M0 mutation log

## Stage 0

Both checks were rerun by the judge on 2026-09-05 on copies under /private/tmp/claude-501/-Users-oobi-Documents-claude4/3017512c-b634-4681-9bd6-97118fdb85ef/scratchpad/stage0.  No repository file was mutated; `git -C /Users/oobi/Documents/kanon status --porcelain -uall` still lists only paths under dev/.

### S0-M1 timer resolution

Mutation: copy dev/bench.sh to the scratch dir, then replace the nanosecond clock with a whole-second one.

Commands:

```
cp /Users/oobi/Documents/kanon/dev/bench.sh <scratch>/stage0/bench-m1.sh
sd 'time\.perf_counter_ns\(\)' 'int(time.time()) * 1000000000' <scratch>/stage0/bench-m1.sh
rg -c 'int\(time\.time\(\)\) \* 1000000000' <scratch>/stage0/bench-m1.sh
zsh <scratch>/stage0/bench-m1.sh sleep50 'sleep 0.05'
```

Both call sites were rewritten; `rg -c` printed `2`, and the only remaining mention of the old clock is the header comment.  The mutant printed `BENCH sleep50 median_ms=0.000 min_ms=0.000 max_ms=0.000 runs=5`.  The S0-G2 band is 40 to 150 ms, so the band check on the mutant is false while the same check on the real script passes with `median_ms=71.703`.

Result: killed.

### S0-M2 hash

Mutation: copy dev/denominators.json and dev/DENOMINATORS.sha256 to a scratch directory, then flip one byte in the JSON copy.  The judge flipped a different byte from the builder's run: the last character of the pin short hash.

Commands:

```
cp /Users/oobi/Documents/kanon/dev/denominators.json <scratch>/stage0/m2/denominators.json
cp /Users/oobi/Documents/kanon/dev/DENOMINATORS.sha256 <scratch>/stage0/m2/DENOMINATORS.sha256
sd '"tot_pin": "8cf0b8b"' '"tot_pin": "8cf0b8c"' <scratch>/stage0/m2/denominators.json
cmp -l /Users/oobi/Documents/kanon/dev/denominators.json <scratch>/stage0/m2/denominators.json
zsh -c "cd <scratch>/stage0/m2 && shasum -c DENOMINATORS.sha256"
```

`cmp -l` printed exactly one differing byte.  The check printed `denominators.json: FAILED` and `shasum: WARNING: 1 computed checksum did NOT match`, and exited 1, while the same check on the real pair prints `denominators.json: OK` and exits 0.

Result: killed.

## Stage A

Copies live under SCRATCH/stageA, one fresh copy per mutation, made with `rsync -a --exclude _build /Users/oobi/Documents/kanon/ SCRATCH/stageA/mN/`.  SCRATCH is /private/tmp/claude-501/-Users-oobi-Documents-claude4/3017512c-b634-4681-9bd6-97118fdb85ef/scratchpad.  The repository itself was never mutated.  The judge reran all three checks after the fix round.

### SA-M1 closed grammar

Mutation: a fixture that uses the reserved word `mu`, in a scratch fixtures directory of its own, so the repository's own ten fixtures stay untouched.

Commands:

```
printf 'def bad : Type := mu\n' > SCRATCH/stageA/fx/mu.kan
/Users/oobi/Documents/kanon/_build/default/test/main.exe SCRATCH/stageA/fx
```

The suite printed `PARSE mu FAIL: mu arrives at M1` then `PARSE-FAIL 0/1` and exited 1.

Result: killed.  Caught by the PARSE leg, through the parser's refusal of the reserved word (SA-D3).

### SA-M2 carry

Mutation: one line appended to lib/level.ml in a copy of the tree.

Commands:

```
rsync -a --exclude _build /Users/oobi/Documents/kanon/ SCRATCH/stageA/m2/
printf '\n(* mutation *)\n' >> SCRATCH/stageA/m2/lib/level.ml
zsh SCRATCH/stageA/m2/dev/carry-check.sh
```

The copy's own check printed `CARRY lib/level.ml diff=5 expected=2 header=OK FAIL`, then the other six OK rows, then `CARRY-FAIL`, and exited 1.  The copy ran its own script and read its own tree, which is what SA-D7 buys.

Result: killed.  Caught by the CARRY leg.

### SA-M3 R0 growth

Mutation: a sixth name added to `Shape.declared` in a second copy.

Commands:

```
rsync -a --exclude _build /Users/oobi/Documents/kanon/ SCRATCH/stageA/m3/
sd '"SNu" \]' '"SNu"; "SXx" ]' SCRATCH/stageA/m3/lib/shape.ml
zsh SCRATCH/stageA/m3/dev/dune.sh clean
zsh SCRATCH/stageA/m3/dev/dunecho.sh build
zsh SCRATCH/stageA/m3/dev/r0-count.sh
```

The copy built clean, `OK build: 0 errors, 0 warnings`, exit 0, so the mutant is a live program and not a compile error.  Its R0 check printed `3c3`, `< shapes declared 5: SPi SColl SPar SMu SNu`, `> shapes declared 6: SPi SColl SPar SMu SNu SXx`, then `R0-COUNT FAIL`, and exited 1.

Result: killed.  Caught by the R0-COUNT leg, because spec_count.ml counts with `List.length` over the very list that grew (a literal integer there would have let the mutant live).

## Stage B

Four mutations, brief section 5.  A fresh copy per mutation under SCRATCH/stageB, made with `rsync -a --exclude _build --exclude .gatework /Users/oobi/Documents/kanon/ SCRATCH/stageB/mN/`, never the repository itself.  Each copy builds with `zsh COPY/dev/dune.sh build` and runs with `COPY/_build/default/test/main.exe COPY/test`.  Each site carries a `(* SB-Mk site *)` comment, so `rg -n 'SB-Mk site' COPY/lib` finds it.

### SB-M1 function eta

Mutation: `expand_ran = Some spi_eta_ran` becomes `expand_ran = None` at the SB-M1 site of lib/rules.ml, so conv falls through to the head comparison at the right former of the point shape.

The copy built clean, `OK build: 0 errors, 0 warnings`, so the mutant is a live program.  Its suite printed `CHECK b01-function-eta FAIL: mismatch: the term has type (Out SPi 0 g (Ran SPi w _ A A) (APt 0 f) F) and the expected type is (Out SPi 0 g (Ran SPi w _ A A) (APt 0 (Sec SPi w x A [x => (Out SPi w _ A (APt w x) f)])) F)`, then `CHECK-OK 17/18`, `SUITE-KERNEL FAIL`, exit 1.

Result: killed.  Caught by the CHECK leg on b01-function-eta.

### SB-M2 proof irrelevance

Mutation: the arm `| () when is_prop ops ctx ty -> Ok true` is dropped at the SB-M2 site of lib/conv.ml, so conversion starts at the eta step.

The copy built clean.  Its suite printed `CHECK b05-proof-irrelevance FAIL: mismatch: the term has type (Out SPi 0 z P (APt 0 p1) G) and the expected type is (Out SPi 0 z P (APt 0 p2) G)`, then `CHECK-OK 17/18`, `SUITE-KERNEL FAIL`, exit 1.

Result: killed.  Caught by the CHECK leg on b05-proof-irrelevance.

### SB-M3 imax

Mutation: the body of `imax` at the SB-M3 site of lib/rules.ml becomes `Level.max l l'`, which drops the framework axiom of R-Q6.

The copy built clean.  Its suite printed `CHECK b06-impredicativity FAIL: universe: the former lives at 1 and the expected universe is 0`, then `CHECK-OK 17/18`, `SUITE-KERNEL FAIL`, exit 1.

Result: killed.  Caught by the CHECK leg on b06-impredicativity, which declares an arrow out of `Type 0` at `Prop`.

### SB-M4 closed shapes

Mutation: the SMu arm of `rules` at the SB-M4 site of lib/rules.ml answers `Ok (coll_pack ())` instead of `Error (Not_yet smu_word)`, so a shape M0 declares and does not admit gets the collection pack.

The site comment matters here:  the text `| Shape.SMu (_, _) -> Error (Error.Not_yet smu_word)` appears twice in rules.ml, at the shape equality and at `rules`, and only the second is the site.  A first attempt that edited the earlier occurrence did not build, `Error: Unbound value "coll_pack"`, and a dead mutant proves nothing, so the copy was made again and the anchored site was edited.

The second copy built clean.  Its suite printed `KNEG smu FAIL: the message is "the rule pack does not match the shape of the term"`, then `KNEG-OK 0/1`, `SUITE-KERNEL FAIL`, exit 1.

Result: killed.  Caught by the KNEG leg.  The mutant does not admit SMu quietly:  it gets a pack whose shape does not match, which the suite reads as the wrong message and refuses.

### Judge rerun of the four mutations (2026-09-05)

The judge remade one copy per mutation after the fix round, with `rsync -a --exclude _build --exclude .gatework /Users/oobi/Documents/kanon/ SCRATCH/judgeB/stageB/mN/`, and edited each site through an anchored replacement that first counts the anchor and stops when the count is not one.  This is the guard the SB-M4 trap of the first run needs:  the anchor holds the `(* SB-Mk site *)` comment line and the line under it, so the earlier identical arm of the shape equality cannot be edited by mistake.  The counts below are the counts of the fixed suite, 22 checked positives and 11 negatives, so they read one higher than the counts of the first run.

- SB-M1 function eta.  `expand_ran = Some spi_eta_ran;` becomes `expand_ran = None;` at lib/rules.ml.  The copy built clean, `m1-BUILD-EXIT=0`, and its suite printed `CHECK b01-function-eta FAIL: mismatch: the term has type (Out SPi 0 g (Ran SPi w _ A A) (APt 0 f) F) and the expected type is (Out SPi 0 g (Ran SPi w _ A A) (APt 0 (Sec SPi w x A [x => (Out SPi w _ A (APt w x) f)])) F)`, then `CHECK-OK 21/22`, `SUITE-KERNEL FAIL`, exit 1.  Killed.
- SB-M2 proof irrelevance.  The guard at lib/conv.ml becomes `| () when false && is_prop ops ctx ty -> Ok true`, so the step never fires and conversion starts at eta.  The copy built clean and its suite printed `CHECK b05-proof-irrelevance FAIL: mismatch: the term has type (Out SPi 0 z P (APt 0 p1) G) and the expected type is (Out SPi 0 z P (APt 0 p2) G)`, then `CHECK-OK 21/22`, `SUITE-KERNEL FAIL`, exit 1.  Killed.
- SB-M3 imax.  The body of `imax` at lib/rules.ml becomes `Level.max l l'`.  The copy built clean and its suite printed `CHECK b06-impredicativity FAIL: universe: the former lives at 1 and the expected universe is 0`, then `CHECK-OK 21/22`, `SUITE-KERNEL FAIL`, exit 1.  Killed.
- SB-M4 closed shapes.  The SMu arm of `rules` at lib/rules.ml answers `Ok (coll_pack ())`.  The copy built clean and its suite printed `KNEG smu FAIL: the message is "the rule pack does not match the shape of the term"`, then `KNEG-OK 0/1`, `SUITE-KERNEL FAIL`, exit 1.  Killed.

Four mutants of four are killed, each by the leg brief section 5 names.

## Stage C

Three mutations, brief section 5.  A fresh copy per mutation under SCRATCH/stageC, made with `rsync -a --exclude _build --exclude .gatework /Users/oobi/Documents/kanon/ SCRATCH/stageC/fmN/`, never the repository itself.  Each copy builds with `zsh COPY/dev/dune.sh build` and runs with `COPY/_build/default/test/main.exe COPY/test`.  Each site carries a `(* SC-Mk site *)` comment, so `rg -n 'SC-Mk site' COPY/lib` finds it:  lib/erase.ml:97 for SC-M1, lib/erase.ml:170 for SC-M2 and lib/totality.ml:51 for SC-M3.  The three runs below are the fix round's own (SC-D43).

### SC-M1 binder erasure

Mutation: `not (Quantity.equal q Quantity.Zero)` becomes `Quantity.equal q Quantity.Zero && false` at the SC-M1 site of lib/erase.ml, so `quantity_runtime` answers false for `One` and for `Many` as it does for `Zero`, and a runtime parameter is dropped.

The copy built clean, `fm1-BUILD-EXIT=0`, so the mutant is a live program.  Its suite printed `CHECK-OK 27/27`, then `ERASE c02-zero-binder FAIL: the erased form is not the golden text` with sixteen other ERASE FAIL lines, then `ERASE-OK 10/27`, `SUITE-KERNEL FAIL`, exit 1.

Result: killed.  Caught by the ERASE leg on c02-zero-binder, the line brief section 5 names.

### SC-M2 proof kept

Mutation: `Ok (not (Level.equal l Level.zero))` becomes `Ok (Level.equal l Level.zero || true)` at the SC-M2 site of lib/erase.ml, so `proof_free` answers true at a proposition type and a proof at a runtime position stays runtime instead of `KErased`.

The copy built clean, `fm2-BUILD-EXIT=0`.  Its suite printed `CHECK-OK 27/27`, then `ERASE c01-prop-argument FAIL: the erased form is not the golden text` with six other ERASE FAIL lines, b01, b02, b03, b04, b05 and b07, then `ERASE-OK 20/27`, `SUITE-KERNEL FAIL`, exit 1.

Result: killed.  Caught by the ERASE leg on c01-prop-argument, the line brief section 5 names.

### SC-M3 totality

Mutation: `if String.equal n name then Error (Error.Not_yet word) else Ok ()` becomes `if String.equal n name && false then Error (Error.Not_yet word) else Ok ()` at the SC-M3 site of lib/totality.ml, so `guard` answers `Ok None` whatever the body holds.

The copy built clean, `fm3-BUILD-EXIT=0`.  Its suite printed `CHECK-OK 27/27`, `ERASE-OK 27/27`, `NEG-OK 11/11`, then `KNEG self FAIL: the self reference is admitted at M0`, `KNEG-OK 1/2`, `SUITE-KERNEL FAIL`, exit 1.

Result: killed.  Caught by the KNEG leg on self, the line brief section 5 names.

Three mutants of three are killed, each by the leg brief section 5 names.

## Stage D

Three mutations, brief section 5.  A fresh copy for each mutation under
SCRATCH/stageD, made with `rsync -a --exclude _build --exclude .gatework
/Users/oobi/Documents/kanon/ SCRATCH/stageD/judge-mN/`, built with the
copy's own `dev/dunecho.sh build` and run with the copy's `test/wasm.exe`
over the copy's test directory and an OUTDIR under the copy.  The
repository was never mutated.  `rg -n SD-M ROOT/wasm` lists four marked
lines, one for SD-M1, one for SD-M3 and two for SD-M2, the encoder arm
and the emission site.

### SD-M1 LEB

Mutation: at the SD-M1 site of wasm/gc_encode.ml line 92,
`else byte (128 lor (n land 127)) ^ uleb (n lsr 7)` becomes
`else byte (n land 127) ^ uleb (n lsr 7)`, so the unsigned LEB128
encoder clears the continuation bit on every byte but the last.

The copy built clean, `OK build: 0 errors, 0 warnings`, so the mutant is
a live program.  Its suite printed `EMIT d01-lit-prims FAIL: validate:
[parse exception: invalid function section size, must equal types (at
0:48)]`, six more `FAIL: validate:` lines with `Section extends beyond
end of input`, one `FAIL: validate: [parse exception: invalid UTF-8
string (at 0:235)]` on d06, then `WASM-OK 2/10` and `SUITE-WASM FAIL`,
exit 1.  Only d08 and d10 stayed OK, because their indices are all
under 128.

Result: killed.  Caught by the validate leg brief section 5 names.

### SD-M2 return_call

Mutation: at the SD-M2 site of wasm/emit.ml line 387, the two lines
`if tail_ok c tail result then [ G.Return_call fi ]` and
`else [ G.Call fi ]` become `[ G.Call fi ]`, so a KTail at a direct call
is a plain call and the value falls through to the return.

The copy built clean, `OK build: 0 errors, 0 warnings`.  Its suite
printed `EMIT d02-tail-call FAIL: golden differs` and
`EMIT d03-pair FAIL: golden differs`, then `WASM-OK 8/10` and
`SUITE-WASM FAIL`, exit 1.

The mutant module still runs.  `node dev/run-node.mjs
COPY/wasmout/d02-tail-call.wasm main` printed `10` and exited 0, which
is the value the kernel gives for d02 and the value the unmutated
module prints.  `rg -c return_call` over the mutant `.wat` found no
line and exited 1, while the same sweep over
`test/golden/d02-tail-call.wat` printed `3`.

Result: killed.  Caught by the golden leg alone.  This is the proof
plan section 10 asks for:  behaviour did not change, the value is still
10 on node, and only the byte for byte golden saw the missing
return_call.

### SD-M3 tuple

Mutation: at the SD-M3 site of wasm/emit.ml line 308, a KStruct of three
fields builds a nested struct of the last two fields and then the outer
struct, so a 3 tuple becomes a pair whose second field is a pair.

The copy built clean, `OK build: 0 errors, 0 warnings`.  Its suite
printed `EMIT d04-tuple FAIL: emit: unbound: no type index for
tuple<i31,i31>`, then `WASM-OK 9/10` and `SUITE-WASM FAIL`, exit 1.  The
nested pair has no type index, because link.ml assigns an index only to
a tid the erased program names, and d04 names `tuple<i31,i31,i31>`
alone.

Brief section 5 asks for `golden differs` or `validate` at this site, so
the judge ran a second form on a fourth copy:  the same three field case
emits two `Struct_new` of the outer type instead of one, which is the
plan's own wording, "emit a tuple as two structs".  That copy also built
clean and its suite printed `EMIT d04-tuple FAIL: validate: [parse
exception: popping from empty stack (at 0:76)]`, `WASM-OK 9/10`,
`SUITE-WASM FAIL`, exit 1.

Result: killed, under both forms, and both times by d04 alone.

Three mutants of three are killed, each by the leg brief section 5
names.

## Stage D review regression sensitivity (2026-09-05)

The five new fixtures were run against the original staged backend in
the review scratch copy.  Its emitter, linker, encoder, erased form and
kernel/surface sources were verified against the current pre-fix index.
These are baseline comparisons, not new edits to the three Stage D
mutation sites above.

| fixture | original staged backend | corrected backend, kernel and both hosts |
| --- | --- | --- |
| d11-poly-pair | emits, then Node exits 1: illegal cast | 5 |
| d12-poly-case | emit exits 2: a case scrutinee is not a sum: any | 1 |
| d13-function-case | emit exits 2: a case scrutinee is not a sum: any | 1 |
| d14-generic-capture | emit exits 2: no type index for tuple<i31> | 11 |
| d15-generic-aggregates | emit exits 2: a case scrutinee is not a sum: any | 36 |

The corrected modules pass wasm-opt validation.  Node and Wasmtime exit
0 with the values above.  The emission suite independently computes
each expected value using the kernel, and reports WASM-OK 15/15.

## Stage E

Three mutations, each on its own fresh copy of the repository made with
`rsync -a --exclude _build --exclude .gatework`, built through the
copy's own dev/dunecho.sh, which printed `OK build: 0 errors, 0
warnings` for all three.  ROOT was never mutated.  The judge reran all
three at 2026-09-05 22:03.

### SE-M1 module

- Site.  The copy's wasm/emit.ml:717, the export wrapper of SD-D8.
- Edit.  `body = [ G.Call fi; G.I31_get_s ]` becomes
  `body = [ G.Call fi; G.I31_get_s; G.I32_const 1; G.I32_add ]`, so both
  hosts answer one more than the kernel.
- Killing line.  `zsh dev/gates.sh` printed `FAIL M0-E2E` and
  `GATES-FAIL`, exit 1.  SUITE-WASM also printed `FAIL SUITE-WASM`,
  because every emission fixture moved with the wrapper.  Every other
  leg still passed, among them
  `PASS M0-TIME median_ms=109.371 bound_ms=150`.
- The value `--host both` still printed.  `kanon run
  examples/m0-spine.kan --export main --host both` printed `522` and
  exit 0, against the spine's promise of 521.  The two hosts agree with
  each other and disagree with the kernel, which is what M0-E2E reads.

### SE-M2 one host

- Site.  The copy's dev/run-wasmtime.sh:47, the success arm.
- Edit.  `cat "$out"` becomes `awk '{ print $1 + 1 }' "$out"`, so the
  wasmtime host alone answers one too many.
- Killing line.  `kanon run examples/m0-spine.kan --export main --host
  both` printed `kanon: run: hosts disagree: node 521 wasmtime 522` and
  exit 3.  `zsh dev/gates.sh` printed `FAIL M0-E2E` and `GATES-FAIL`,
  exit 1.  M0-TIME failed with it, because the timed command is the same
  run and bench.sh reported `BENCH-ERROR m0_e2e exit=3`.

### SE-M3 timer

- Site.  The copy's dev/gates.sh:48, the bound of plan section 9 and
  correction C1.
- Edit.  `M0_TIME_MS=150` becomes `M0_TIME_MS=1`.
- Killing line.  `zsh dev/gates.sh` printed
  `FAIL M0-TIME median_ms=109.429 bound_ms=1` and `GATES-FAIL`, exit 1.
  The median carries three decimals and is far above 1, so the timer
  resolves milliseconds, which is what correction C1 asks the mutation
  to prove.  Every other leg still passed, among them
  `PASS M0-E2E main=521` and `PASS M0-RATIO ratio=0.288`.

## Lanyard M0 Stage B (2026-09-09)

`python3 -P test/target.py` passes 28 tests. Mutation source copies hold the
required upstream file bytes alone. They link no Git metadata, and they live
under `.gatework/` in the repository root. No test edits Toasty, Topcoat,
their references, or the committed Lanyard base.

| Mutation | Observed rejection |
| --- | --- |
| Flip one byte at each of the four S3 anchor spans, separately | TARGET-PIN DIFF FAIL in all four subtests |
| Remove an anchor file or truncate a bounded span | TARGET-PIN ANCHOR FAIL |
| Change Topcoat's inherited workspace version | TARGET-PIN PIN FAIL |
| Change Toasty's crate-local version | TARGET-PIN PIN FAIL |
| Change expected HEAD, release tag or peeled release commit | TARGET-PIN PIN FAIL for each identity field |
| Change a signature print rule without updating its frozen digest | TARGET-PIN DIFF FAIL |
| Delete a fingerprint line | TARGET-PIN DIFF FAIL |
| Delete a print field | Signature parser rejects the row; CLI exits 1 and preserves previous output |
| Add a tenth foreign atom, omit a required atom, or mislabel a universe result | Signature parser rejects the row |
| Duplicate a constant across files or duplicate a JSON key | Signature parser rejects the row |
| Remove an argument quantity or a runtime print placeholder | Signature parser rejects the row |
| Add an unknown or malformed print placeholder | Signature parser rejects the row |
| Drop the error effect of a question-mark print rule | Signature parser rejects the row |
| Print a One argument twice | Signature parser rejects the row |
| Claim PRINTED status before any fixture evidence | Signature parser rejects the row |

Positive controls cover the untouched pins, deterministic generation,
nine generated type constants, the exclusion of roadmap comments, UTF-8
and quote escaping, and splitting only outer arrows of a telescope.
A valid print-rule edit changes both generated metadata and its semantic
digest. The compiled OCaml client independently checks the create schema
and total lookup. These tests do not substitute for Stage E's EMIT-DIFF
mutation, because there is no Rust emitter yet.

## Lanyard Stage E native printer slice (2026-09-10)

The Stage B note above states that no Rust emitter exists. That note was
true on its date. rust/emit.ml held the printer at 335 lines on that
date. This slice carries the LAN-EMIT and LAN-NATIVE mutants below. The
deleted print rule mutation of EMIT-DIFF stays open.

The native control compiles with Rust 1.98.1 and matches 928 independent
Python integer observations. Both output mutants compile and run to exit
0, then disagree with that same oracle:

- Native arithmetic: change the emitted add method call to sub.
- Native Boolean tags: replace the true tag with the false tag.

Both are killed by test/lan_native.py. The combined E-native gate also
retains the seven Stage D erasure mutants. The foreign print-rule deletion
mutation still belongs to the remaining Todo crate printer slice.

## Lanyard Stage E typed closures (2026-09-10)

test/lan_closures.py runs three mutations after the control compiles and
matches 15 independent expected observations:

- Swap two captured Nat arguments in a lifted closure call. The mutant
  compiles and executes but gives the wrong capture-order result.
- Replace the saved offset in pack's duplication environment with zero.
  The mutant compiles and executes but calls through the owned clone give
  the wrong result after the original is dropped.
- Remove Send from the boxed callback bounds. Rust must reject the
  program with the thread-safety diagnostic. The control includes both
  Send + Sync and Future + Send bounds with a closure held across await.

All three were killed in the full Stage E run. The two prior native
mutants and seven erasure mutants remain green. Nine additional IR
refusals pin closure layout, lifted function, arity, capture and argument
diagnostics; the two former unsupported-closure cases now pin typed
errors. The three added erasure cases pin quantities, nullary signatures
and nested signatures before Rust printing.

## Lanyard Stage E recursive families (2026-09-10)

test/lan_recursive.py compares 13 observations against literal expected
results, then runs three mutations:

- Reverse the two same-typed Tree fields in treeScore's case payload.
  The mutant must compile and produce a different order-sensitive score.
- Change choice's constructor tag from first to second, retaining its Nat
  payload. The mutant must compile and change the observed result.
- Remove Box from nominal enum payload types. The mutant must fail
  compilation with the infinite-size diagnostic.

All three were killed in the cumulative Stage E gate. The existing seven
erasure, two arithmetic and three closure mutants also passed. A separate
positive probe emits an identity signature whose family references two
other families without constructing or matching any of them, checking
transitive metadata completion. Eighteen new malformed-IR refusal rows
and one duplicate-metadata success row exercise the printer boundary.
The foreign print-rule deletion mutation remains in the pending Todo slice.
## Lanyard Stage E synchronous foreign constants (2026-09-10)

test/lan_foreign.py exercises three non-vacuity controls against generated
code and template expansions:

- Reverse the evaluation order of two same-typed arguments. The mutant
  compiles, then its order-sensitive values differ from the oracle.
- Evaluate a repeated Many slot again instead of borrowing its stored
  value. The mutant compiles, then values and the evaluation count differ.
- Pass an Arc directly where the pinned context helper requires a Cx
  reference. The strict API double rejects the mutant for its argument type.

The OCaml suite additionally removes a used entry from the catalog and
requires a missing-print-rule error. It rejects altered print text, effects,
names, type arguments, arities, permuted catalog quantities and non-atomic
call types. The Todo crate's deleted-print-rule
EMIT-DIFF mutation remains future work with model and async printing.

## Lanyard Stage E async database constants (2026-09-10)

`test/lan_async.py` checks the exact async golden, then kills four mutants:

- Swallow the database error after awaiting it. This must compile, then
  violate the error and later-call observations.
- Remove the foreign await. Rust must reject `?` on the unpolled future.
- Reverse two sequential pushes. This must compile, then violate the order
  and early-error observations with distinct database identifiers.
- Replace Arc with Rc. The explicit Future + Send bounds must reject the
  generated futures, including a URI retained across suspension.

Baseline: 17 runtime observations; mutants killed: 4/4. LAN-ASYNC-EMIT also
rejects direct and mutual async recursion, direct and transitive async
closures, forged effects and missing async print rules. It also pins the
printed text of a synchronous call in an async function. Existing Stage E
native and foreign mutations remain in the cumulative gate. The Todo crate
EMIT-DIFF mutation remains pending with model printing and handler fusion.

## Lanyard Stage E applied foreign types (2026-09-11)

`python3 -P test/lan_foreign_types.py` compares the emitted bytes to
`test/goldens/foreign-types.rs`, then compiles and executes 15 runtime
observations with Rust 1.98.1. It checks these three mutations:

- Copy an owned Deferred instead of moving it. The wrapper double has
  no Clone implementation, so compilation fails at the copy. The real
  Toasty Deferred and the real Topcoat Form both derive Clone, so this
  compile failure is a property of the python doubles. The printer
  policy itself is pinned by the `clone of an owned foreign value`
  refusal row of `test/lan_foreign_types_emit.ml`.
- Change Form Uri to Form Nat. Compilation fails with a type mismatch
  when the harness supplies the checked URI payload.
- Replace the moved Deferred payload with an unloaded Deferred. This
  compiles and execution fails when the oracle reads the lost payload.

All 3 mutations are killed. The 6 positive and 20 negative printer
cases include catalog quantity, effect, result and placeholder drift,
bad argument counts, malformed layouts, a closure argument of a foreign
type and missing family metadata. The 5 source refusal cases add a
runtime-quantity type application and a runtime index argument, which
both take the opaque fallback.
Earlier native, recursive, closure, foreign and async mutations remain
in the cumulative E-foreign-types gate.

Review round 2 mutated the applied branch of `repr_of` in
`lib/erase.ml` lines 244 to 249 twice. The first mutant forces the
universe test to `if true || Option.is_some (Value.as_univ domain)
then`. It builds and the `index-argument` row kills it with
`LAN-FOREIGN-TYPES FAIL: index-argument refusal differs: not yet: Rust
emission: foreign type 3`. The second mutant relaxes the argument
pattern `Value.VAPt (Quantity.Zero, value)` to `Value.VAPt (_q,
value)`. It builds and it survives the whole suite. The checker gives
an application the quantity of its binder, so a Zero `PPoint` never
meets a non-Zero `VAPt`, and the mutant is unreachable from checked
source. The code keeps the Zero pattern as a defensive guard. To delete
the pattern or to keep it is a user ruling.

## Nat model schemas (2026-09-11)

test/lan_models.py compiles the exact golden with an explicit library
double and records 14 runtime observations. Its four controls are:

- Disable the negative database-value guard. The mutant compiles and
  fails the negative-value observation.
- Replace checked Nat-to-i64 arithmetic with wrapping arithmetic. The
  mutant compiles and fails the overflow observation.
- Read a model's value field into its native key field. The mutant
  compiles and fails the create result observation.
- Remove await from create. The mutant fails compilation.

All four controls were killed. The printer unit suite has 6 positives
and 18 refusals, including forged instances, schema type/quantity/effect
drift, and missing or additional print-rule placeholders. The real
Toasty/SQLite probe separately passed 18 observations using the same
golden. Its storage observations cover duplicate/missing keys, model
isolation, a non-leading key, rejected writes and negative stored values.

The earlier foreign gate now checks unsupported model fields, including
Todo.title, in place of its blanket schema refusal. Schema calls for
models with Nat fields are positive coverage in the new slice. No prior
native, closure, recursive, foreign or async mutation was removed.

## Boolean model fields (2026-09-11)

The model oracle now passes 28 compiled observations and kills eight
mutations. The four additional controls corrupt false writes, true
writes, Boolean reads or the selected Boolean result column. Each
mutant must compile and then fail execution. The fixture gives its two
Boolean columns opposite values and exercises both combinations.

The Nat result-field mutation now targets `f0` of Counter explicitly.
Its previous unqualified replacement also rewrote Flag's key read to a
nonexistent value column and failed compilation. The scoped mutation
still corrupts Counter's key, compiles and fails the create observation.
The other three Nat and await controls retain their targets and verdicts.

The printer suite has 9 positives and 22 refusals. New cases cover
aliases, anonymous two-unit sums, a misleading Bool name, Boolean keys,
payload sums and three-unit sums. The real Toasty/SQLite probe passes
28 observations, including direct stored-value checks that do not use
the printer's Boolean read conversion. Final captures are recorded in
dev/validation/stage-e-model-bools/.
