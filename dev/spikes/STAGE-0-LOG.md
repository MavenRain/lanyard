# Stage 0 log

Date: 2026-09-09.  Nine spikes, one row each, in the shape of the Stage
0 brief section 7.  Every file named below is under
/Users/oobi/Documents/lanyard-m0/spikes/dev/.  The load figures are the
one minute load average from `uptime` before and after the measured leg
of that spike.  The bytes left column is the closer's own `du -sk` over
that spike's scratch directory at 08:02 on 2026-09-09, in KiB.

| spike | file | pass line | result | NOISY | load before | load after | bytes left |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | SPIKE-TRUSTED.md | `TRUSTED-LINES kernel=3997/4000 encoder=246/600 OK` | PASS | no | 16.90 | 16.90 | 24 |
| S2 | SPIKE-BENCH.md | `BENCH kanon-check-m1-corpus median_ms=16.249 min_ms=15.603 max_ms=17.209 runs=5` | PASS by shape | YES | 14.90 | 14.90 | 8 |
| S3 | SPIKE-ANCHOR.md | anchor path topcoat-router/src/href.rs printed, four sha256 values, one per site | PASS | no | 15.64 | 15.86 | 52 |
| S4 | SPIKE-DENOM.md | thirteen measured points with the 8 and 16 kloc anchors, R squared 0.291, sha ba1293a3, "40.7 retired" beside 45.0 and 18.11 | PASS by shape | YES | 23.89 | 24.10 | 76 |
| S5 | SPIKE-COVER.md | `PARITY-EXPECT m2=570 of 570`, computed from the rule | PASS | no | 14.08 | 16.15 | 1364 |
| S6 | SPIKE-BASE.md | wasm/emit.ml 1123, wasm/link.ml 1162, wasm/gc_encode.ml 246, lib/erase.ml 1484, honest base 5481 | PASS | no | 17.82 | 17.82 | 32 |
| S7 | SPIKE-ARC.md | `ARC median_ns_per_clone=22.4209 runs=5` against `RC median_ns_per_clone=4.1950 runs=5` | PASS by shape | YES | 14.84 | 16.85 | 20 |
| S8 | SPIKE-ORDER.md | 510 line copy, twelve arms, `Total line delta: 45`, headroom sentence answered | PASS | no | 13.49 | 22.49 | 32 |
| S9 | SPIKE-SEND.md | Arc form exits 0 with no diagnostic, Rc form exits 1 with the Send diagnostic | PASS | no | 28.47 | 29.87 | 16 |

S2, S4 and S7 are the timing spikes and all three are NOISY, because the
load average was above 4 for the whole stage.  NOISY is recorded and no
number was dropped.  No timing spike ran beside another timing spike.
S1, S3, S5, S6, S8 and S9 count lines, hash bytes, label rows or read an
exit code, so the load average does not mark them NOISY.

## The dev directory, by `wc -c`

```
    9015 SPIKE-TRUSTED.md
    9089 SPIKE-BENCH.md
   10348 SPIKE-ANCHOR.md
   13024 SPIKE-DENOM.md
    5147 denominators.json
   24428 SPIKE-COVER.md
   10546 SPIKE-BASE.md
   11002 SPIKE-ARC.md
   10010 SPIKE-ORDER.md
    6641 SPIKE-SEND.md
  109250 total
```

M0-BUILD-LOG.md and MUTATION-LOG.md sit beside them and their byte
counts are in the final gate transcript,
/Users/oobi/Documents/lanyard-m0/spikes/mutants/gates-run2.log.  Every
file in the directory ends with a newline, proved by `tail -c 1 FILE |
xxd -p` printing `0a` for each.

## Mutations

Three checks ran and three mutants were KILLED: S0-M1 the anchor byte
flip, S0-M2 the ten line rise from 3997 to 4007, and S0-M3 the Rc Send
failure at exit 1 against the Arc form at exit 0.  MUTATION-LOG.md holds
the commands and the printed evidence.  No mutant survived.

## Closing checks

```
ls -d /Users/oobi/Documents/lanyard
ls: /Users/oobi/Documents/lanyard: No such file or directory

git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin status --porcelain | wc -l
       0

git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin rev-parse HEAD
046689a78ef6708404bd190dc86845cbee0bb36f

git -C /Users/oobi/Documents/toasty rev-parse HEAD
7bd502cbf44cc47f70db9f2b27ab35d77a096364

git -C /Users/oobi/Documents/topcoat rev-parse HEAD
51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a

du -sk /Users/oobi/Documents/lanyard-m0/spikes
2068

df -g /System/Volumes/Data
49 GiB free, above the 29 GiB floor of S0-B6
```

No path outside /Users/oobi/Documents/lanyard-m0 was written.  Every
spike wrote in its own scratch directory and in dev/, the judge wrote
only under mutants/, and the closer wrote this file.  The pin worktree,
toasty, topcoat, kanon, kanon-m2-corpus, brisk and lean4export were read
only for the whole stage.  The pin binary was run read only and it was
never rebuilt.  /Users/oobi/Documents/lanyard was never created.

Stage 0 has no commit.  It creates no repository, so there is nothing to
stage and nothing to commit.  `git add` and `git commit` were never run.
Stage A creates /Users/oobi/Documents/lanyard on its own opt-in, carries
dev/ into it as dev/spikes/, and prints the first commit command for the
user to run.
