# SPIKE-ORDER, the price of the Order.translate extension

Spike S8, wave Order, alone and last.  Date 2026-09-09.  It prices fact
8 of M0-PLAN.md section 12, the road not taken at R-Q3.  R-Q3 is RULED
(RATIFICATIONS.md block (b)): Eff is monomorphised per signature, lib
order.ml is carried byte for byte, and no kernel change lands at M0.
This spike prices the alternative and stops.  It recommends nothing and
it reopens nothing.

The pin worktree /Users/oobi/Documents/kan-rust-lang-kanon-pin is read
only here.  The measured file was copied out of the pin first and every
count below is taken on the copy.  No build ran.  The pin binary was run
read only.

## 1 The copy and its line count

```
cp /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/order.ml /Users/oobi/Documents/lanyard-m0/spikes/s8/order.ml
wc -l /Users/oobi/Documents/lanyard-m0/spikes/s8/order.ml
```

Printed:

```
     510 /Users/oobi/Documents/lanyard-m0/spikes/s8/order.ml
```

The copy is 510 lines, as M0-PLAN.md section 2 and the Stage 0 brief
section 2 state.  Every line number in section 3 is a line of this copy.

## 2 The extension that is priced

The extension is the fix attack 2 F2 names: extend Order.translate, and
the walk that certifies what it validates, to descend through an
application of a function-typed field.  The pin refuses that shape
today.  In lib/order.ml the refusal has one cause, at lines 242 to 253:
`guarded_call` reads the argument at the candidate position, and an
argument that is a `Term.Out` node, which is an application, answers
`false` under the one rule the file ships.  The branch binder `k` of a
constructor field `stepI : (Nat -> EffI) -> EffI` is bound `Smaller` by
`elim_ok` at line 331, but the recursive call passes `k 0` and not `k`,
so the walk never reaches the status it already holds.

## 3 The arms the extension needs

One line per arm.  The site column is a line span of the copy in section
1.  The lines column is the net lines the arm adds, so an arm that is an
edit of an existing arm line adds none.  The arm count is read off the
copy.  The lines per arm are an estimate at the shape the file already
uses, with the doc comment every type and every reader in this file
carries.

| arm | site in the copy | what the arm needs | lines |
| --- | --- | --- | --- |
| 1 | type status, 28 to 31 | a fourth status for a binder that is a function-typed field of a `Smaller` constructor, with its doc line | 2 |
| 2 | smaller_at, 221 to 226 | the false arm names the new status, so the match stays exhaustive | 0 |
| 3 | principal_or_smaller_at, 228 to 235 | the false arm names the new status | 0 |
| 4 | a new reader above guarded_call, at 237 | decide that a `Term.Out` is a point application whose head is a `Term.Var` of the new status, through `spine` and `Term.as_apt`, with its doc comment | 12 |
| 5 | guarded_call, the `Term.Out` arm, 242 to 253 | call that reader in place of the `Structural -> false` answer, and keep the match on the rule that R1 requires | 4 |
| 6 | type step, 39 to 42 | a field that records that the step entered through a function-typed field, with its doc line | 2 |
| 7 | chain_at in elim_ok, 332 to 338 | set that field on the step it builds | 2 |
| 8 | binder_status in elim_ok, 331 | one status per binder in place of one status for the whole leg, since a function-typed field takes the new status while a first-order field stays `Smaller` | 3 |
| 9 | a new pusher beside under, 201 to 206 | push a per-binder status list, reading the field shapes of the constructor address | 10 |
| 10 | branch_ok in elim_ok, 349 to 356 | pass the constructor address to that pusher | 2 |
| 11 | the chain validation of translate_recursive, 492 to 509 | admit a step whose `st_ctor` is `None` when the new field is set, which is the arm that lets the field application through | 5 |
| 12 | the doc comment of translate, 457 to 462 | restate the disclosed deviation from brief 3.4, since Elim is now entered through a field application | 3 |

Total line delta: 45.  The arithmetic is 2 plus 0 plus 0 plus 12 plus 4
plus 2 plus 2 plus 3 plus 10 plus 2 plus 5 plus 3, which is 45.  Twelve
arms are needed and ten of them add lines.

## 4 The S1 headroom, quoted

Source: /Users/oobi/Documents/lanyard-m0/spikes/dev/SPIKE-TRUSTED.md,
section 1, which holds the line spike S1 printed:

```
TRUSTED-LINES kernel=3997/4000 encoder=246/600 OK
```

and states the headroom beside it:

```
- Headroom against 4000: 3.  The arithmetic is 4000 minus 3997 equals 3.
```

S1 also records, in its finding S1-F1, that the kernel bucket the script
measures is twelve files and not eight, and that lib/order.ml is one of
the twelve.  So the 510 lines of lib/order.ml are inside the 3997 and
every line this extension adds is spent against the headroom of 3.

## 5 The verdict on "three lines of headroom"

The headroom figure is CONFIRMED at 3 lines and the claim that the
Order.translate extension can be paid out of it is CORRECTED: the
extension needs about 45 lines across twelve arms, which is 42 lines
more than the headroom, so the TRUSTED-LINES ceiling has to rise in the
same commit that buys it.

R-Q3 is ruled and this record is informational.  Under the ruling the
extension is not written, lib/order.ml stays at 510 lines byte for byte,
and the headroom of 3 stays unspent.

