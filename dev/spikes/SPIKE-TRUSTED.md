# SPIKE-TRUSTED, the kernel bucket

Spike S1, wave Counts.  Date 2026-09-09.  It closes fact 1 of
M0-PLAN.md section 12: the kernel bucket at 3997 of 4000 was QUOTED from
the verdict and no probe measured it.  It is measured here.

The pin worktree /Users/oobi/Documents/kan-rust-lang-kanon-pin is read
only for this spike.  The script measures its own root and writes
nothing, so the pin did not move.  No build ran.

## 1 The printed pass line

```
TRUSTED-LINES kernel=3997/4000 encoder=246/600 OK
```

The command that printed it, verbatim:

```
zsh /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/trusted-lines.sh
```

Exit status 0.  The quoted figure holds.  The kernel bucket is 3997
lines against a bound of 4000, and the encoder bucket is 246 lines
against a bound of 600.

- Kernel number: 3997.
- Encoder number: 246.
- Headroom against 4000: 3.  The arithmetic is 4000 minus 3997 equals 3.
- Headroom against 600: 354.  The arithmetic is 600 minus 246 equals 354.

## 2 The members with their own line counts

The eight kernel members that M0-PLAN.md section 4 and the script header
name, each by `wc -l`:

```
wc -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/shape.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/term.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/rules.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/check.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/value.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/eval.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/conv.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/totality.ml
```

```
      60 lib/shape.ml
     133 lib/term.ml
    1481 lib/rules.ml
     538 lib/check.ml
     137 lib/value.ml
     297 lib/eval.ml
     396 lib/conv.ml
     146 lib/totality.ml
    3188 total
```

The one encoder member, by `wc -l`:

```
wc -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/wasm/gc_encode.ml
```

```
     246 wasm/gc_encode.ml
```

## 3 What the script actually reads: twelve files, not eight

The eight named kernel members sum to 3188, not to 3997.  The printed
kernel number comes from twelve files.  The script's own
`kernel_files` array holds four more files, each added by a later
ruling recorded in a comment beside it:

- lib/positivity.ml and lib/global.ml, "M1 Stage G, brief 3.10 and
  SG-D12:  the two files the mu shape adds join the believed list and
  the two budgets above do not move".
- lib/order.ml, "M1 Stage I, brief 3.10 and SI-D15:  the file that
  holds the structural order and the certificate joins the believed
  list".
- lib/bignum.ml, "Stage K SK-D1: the arbitrary precision host boundary
  is believed".

The four extra members, by `wc -l`:

```
wc -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/positivity.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/global.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/order.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/bignum.ml
```

```
     118 lib/positivity.ml
     130 lib/global.ml
     510 lib/order.ml
      51 lib/bignum.ml
     809 total
```

All twelve, as the script reads them:

```
wc -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/shape.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/term.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/rules.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/check.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/value.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/eval.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/conv.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/totality.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/positivity.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/global.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/order.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/bignum.ml
```

The total row prints 3997, which equals 3188 plus 809.  The printed
number is correct for the twelve-file bucket the script defines.  The
eight-file description in M0-PLAN.md section 4 and in the Stage 0 brief
section 2 is the one that is short.  Both numbers are recorded here and
neither is corrected in the pin, because the pin is read only and
because a description is not a measurement.  This is finding S1-F1.

The lib/order.ml row is load bearing for spike S8.  Its 510 lines are
inside the 3997, so an Order.translate extension spends the headroom of
3 directly.

## 4 Command lines, verbatim

```
ls -d /Users/oobi/Documents/lanyard
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin status --porcelain | wc -l
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin rev-parse HEAD
git -C /Users/oobi/Documents/toasty rev-parse HEAD
git -C /Users/oobi/Documents/topcoat rev-parse HEAD
uptime
zsh /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/trusted-lines.sh
uptime
wc -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/trusted-lines.sh
cat /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/trusted-lines.sh
wc -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/erase.ml
ls -d /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/rir.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/rust
du -sk /Users/oobi/Documents/lanyard-m0/spikes/s1
```

