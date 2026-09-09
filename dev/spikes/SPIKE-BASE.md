# SPIKE-BASE, spike S6, the emitter baseline

Date: 2026-09-09.  Wave: Counts.  Fact 6 of M0-PLAN.md section 12, the
246-line encoder citation.  The plan closes that citation and this file
records it in the tree.  Nothing here is ruled and nothing here builds.

Pin worktree: /Users/oobi/Documents/kan-rust-lang-kanon-pin at
046689a78ef6708404bd190dc86845cbee0bb36f.  The worktree is READ ONLY for
this spike.  No file inside it was written and no build ran.

## 1 The four numbers

Command, verbatim:

```
wc -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/wasm/emit.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/wasm/link.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/wasm/gc_encode.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/erase.ml
```

Printed output, verbatim:

```
    1123 /Users/oobi/Documents/kan-rust-lang-kanon-pin/wasm/emit.ml
    1162 /Users/oobi/Documents/kan-rust-lang-kanon-pin/wasm/link.ml
     246 /Users/oobi/Documents/kan-rust-lang-kanon-pin/wasm/gc_encode.ml
    1484 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/erase.ml
    4015 total
```

The four expected numbers are wasm/emit.ml 1123, wasm/link.ml 1162,
wasm/gc_encode.ml 246 and lib/erase.ml 1484.  All four printed numbers
equal the expected numbers.  There is no difference and there is no
finding on this leg.  The disputed 246-line encoder citation is correct:
wasm/gc_encode.ml is 246 lines.

## 2 The twelve-file gate list

The list is read out of the gate script itself, so it is the script's
own list and not a retyped one.  Commands, verbatim:

```
rg -o '\$root/lib/[a-z_0-9]+\.ml' /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/trusted-lines.sh > /Users/oobi/Documents/lanyard-m0/spikes/s6/gate-list-raw.txt
sd '\$root' "/Users/oobi/Documents/kan-rust-lang-kanon-pin" < /Users/oobi/Documents/lanyard-m0/spikes/s6/gate-list-raw.txt > /Users/oobi/Documents/lanyard-m0/spikes/s6/gate-list.txt
wc -l < /Users/oobi/Documents/lanyard-m0/spikes/s6/gate-list.txt
wc -l ${(f)"$(cat /Users/oobi/Documents/lanyard-m0/spikes/s6/gate-list.txt)"}
```

The `sd` call reads the pin file through the rg output and writes into
the S6 scratch directory, so no pin path is ever an `sd` argument.  The
list has 12 members by `wc -l < gate-list.txt`, which printed 12.

Printed output, verbatim:

```
      60 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/shape.ml
     133 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/term.ml
    1481 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/rules.ml
     538 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/check.ml
     137 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/value.ml
     297 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/eval.ml
     396 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/conv.ml
     146 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/totality.ml
     118 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/positivity.ml
     130 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/global.ml
     510 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/order.ml
      51 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/bignum.ml
    3997 total
```

The twelve members with a count each:

| # | file | lines |
| --- | --- | --- |
| 1 | lib/shape.ml | 60 |
| 2 | lib/term.ml | 133 |
| 3 | lib/rules.ml | 1481 |
| 4 | lib/check.ml | 538 |
| 5 | lib/value.ml | 137 |
| 6 | lib/eval.ml | 297 |
| 7 | lib/conv.ml | 396 |
| 8 | lib/totality.ml | 146 |
| 9 | lib/positivity.ml | 118 |
| 10 | lib/global.ml | 130 |
| 11 | lib/order.ml | 510 |
| 12 | lib/bignum.ml | 51 |

Sum of the twelve members: 60 + 133 + 1481 + 538 + 137 + 297 + 396 +
146 + 118 + 130 + 510 + 51 = 3997.  The `wc -l` total row prints the
same 3997, so the members and the total agree.

The gate script holds one more file outside this list, the encoder
bucket wasm/gc_encode.ml at 246 lines.  The encoder is a second bucket
with its own bound of 600 and it is not a member of the twelve-file
kernel list.  lib/order.ml reads 510 lines, which matches R-Q3 and the
S8 input.

## 3 The honest M0 base

M0-PLAN.md section 4 states the honest M0 base near 5481 lines once
lib/erase.ml at 1484 is counted, which the pin's twelve-file gate does
not count.  The arithmetic, with every member named:

```
twelve-file gate list (kernel bucket)              3997
  lib/shape.ml 60, lib/term.ml 133, lib/rules.ml 1481,
  lib/check.ml 538, lib/value.ml 137, lib/eval.ml 297,
  lib/conv.ml 396, lib/totality.ml 146, lib/positivity.ml 118,
  lib/global.ml 130, lib/order.ml 510, lib/bignum.ml 51
plus lib/erase.ml                                + 1484
                                                 ------
honest M0 base                                     5481
```

3997 + 1484 = 5481.  The base is exactly 5481 lines, so "near 5481" in
the plan is met on the nose.

The base carries thirteen files: the twelve of the gate list plus
lib/erase.ml.

## 4 The difference against the gate's own total

The gate's own kernel total is 3997 and its encoder bucket prints 246
beside it.  Two differences are worth the record:

- Base minus the kernel total: 5481 - 3997 = 1484.  One file explains
  the whole difference, lib/erase.ml at 1484 lines.  The twelve-file
  gate list does not name lib/erase.ml, so the gate does not count it.
- Base minus the two printed buckets together: 5481 - (3997 + 246) =
  5481 - 4243 = 1238.  Two files explain this one, lib/erase.ml at
  +1484 and wasm/gc_encode.ml at -246.  The encoder file leaves the
  base because R-V2 deletes wasm/gc_encode.ml at the fork commit, with
  wasm/emit.ml at 1123 and wasm/link.ml at 1162 and runtime/.