## 6 The probe 2c handler file, rerun on the pin binary

The handler file was rebuilt from the transcript in
/Users/oobi/Documents/kan-rust-lang-design-verdict.md lines 215 to 219
and from /Users/oobi/Documents/kan-rust-lang-attack-2.md lines 29 to 38,
because the original lived in a scratchpad that is gone.  It is 7 lines
at /Users/oobi/Documents/lanyard-m0/spikes/s8/handler.kan:

```
mu EffI : Type 0 with
| pureI : Nat -> EffI
| stepI : (Nat -> EffI) -> EffI

def rec runI : EffI -> Nat := fun (e : EffI) => case e as x in EffI return Nat with | pureI n => n | stepI k => runI (k 0)

def main : Nat := runI (pureI 1)
```

The run, with the prebuilt pin binary read only:

```
/Users/oobi/Documents/kan-rust-lang-kanon-pin/_build/default/bin/kanon.exe check /Users/oobi/Documents/lanyard-m0/spikes/s8/handler.kan
```

Output, verbatim, and the exit status:

```
termination: recursive definition runI failed the structural termination guard
exit:1
```

That is the probe 2c result of attack 2 F2, reproduced on the pin at
046689a78ef6708404bd190dc86845cbee0bb36f.  No build ran.  The binary was
not rebuilt and no copy of it was built.

One control isolates the fold.  The same family, with the recursion and
the recursive call removed, is at
/Users/oobi/Documents/lanyard-m0/spikes/s8/handler-control.kan:

```
/Users/oobi/Documents/kan-rust-lang-kanon-pin/_build/default/bin/kanon.exe check /Users/oobi/Documents/lanyard-m0/spikes/s8/handler-control.kan
```

```
exit:0
```

So the response-exponent family types and its handler fold does not,
which is the shape the extension of section 3 would have to admit.

## 7 Command lines, verbatim

```
ls -d /Users/oobi/Documents/lanyard
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin status --porcelain | wc -l
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin rev-parse HEAD
git -C /Users/oobi/Documents/toasty rev-parse HEAD
git -C /Users/oobi/Documents/topcoat rev-parse HEAD
uptime
mkdir -p /Users/oobi/Documents/lanyard-m0/spikes/s8
cp /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/order.ml /Users/oobi/Documents/lanyard-m0/spikes/s8/order.ml
wc -l /Users/oobi/Documents/lanyard-m0/spikes/s8/order.ml
rg -n 'translate' /Users/oobi/Documents/lanyard-m0/spikes/s8/order.ml
awk 'NR>=200 && NR<=386' /Users/oobi/Documents/lanyard-m0/spikes/s8/order.ml
awk 'NR>=386 && NR<=510' /Users/oobi/Documents/lanyard-m0/spikes/s8/order.ml
ls -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/_build/default/bin/kanon.exe
/Users/oobi/Documents/kan-rust-lang-kanon-pin/_build/default/bin/kanon.exe --help
wc -l /Users/oobi/Documents/lanyard-m0/spikes/s8/handler.kan
/Users/oobi/Documents/kan-rust-lang-kanon-pin/_build/default/bin/kanon.exe check /Users/oobi/Documents/lanyard-m0/spikes/s8/handler.kan
/Users/oobi/Documents/kan-rust-lang-kanon-pin/_build/default/bin/kanon.exe check /Users/oobi/Documents/lanyard-m0/spikes/s8/handler-control.kan
uptime
du -sk /Users/oobi/Documents/lanyard-m0/spikes/s8
```

The two probe files were written with a quoted heredoc under
/Users/oobi/Documents/lanyard-m0/spikes/s8, and the control was made
from the handler through `sd` on standard input.

## 8 Load averages, NOISY, date and bytes left

```
uptime
 7:40  27 users, load averages: 13.49 14.65 15.99
```

```
uptime
 7:48  27 users, load averages: 22.49 25.16 20.91
```

The load average is above 4 at both readings, so the machine is NOISY by
the rule of M0-PLAN.md.  S8 prints no timing number, so no number here is
at risk from the load, and NOISY is recorded and never used to drop a
number or to rerun anything.

Date: 2026-09-09.

Bytes left on disk under this spike:

```
du -sk /Users/oobi/Documents/lanyard-m0/spikes/s8
32	/Users/oobi/Documents/lanyard-m0/spikes/s8
```

That is 32 KiB: the 510-line copy of order.ml and the two probe files.
No build output was made, so none was deleted.

## 9 Decision record S0-D6, the S8 line delta

RECORDED, not ruled.  The user rules.

- The arm count: the Order.translate extension needs twelve arms of
  lib/order.ml, ten of which add lines.  Section 3 lists them one per
  line with the site of each in the 510-line copy.
- The line delta: about 45 lines.
- The headroom: 3 lines, from S1 at
  /Users/oobi/Documents/lanyard-m0/spikes/dev/SPIKE-TRUSTED.md section 1.
- The verdict: "three lines of headroom" is CONFIRMED as the headroom
  figure and CORRECTED as a budget.  45 lines do not fit in 3, so the
  extension needs the TRUSTED-LINES ceiling to rise by at least 42 lines
  in the commit that buys it.
- The status: informational.  R-Q3 is ruled, fact 8 of M0-PLAN.md section
  12 closes only if the user reopens R-Q3, and this record makes no
  recommendation to reopen it.