The two `wc -l` member commands of sections 2 and 3 are printed in full
beside their output above.  The script is 80 lines.

## 5 Load averages and the machine

`uptime` before the measured leg:

```
 6:49  27 users, load averages: 16.90 11.36 8.94
```

`uptime` after the measured leg:

```
 6:49  27 users, load averages: 16.90 11.36 8.94
```

S1 is a count spike, not a timing spike, so the load average of 16.90
does not make it NOISY.  A line count does not move with the load.  The
load is recorded because every measured leg records it.

Bytes left on disk under /Users/oobi/Documents/lanyard-m0/spikes/s1:
16 KB by `du -sk`.  The two runner scripts and their two logs are all
that is there.  No build output was made, so none was deleted.

## 6 Decision record S0-D1, the M0 TRUSTED-LINES ceiling, PROPOSED

Status: PROPOSED.  D-M0-3 gives this ruling to the user
(RATIFICATIONS.md block (c)), so no agent rules it.  It is not ruled
here.

The rule is M0-PLAN.md section 4: "The M0 ceiling is S1's printed number
plus erase.ml, rir.ml, rust/emit.ml and the generated signature module,
which is INSIDE the base per attack 3 F7".  M0-PLAN.md section 9 gives
the TRUSTED-LINES leg as "the base is at or under the M0 ceiling of
section 4" and states no separate margin, so the section 4 rule is the
one used and no margin term is added.

The arithmetic:

```
  3997   S1 printed kernel number, measured today
+ 1484   lib/erase.ml, measured today, wc -l on the pin
+ A_rir  lib/rir.ml, NOT YET WRITTEN, named allowance
+ A_emit rust/emit.ml, NOT YET WRITTEN, named allowance
+ A_sig  the generated signature module, NOT YET WRITTEN, named allowance
= 5481 + A_rir + A_emit + A_sig
```

PROPOSED ceiling: 5481 plus the three named allowances A_rir, A_emit and
A_sig.  The measured part is 5481.  The three allowances stay as names.
No line count is guessed for a file that does not exist, per the brief
section 3.2 and D-M0-3.

The two absent paths were checked:

```
ls: /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/rir.ml: No such file or directory
ls: /Users/oobi/Documents/kan-rust-lang-kanon-pin/rust: No such file or directory
```

The generated signature module has no path yet, because R-V3 puts the
two signature files at target/toasty-7bd502cb.sig and
target/topcoat-51caa01.sig and the module is generated from them at a
stage after Stage 0.

Three notes for the user who rules this:

- The 5481 figure is the honest M0 base of M0-PLAN.md section 4 and it
  matches the near 5481 the plan predicts.  It is 3997 plus 1484.
- The kernel bound of 4000 is a separate bound inside the script and it
  is not the ceiling.  It has headroom 3.  R-Q3 keeps lib/order.ml byte
  for byte at M0 so that headroom stays unspent.
- The ceiling covers the kernel bucket the script reads today, which is
  twelve files and not eight.  Section 3 above records that.

## 7 Gates

S0-G1, S0-G2 and S0-G3 ran at the start of this spike's window and again
at the end.  All printed lines are in section 8 of the S1 log files
/Users/oobi/Documents/lanyard-m0/spikes/s1/run1.log and
/Users/oobi/Documents/lanyard-m0/spikes/s1/run3.log.

S0-G4 asks this file to hold the printed TRUSTED-LINES line verbatim,
the headroom against 4000 as a number, the nine named members and
decision S0-D1 marked PROPOSED.  Section 1 holds the line and the
headroom 3.  Section 2 holds the nine named members with a line count
each, and section 3 holds the four the script adds.  Section 6 holds
S0-D1 marked PROPOSED.  No ceiling is stated as ruled.

## 8 Out of scope, and what did not happen

The pin was not changed.  Nothing was built.  No repository was created.
No file outside /Users/oobi/Documents/lanyard-m0/spikes was written.  No
number is given for a file that does not exist.  The ceiling is PROPOSED
and it is not ruled.