The three deleted wasm files total 1123 + 1162 + 246 = 2531 lines.
Those lines are outside the M0 base for that reason and not because any
count moved.

No ceiling arithmetic runs in this spike.  The M0 TRUSTED-LINES ceiling
is decision S0-D1 and it belongs to spike S1, which prints the kernel
number the ceiling is built from.  This file states the base only.

## 5 Commands, verbatim

The two runner scripts are
/Users/oobi/Documents/lanyard-m0/spikes/s6/run1.sh and
/Users/oobi/Documents/lanyard-m0/spikes/s6/run2.sh, and their logs are
run1.log and run2.log beside them.  Every command line this spike ran:

```
zsh /Users/oobi/Documents/lanyard-m0/spikes/s6/run1.sh
uptime
ls -d /Users/oobi/Documents/lanyard
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin status --porcelain | wc -l
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin rev-parse HEAD
git -C /Users/oobi/Documents/toasty rev-parse HEAD
git -C /Users/oobi/Documents/topcoat rev-parse HEAD
wc -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/wasm/emit.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/wasm/link.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/wasm/gc_encode.ml /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/erase.ml
rg -o '\$root/lib/[a-z_0-9]+\.ml' /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/trusted-lines.sh > /Users/oobi/Documents/lanyard-m0/spikes/s6/gate-list-raw.txt
sd '\$root' "/Users/oobi/Documents/kan-rust-lang-kanon-pin" < /Users/oobi/Documents/lanyard-m0/spikes/s6/gate-list-raw.txt > /Users/oobi/Documents/lanyard-m0/spikes/s6/gate-list.txt
wc -l < /Users/oobi/Documents/lanyard-m0/spikes/s6/gate-list.txt
cat /Users/oobi/Documents/lanyard-m0/spikes/s6/gate-list.txt
wc -l ${(f)"$(cat /Users/oobi/Documents/lanyard-m0/spikes/s6/gate-list.txt)"}
zsh /Users/oobi/Documents/lanyard-m0/spikes/s6/run2.sh
du -sk /Users/oobi/Documents/lanyard-m0/spikes/s6
df -g /System/Volumes/Data | tail -1
```

Each Bash call carried the suffix ` # [skip-disk]` for the disk-floor
interlock of the brief section 8.

## 6 Gates

S0-G9 BASE passes: this file holds the `wc -l` output reading
wasm/emit.ml 1123, wasm/link.ml 1162, wasm/gc_encode.ml 246 and
lib/erase.ml 1484 in section 1, the twelve gate-list members with a
count each in section 2, and the honest base 5481 with its members
named in section 3.

The three window gates of this spike, run at the start of the work and
again at the end.  Printed lines, verbatim:

```
S0-G1 start:  ls: /Users/oobi/Documents/lanyard: No such file or directory
S0-G1 end:    ls: /Users/oobi/Documents/lanyard: No such file or directory
S0-G2 start:  0
S0-G2 start:  046689a78ef6708404bd190dc86845cbee0bb36f
S0-G2 end:    0
S0-G2 end:    046689a78ef6708404bd190dc86845cbee0bb36f
S0-G3 start:  7bd502cbf44cc47f70db9f2b27ab35d77a096364
S0-G3 start:  51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a
S0-G3 end:    7bd502cbf44cc47f70db9f2b27ab35d77a096364
S0-G3 end:    51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a
```

The start pair and the end pair agree, so the pin did not move inside
this window.

## 7 Load, NOISY and disk

Printed `uptime` lines, verbatim:

```
before:  6:49  27 users, load averages: 17.82 11.09 8.78
after:   6:49  27 users, load averages: 17.82 11.09 8.78
end:     6:49  27 users, load averages: 15.31 11.20 8.91
```

Load average before the measured leg: 17.82.  Load average after the
measured leg: 17.82.  The end gates read 15.31.

NOISY does not apply to this spike.  The plan marks a timing spike
NOISY above load average 4, and S6 measures lines and not time.  The
load average is 17.82, well above 4, and a line count does not move
with it.  Every number here is exact and repeatable at any load.

Bytes left on disk under the S6 scratch directory, from
`du -sk /Users/oobi/Documents/lanyard-m0/spikes/s6`:

```
24	/Users/oobi/Documents/lanyard-m0/spikes/s6
```

That reading was taken at the end of the counting legs.  The same
command after the last gate leg prints:

```
32	/Users/oobi/Documents/lanyard-m0/spikes/s6
```

That is 32 KiB, and it is the three runner scripts, the three logs and
the two gate-list files.  No build output was made, so nothing was
deleted.
The 50 MB limit of S0-B5 is not near.

Disk, from `df -g /System/Volumes/Data | tail -1`:

```
/dev/disk3s5       460  353        28    93% 6684661 299764600    2%   /System/Volumes/Data
```

The free figure is 28 GiB.  Blocker S0-B6 wants 29 GiB or more, so this
reading FIRES S0-B6 and the number is reported.  Nothing was deleted to
recover it, per the brief section 8.  This spike wrote 24 KiB of text
and ran no build, so it did not cause the reading.

## 8 Findings

None on the four numbers.  1123, 1162, 246 and 1484 all printed as the
plan states, so no number needed a correction of any kind.

One finding of record, S6-F1: `df -g /System/Volumes/Data` reads 28 GiB
free, which is under the 29 GiB floor of blocker S0-B6.  It is reported
with its printed line above and it is not repaired here.
