# M0 build log

## Stage 0 (2026-09-09)

Stage 0 ran the nine spikes S1 to S9 of M0-PLAN.md section 2 under
/Users/oobi/Documents/lanyard-m0/spikes/.  Stage 0 measures and rules
nothing.  No repository was created, /Users/oobi/Documents/lanyard does
not exist, nothing was built with cargo or dune, no file outside
/Users/oobi/Documents/lanyard-m0 was written, and nothing was staged and
nothing was committed.

### 1 Deliverables

All under /Users/oobi/Documents/lanyard-m0/spikes/dev/, with `wc -c`
taken at 08:02 on 2026-09-09:

| file | bytes | spike |
| --- | --- | --- |
| SPIKE-TRUSTED.md | 9015 | S1 |
| SPIKE-BENCH.md | 9089 | S2 |
| SPIKE-ANCHOR.md | 10348 | S3 |
| SPIKE-DENOM.md | 13024 | S4 |
| denominators.json | 5147 | S4 |
| SPIKE-COVER.md | 24428 | S5 |
| SPIKE-BASE.md | 10546 | S6 |
| SPIKE-ARC.md | 11002 | S7 |
| SPIKE-ORDER.md | 10010 | S8 |
| SPIKE-SEND.md | 6641 | S9 |
| M0-BUILD-LOG.md | this file | closer |
| MUTATION-LOG.md | 8087 | judge |

The stage log is /Users/oobi/Documents/lanyard-m0/spikes/STAGE-0-LOG.md,
which the brief section 10 puts one level above dev/.

### 2 Gates

The battery is /Users/oobi/Documents/lanyard-m0/spikes/mutants/gates-section-4.sh
and the transcripts are gates-run1.log and gates-run2.log beside it.

| gate | result | evidence |
| --- | --- | --- |
| S0-G1 NO-REPO | PASS | `ls: /Users/oobi/Documents/lanyard: No such file or directory` at the start of the window and again at the end |
| S0-G2 PIN-CLEAN | PASS | porcelain `0` and HEAD `046689a78ef6708404bd190dc86845cbee0bb36f`, both read at the start of the window and again at the end |
| S0-G3 LIB-PINS | PASS | toasty `7bd502cbf44cc47f70db9f2b27ab35d77a096364`, topcoat `51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a` |
| S0-G4 TRUSTED | PASS | `TRUSTED-LINES kernel=3997/4000 encoder=246/600 OK` verbatim, `Headroom against 4000: 3`, `Status: PROPOSED`, nine named members plus the four the script adds |
| S0-G5 BENCH | PASS by shape | one line `BENCH kanon-check-m1-corpus median_ms=16.249 min_ms=15.603 max_ms=17.209 runs=5`, second median 15.861 ms at runs 5, `2.45 percent`, NOISY at load average 14.90 |
| S0-G6 ANCHOR | PASS | `topcoat-router/src/href.rs` printed by fd, four distinct sha256 values, four `awk 'NR>=` extraction commands |
| S0-G7 DENOM | PASS by shape | `PARSE rows=13 ok=13 F=96.74 m=7.24 r2=0.291 noisy=true runs=5`, host block of four keys, `40.7 retired` three times, sha ba1293a3f8970531ab32490fc20d55fd8a04cb16ca7f45d2ca0956075f4bf03d |
| S0-G8 COVER | PASS | rule paragraph "The rule is this", `PARITY-EXPECT m2=570 of 570` computed by awk, `MILESTONE M0 roots=89`, `M1 roots=8`, `M2 roots=473`, eleven worked rows |
| S0-G9 BASE | PASS | 1123, 1162, 246 and 1484 printed by `wc -l`, twelve gate-list members with a count each, honest base 5481 |
| S0-G10 ARC | PASS by shape | two `rustup run 1.98 rustc --edition 2024 -O` lines, `median_ns_per_clone=22.4209` and `median_ns_per_clone=4.1950`, difference 18.2259 ns |
| S0-G11 ORDER | PASS | 510 line count of the copy, twelve arms, `Total line delta: 45`, S1 headroom of 3 quoted, the "three lines of headroom" sentence answered |
| S0-G12 SEND | PASS | two `rustup run 1.98 rustc --edition 2024 --emit=metadata` lines, `exit=0` for Arc with no diagnostic, `exit=1` for Rc with `future cannot be sent between threads safely` |
| S0-G13 PROSE | PASS | `rg -l` with a pattern built by `printf '[\u2014\u2013]'` over the whole spikes tree prints no file |
| S0-G14 SPIKE-FILES | PASS | ten `wc -c` rows, 109250 bytes total, and every file ends `0a` by `tail -c 1 FILE | xxd -p` |
| S0-G15 SCRATCH-CLEAN | PASS | `du -sk /Users/oobi/Documents/lanyard-m0/spikes` prints 2044 in the first run and 2068 in the final run, the rise is the three log files, `fd -t f -S +50m` finds no file, and `df -g /System/Volumes/Data` prints 48 GiB free in the first run and 49 GiB in the final run |

Mutations: three ran and three were KILLED.  MUTATION-LOG.md holds the
commands and the printed evidence.  No mutant survived, so no blocker
fired from the brief section 5.

Blockers: none fired inside this window.  S0-B6 fired once earlier in
the stage and is recorded as finding S6-F1 below.

### 3 Frozen numbers

- Kernel bucket 3997 of 4000, encoder 246 of 600, headroom 3.
- Honest M0 base 5481 lines, which is 3997 plus lib/erase.ml at 1484.
- Emitter inputs wasm/emit.ml 1123, wasm/link.ml 1162, wasm/gc_encode.ml
  246 and lib/erase.ml 1484.
- Bench 16.249 ms by the pin tool against 15.861 ms by python3
  perf_counter, both medians of five, agreement 2.45 percent.
- Anchor digests: site 1
  314e1e3d815d7b03a30f06e0c882797f42a73f25318dd945287e9da5e8150465,
  site 2
  8153ebe800d72c3d3cbd9990417bf8136e20055d71c1d42d593707ef9a7f9e4d,
  site 3
  160a7d3ae57ce2a0fbd79ce2d3d8782245ae54ecf7be42503fb3eeacbf070337,
  site 4
  bf2347febd67b875c0fff040221ee2ef51af41a35d852a3c60f709cb0ed3527b.
- Denominator fit F 96.74 ms, m 7.24 ms per kloc, R squared 0.291 over
  13 rows, five runs per row, sha256 of denominators.json
  ba1293a3f8970531ab32490fc20d55fd8a04cb16ca7f45d2ca0956075f4bf03d.
  40.7 is retired against the live tightest total 45.0 and slope 18.11.
- Cover counts 570 roots, 89 at M0, 8 at M1 and 473 at M2, so the M2
  expectation is 570 of 570, computed.
- Arc 22.4209 ns per clone against Rc 4.1950 ns per clone, both medians
  of five, difference 18.2259 ns, REPORTED and bound at no milestone.
- Order.translate extension: twelve arms and about 45 lines.
- Send probe: Arc exits 0, Rc exits 1 on the Send bound.

### 4 Findings and how each was resolved

| id | severity | resolution |
| --- | --- | --- |
| S1-F1 | high | RECORDED, no repair.  The script's `kernel_files` array holds twelve paths, not the eight that M0-PLAN.md section 4 and the brief section 2 name.  The eight sum to 3188 and the four later members, lib/positivity.ml 118, lib/global.ml 130, lib/order.ml 510 and lib/bignum.ml 51, sum to 809.  3188 plus 809 is 3997, so the printed number is right for the bucket the script defines and the eight-file description is short.  The pin is read only, so nothing was corrected inside it.  SPIKE-TRUSTED.md section 3 and SPIKE-BASE.md section 2 both carry the twelve-file list.  S0-M2 copied all twelve, which is why the copy reproduced 3997. |
| S1-F2 | medium | RECORDED, no repair.  lib/order.ml at 510 lines is inside the counted 3997, so an Order.translate extension spends the headroom of 3 directly against the 4000 bound.  S8 prices that extension at twelve arms and about 45 lines, and R-Q3 keeps lib/order.ml byte for byte at M0, so the headroom stays unspent today.  SPIKE-TRUSTED.md sections 3 and 6 and SPIKE-ORDER.md section 9 hold the sentence. |
| S6-F1 | high | CLEARED by remeasurement, not by a delete.  At 06:51 `df -g /System/Volumes/Data` read 28 GiB free, which fired S0-B6, and SPIKE-BASE.md section 8 records that reading.  At 07:57 the same command read 49 GiB free and at 08:02 it read 48 GiB free, both above the 29 GiB floor.  Another session freed the space.  Nothing was deleted outside this stage's own scratch to recover it, per the brief section 8.  Both readings are kept. |
| S7-F1 | medium | RECORDED, no rerun.  The Arc median is dominated by scheduler noise: the five Arc runs read 30.6752, 6.2412, 69.7733, 22.4209 and 9.8305 ns per clone, a max over min ratio of 11.2, against five Rc runs of ratio 1.21.  SPIKE-ARC.md keeps every raw value, reports the median 22.4209 ns, gives the quiet view 2.1672 ns beside it, and marks the spike NOISY at load average 16.85.  No run was repeated, because NOISY never orders a rerun.  The gate S0-G10 passes by shape, and decision S0-D3 states the number is REPORTED at M0 and bound at no milestone. |
| V-F1 | blocker | FIXED.  The three log deliverables and the mutants directory did not exist.  The judge ran S0-M1, S0-M2 and S0-M3 from /Users/oobi/Documents/lanyard-m0/spikes/mutants/run-mutants.sh, all three KILLED, and wrote dev/MUTATION-LOG.md.  The closer wrote this file and /Users/oobi/Documents/lanyard-m0/spikes/STAGE-0-LOG.md with the nine rows. |
| V-F2 | medium | FIXED.  Two scratch scripts held a typed em-dash and en-dash: /Users/oobi/Documents/lanyard-m0/spikes/s4/gate-g7.sh line 11 and /Users/oobi/Documents/lanyard-m0/spikes/s6/run3.sh line 7.  Both now build the pattern with `pat=$(printf '[\u2014\u2013]')` and match through `"$pat"`, which is what S0-G13 asks for, so neither character is typed in any stage file.  The behaviour of both scripts is unchanged.  S0-G13 now runs over the whole spikes tree and prints no file. |

### 5 Decisions recorded

An agent RECORDS a decision and the user RULES it.  No ruled item of
RATIFICATIONS.md was reopened.

- S0-D1 the M0 TRUSTED-LINES ceiling, owned by S1, PROPOSED in
  SPIKE-TRUSTED.md section 6.  The rule is M0-PLAN.md section 4 with no
  separate margin: 3997 plus lib/erase.ml 1484 is 5481, plus the three
  named allowances A_rir, A_emit and A_sig for lib/rir.ml, rust/emit.ml
  and the generated signature module, which are NOT YET WRITTEN.  D-M0-3
  gives the ruling to the user.
- S0-D2 the denominator set, owned by S4, in SPIKE-DENOM.md section 7.
  Thirteen Go packages carry a row, with the 8 and 16 kloc points
  covered.  M1-RATIO reads the frozen denominators.json.
- S0-D3 the Arc price wording, owned by S7, in SPIKE-ARC.md section 9.
  M0-TIME prints the medians and states that the number is reported at
  M0 and bound at no milestone.
- S0-D4 the S5 covering rule, owned by S5, in SPIKE-COVER.md sections 1
  and 11.  Sixteen ledger rows, the closure rule and the computed M2
  expectation of 570 of 570.  M2-PARITY reads it.
- S0-D5 the S2 timing tool, owned by S2, in SPIKE-BENCH.md section 8.
  The two instruments agree to 2.45 percent, which is inside 5 percent,
  so the pin's dev/bench.sh stands and dev/bench.py is not forced.
- S0-D6 the S8 line delta, owned by S8, in SPIKE-ORDER.md section 9.
  Twelve arms and about 45 lines.  The record stays informational,
  because fact 8 closes only if the user reopens R-Q3.

### 6 What did not happen

No repository was created and /Users/oobi/Documents/lanyard is still
absent.  The pin worktree was not written, its binary was not rebuilt
and its porcelain still prints 0.  toasty, topcoat, kanon,
kanon-m2-corpus, brisk and lean4export were not written.  No cargo
command and no dune command ran.  Every rustc leg was a single-file
compile and every output it made was deleted.  Nothing was installed.
`git add` and `git commit` were never run.

## Stage A (2026-09-09)

Stage A forked /Users/oobi/Documents/lanyard from /Users/oobi/Documents/kanon
at 046689a78ef6708404bd190dc86845cbee0bb36f (short 046689a) with its 27
commits of history, deleted wasm/ and runtime/ and the seven wasm legs of
dev/gates.sh, kept the twelve kernel files and lib/erase.ml byte for byte,
carried the thirteen Stage 0 records into dev/spikes/, renamed the project,
the driver binary and the source extension, and left the dune build green.
One workflow ran, wf_ce4a6459-f61, with one review round and one fix round.
Nothing was committed.  No cargo command ran.  No language code was written.

### Deliverables

- The fork on branch main at the pin sha, remote removed, 27 commits.
- Deletions: wasm/dune, wasm/emit.ml (1123 lines), wasm/link.ml (1162),
  wasm/gc_encode.ml (246), runtime/reactor.kan, runtime/reactor.mjs,
  runtime/run.mjs, test/wasm.ml and, in the fix round, bin/host.ml (137).
- dev/gates.sh legs deleted: SUITE-WASM, ENCODER-SUBSET, M0-E2E, M0-TIME,
  M0-RATIO, REACTOR, RUNTIME.  Legs kept: CARRY, R0-COUNT, R0-AUDIT,
  SUITE-KERNEL, AXIOMS, TRUSTED-LINES, DENOMINATORS, HOUSE, PIN, POSITIVITY,
  M1-CORPUS, M1-SUITE, AGREEMENT.
- dev/KERNEL-CARRIED.md (thirteen rows, all VERBATIM) and dev/kernel-carry.sh.
- dev/spikes/ with the twelve Stage 0 files and STAGE-0-LOG.md.
- dev/dunecho.sh with the switch delta, dev/trusted-lines.sh in its Stage A
  form, dev/r0-count.sh and every dev script repointed to bin/lanyard.exe.

### Frozen numbers

- Kernel bucket 3997 of 4000: shape 60, term 133, rules 1481, check 538,
  value 137, eval 297, conv 396, totality 146, positivity 118, global 130,
  order 510, bignum 51.  lib/erase.ml 1484.  lib/shape.ml stays at 60 and
  lib/rules.ml keeps spar_word at rules.ml:20.
- M0 TRUSTED-LINES ceiling: 5481 + A_rir + A_emit + A_sig, no total.  The
  three allowances are OPEN user rulings (S0-D1, D-M0-3) and no number is
  guessed here.
- Deleted wasm source: 2531 lines in three .ml files plus wasm/dune.
- Carried Stage 0 records: twelve files, 127830 bytes, plus STAGE-0-LOG.md,
  thirteen EQUAL sha256 pairs.
- History: 27 commits, HEAD 046689a78ef6708404bd190dc86845cbee0bb36f.

### Gates

| Gate | Result | Evidence |
|---|---|---|
| SA-G1 NO-TREE | PASS | The builder read ls -d /Users/oobi/Documents/lanyard before the clone and it printed the No such file or directory error;  the tree now holds only the work of this stage, HEAD 046689a78ef6708404bd190dc86845cbee0bb36f. |
| SA-G2 FORK | PASS | is-inside-work-tree true, HEAD 046689a78ef6708404bd190dc86845cbee0bb36f, count 27. |
| SA-G3 NO-REMOTE | PASS | git remote -v printed [], exit 0. |
| SA-G4 SOURCES-READONLY | PASS | START: kanon HEAD 45f74406c4574d7cb00d8944cebf79193cd01f9b porcelain 46, pin HEAD 046689a78ef6708404bd190dc86845cbee0bb36f porcelain 0.  END: kanon HEAD 45f74406c4574d7cb00d8944cebf79193cd01f9b porcelain 46, pin HEAD 046689a78ef6708404bd190dc86845cbee0bb36f porcelain 0. |
| SA-G5 DELETIONS | PASS | ls: /Users/oobi/Documents/lanyard/runtime: No such file or directory ls: /Users/oobi/Documents/lanyard/wasm: No such file or directory;  D rows 10;  deleted legs in dev/gates.sh: 0;  legs kept: CARRY R0-COUNT R0-AUDIT SUITE-KERNEL AXIOMS TRUSTED-LINES DENOMINATORS HOUSE PIN POSITIVITY M1-CORPUS M1-SUITE AGREEMENT. |
| SA-G6 KERNEL-CARRY | PASS | exit 0, KERNEL-CARRY rows=13 KERNEL-CARRY OK, row lines 13, rerun after the dev/trusted-lines.sh edit landed. |
| SA-G7 SPIKES-CARRY | PASS | rows 13 equal 13 (the twelve dev/spikes files hold their SOURCE digests here because this stage appends to two of them below;  the pre-append digests are the proof of carry);  rows in the mutation log and in /Users/oobi/Documents/lanyard-m0/fix2/g7-rows.txt. |
| SA-G8 BUILD | PASS | build exit 0, last line: OK build: 0 errors, 0 warnings, switch delta rows: 1. |
| SA-G9 R0-COUNT | PASS | R0-COUNT OK exit 0;  git diff --stat 046689a78ef6708404bd190dc86845cbee0bb36f -- SPEC.md printed []. |
| SA-G10 TRUSTED-LINES | PASS | TRUSTED-LINES kernel=3997/4000 M0 ceiling: 5481 + A_rir + A_emit + A_sig TRUSTED-LINES OK exit 0. |
| SA-G11 NAMES | PASS | dune-project 3:(name lanyard) 6: (name lanyard);  /Users/oobi/Documents/lanyard/bin/lanyard.ml;  /Users/oobi/Documents/lanyard/_build/default/bin/lanyard.exe;  fd kanon.ml under bin: []. |
| SA-G12 HOUSE | PASS | zsh dev/house.sh /Users/oobi/Documents/lanyard printed HOUSE OK, exit 0. |
| SA-G13 PROSE | PASS | rg with the pattern built from U+2014 and U+2013 over every staged path and every file of this stage under lanyard-m0 printed nothing (rerun in the close). |
| SA-G14 NO-COMMIT | PASS | rev-list count 27, HEAD 046689a78ef6708404bd190dc86845cbee0bb36f, at the END of the stage (reprinted in the close). |
| SA-G15 LOGS | PASS | diff of head -n 138 of this file against the Stage 0 source and head -n 169 of MUTATION-LOG.md against its source print nothing;  each file has one Stage A heading (reprinted in the close). |

### Findings and their resolution

Review round, seven findings, all resolved in the fix round of 2026-09-09.

- SA-G15 LOGS (high).  The carried logs had no Stage A section.  FIXED: this
  section and the Stage A section of MUTATION-LOG.md;  the Stage 0 spans
  stay byte for byte.
- closer-incomplete (high).  No path was staged and no commit message
  existed.  FIXED: every row of git status --short -uall is staged, the
  message is at /Users/oobi/Documents/lanyard-m0/stage-a-commit-message.txt
  and the commit command is printed, never run.
- gate-report-gap (medium).  The builder reported thirteen gates.  FIXED:
  all fifteen gates rerun after the fixes, table above.
- SA-F1 vendor/tot (medium).  The plain clone left the submodule empty, so
  dev/carry-check.sh had nothing to read.  FIXED: one command,
  git -c protocol.file.allow=always submodule update --init -- vendor/tot,
  cloned the pin 8cf0b8bf from the local url /Users/oobi/Documents/tot, no
  network;  evidence line below.
- SA-F1 m1-gates.py (high).  The kept legs AGREEMENT, M1-CORPUS and
  M1-SUITE call the run and emit commands the driver no longer has, so they
  are red until the Rust back end lands.  RECORDED, not edited: the brief
  names exactly seven legs to delete and zsh dev/gates.sh M0 is a Stage F
  gate.  The stage that lands the back end owns these legs.
- SA-F2 house scripts (medium).  dev/house.sh, dev/house-catchalls.py and
  dev/house-allow.txt named wasm/ and bin/kanon.ml.  FIXED in the build
  round;  the fix round dropped the bin/host.ml allow row and the
  catchalls assertion now names one D-M1-10 site.
- SA-F3 bin/host.ml (medium).  Dead module after the run dispatch left.
  FIXED: git rm bin/host.ml, 137 lines, no Host reference remained in bin,
  test, surface or lib;  build green after the removal.
- SA-F1 kernel-carry bucket (medium).  SA-G6 rerun after the
  dev/trusted-lines.sh rewrite landed:  bucket files=12 expected=12 OK.
- SA-F1 dev/DENOMINATORS.sha256 (medium).  The fork carries a third
  colliding basename, dev/DENOMINATORS.sha256 (84 bytes, the kanon vendored
  pin ledger).  Stage A writes no dev/spikes/DENOMINATORS.sha256 (R-Q4,
  S0-D2).  The lanyard frozen denominator artifact is
  dev/spikes/denominators.json, sha256
  ba1293a3f8970531ab32490fc20d55fd8a04cb16ca7f45d2ca0956075f4bf03d.
  RECORDED beside SA-D6 and put to the user.

vendor/tot after the fix: submodule status  8cf0b8bfbb574e344d8d489ba6fd6b81de4cf562 vendor/tot (8cf0b8b);  dev/carry-check.sh last line CARRY-OK

### Decisions SA-D1 to SA-D7

- SA-D1 branch: main.  git branch --show-current printed main.
- SA-D2 remote: origin removed after the clone;  git remote -v prints
  nothing.
- SA-D3 the smallest edits that restore green, as the staged diffstat
  against the fork point (bin/lanyard.ml is the renamed bin/kanon.ml with
  the run, emit and host dispatch cut, 345 to 122 lines;  dev/gates.sh 356
  to 279 lines):

```
 bin/dune |    4 +-
 bin/host.ml |  137 -----
 bin/kanon.ml |  345 ------------
 bin/lanyard.ml |  122 ++++
 dev/KERNEL-CARRIED.md |  105 ++++
 dev/agreement.py |    2 +-
 dev/dunecho.sh |    8 +-
 dev/gates.sh |   87 +--
 dev/house-allow.txt |    2 +-
 dev/house-catchalls.py |    4 +-
 dev/house.sh |   24 +-
 dev/kernel-carry.sh |  172 ++++++
 dev/m1-gates.py |    2 +-
 dev/mu-bridge/check.py |    2 +-
 dev/mu-bridge/check_finitary.py |    2 +-
 dev/mu-bridge/check_tree.py |    2 +-
 dev/mu-bridge/check_vector.py |    2 +-
 dev/nat-runtime.sh |    2 +-
 dev/one-paths.sh |    2 +-
 dev/r0-count.sh |    4 +-
 dev/reactor-test.mjs |    2 +-
 dev/spikes/M0-BUILD-LOG.md |  138 +++++
 dev/spikes/MUTATION-LOG.md |  169 ++++++
 dev/spikes/SPIKE-ANCHOR.md |  317 +++++++++++
 dev/spikes/SPIKE-ARC.md |  255 +++++++++
 dev/spikes/SPIKE-BASE.md |  252 +++++++++
 dev/spikes/SPIKE-BENCH.md |  235 ++++++++
 dev/spikes/SPIKE-COVER.md |  529 ++++++++++++++++++
 dev/spikes/SPIKE-DENOM.md |  221 ++++++++
 dev/spikes/SPIKE-ORDER.md |  227 ++++++++
 dev/spikes/SPIKE-SEND.md |  196 +++++++
 dev/spikes/SPIKE-TRUSTED.md |  223 ++++++++
 dev/spikes/STAGE-0-LOG.md |   93 ++++
 dev/spikes/denominators.json |  194 +++++++
 dev/trusted-lines.sh |   60 +-
 dune-project |    4 +-
 runtime/reactor.kan |   53 --
 runtime/reactor.mjs |  275 ---------
 runtime/run.mjs |   28 -
 test/dune |    4 +-
 test/wasm.ml |  280 ----------
 wasm/dune |    3 -
 wasm/emit.ml | 1123 -------------------------------------
 wasm/gc_encode.ml |  246 ---------
 wasm/link.ml | 1162 ---------------------------------------
 45 files changed, 3525 insertions(+), 3794 deletions(-)
```

- SA-D4 TRUSTED-LINES Stage A form: the encoder half that read
  wasm/gc_encode.ml is dropped;  the leg prints TRUSTED-LINES
  kernel=3997/4000, then M0 ceiling: 5481 + A_rir + A_emit + A_sig, then
  TRUSTED-LINES OK.  No total is printed.  A_rir, A_emit and A_sig are open
  user rulings and no agent guesses a number.
- SA-D5 R0-COUNT Stage A form: dev/r0-count.sh runs
  _build/default/bin/lanyard.exe spec-count and diffs the eight lines
  against the fenced block under the R0 counts heading of SPEC.md, whose
  bytes did not move;  it printed R0-COUNT OK.  The ninth census line is
  Stage C.
- SA-D6 the lanyard Stage 0 logs live at dev/spikes/M0-BUILD-LOG.md and
  dev/spikes/MUTATION-LOG.md, because dev/M0-BUILD-LOG.md and
  dev/MUTATION-LOG.md are carried kanon bytes of another project and this
  stage does not touch them.  The basename collision, and the third one at
  dev/DENOMINATORS.sha256, are put to the user.
- SA-D7 renamed now: the project name (dune-project name and package
  lanyard), the driver binary (bin/lanyard.ml, _build/default/bin/lanyard.exe)
  and the source extension .lan as a written rule with no file.  Not renamed:
  the OCaml library names kanon_kernel and kanon_surface and the module
  names (the stage that first edits a library dune file owns it, Stage D at
  the earliest), SPEC.md and README.md prose (Stage C with the census line),
  examples/, test/ and meta/ (Stage F with the M0 close).  The carried
  corpus keeps .kan.

### Blockers

None fired and none waived.

### Judge rerun (2026-09-09)

The Stage A judge reran the fifteen gates and the three mutants after the
fix round, from /Users/oobi/Documents/lanyard-m0/judge/sa-judge-run.sh and
/Users/oobi/Documents/lanyard-m0/judge/sa-judge-close.sh.  Transcripts:
/Users/oobi/Documents/lanyard-m0/judge/gates.log and close.log.  The judge
also set two spaces after every semicolon in the Stage A section of this
file and of MUTATION-LOG.md and touched no Stage 0 byte.

| Gate | Judge | Evidence |
|---|---|---|
| SA-G1 NO-TREE | PASS | The judge runs after the clone, so the START reading is the builder's printed line `ls: /Users/oobi/Documents/lanyard: No such file or directory` with ls rc 1;  now HEAD 046689a78ef6708404bd190dc86845cbee0bb36f, 45 status rows, 0 unstaged rows. |
| SA-G2 FORK | PASS | is-inside-work-tree true, HEAD 046689a78ef6708404bd190dc86845cbee0bb36f, rev-list count 27, branch main. |
| SA-G3 NO-REMOTE | PASS | `git remote -v` printed [] with rc 0 and 0 bytes;  remote config rows 0;  refs/remotes rows 0. |
| SA-G4 SOURCES-READONLY | PASS | START kanon HEAD 45f74406c4574d7cb00d8944cebf79193cd01f9b porcelain 46, pin HEAD 046689a78ef6708404bd190dc86845cbee0bb36f porcelain 0;  END identical, both readings in the judge window (gates.log, close.log). |
| SA-G5 DELETIONS | PASS | `ls: /Users/oobi/Documents/lanyard/runtime: No such file or directory` and `ls: /Users/oobi/Documents/lanyard/wasm: No such file or directory`;  D rows 10;  rg for the seven deleted leg names over dev/gates.sh printed nothing;  kept legs CARRY, R0-COUNT, R0-AUDIT, SUITE-KERNEL, AXIOMS, TRUSTED-LINES, DENOMINATORS, HOUSE, PIN, POSITIVITY, M1-CORPUS, M1-SUITE, AGREEMENT. |
| SA-G6 KERNEL-CARRY | PASS | rc 0, 13 file rows, `KERNEL-CARRY bucket files=12 expected=12 OK`, `KERNEL-CARRY rows=13`, `KERNEL-CARRY OK`. |
| SA-G7 SPIKES-CARRY | PASS | rows 13 equal 13:  eleven whole files and the two Stage 0 spans (head -n 138 of this file, head -n 169 of MUTATION-LOG.md) against the sources;  SPIKE-TRUSTED.md bebfabdfe63325da3e8458e41f1eb8c8e4acf95867ff43726a312bd9b33dc86c on both sides;  STAGE-0-LOG.md b28f4f2d62da4a14dbfa3c702e34a572d58398f4ea914c14a200aab9898e2ba6 on both sides. |
| SA-G8 BUILD | PASS | `zsh dev/dunecho.sh build` rc 0, last line `OK build: 0 errors, 0 warnings`, switch line count 1. |
| SA-G9 R0-COUNT | PASS | `R0-COUNT OK` rc 0;  `git diff --stat 046689a78ef6708404bd190dc86845cbee0bb36f -- SPEC.md` printed 0 bytes. |
| SA-G10 TRUSTED-LINES | PASS | `TRUSTED-LINES kernel=3997/4000`, `M0 ceiling: 5481 + A_rir + A_emit + A_sig`, `TRUSTED-LINES OK`, rc 0, no total printed. |
| SA-G11 NAMES | PASS | dune-project lines 3 and 6 read (name lanyard);  bin/lanyard.ml present;  _build/default/bin/lanyard.exe at 2515320 bytes;  fd kanon.ml under bin printed nothing. |
| SA-G12 HOUSE | PASS | `zsh dev/house.sh /Users/oobi/Documents/lanyard` printed HOUSE OK, rc 0, the one catch site test/sys_io.ml:19. |
| SA-G13 PROSE | PASS | rg with pat=$(printf '[\u2014\u2013]') over the 35 staged AMR paths, the commit message, the two judge scripts and gates.log printed no file, rc 1. |
| SA-G14 NO-COMMIT | PASS | rev-list --count HEAD 27 and HEAD 046689a78ef6708404bd190dc86845cbee0bb36f at the END of the judge window (close.log);  no commit, push or tag ran. |
| SA-G15 LOGS | PASS | diff of head -n 138 of this file and of head -n 169 of MUTATION-LOG.md against the sources printed nothing, rc 0 both;  one `## Stage A (2026-09-09)` heading in each file, at line 140 and at line 171. |

Mutants: SA-M1 KILLED, SA-M2 KILLED, SA-M3 KILLED (MUTATION-LOG.md, Stage A
judge rerun).  Verdict PASS.  Blockers fired: none.  Blockers waived: none.

Open for the user: A_rir, A_emit and A_sig stay names;  the basename
collisions of SA-D6 (dev/M0-BUILD-LOG.md, dev/MUTATION-LOG.md and
dev/DENOMINATORS.sha256);  the kept legs AGREEMENT, M1-CORPUS and M1-SUITE
stay red until the back end lands;  the library rename of SA-D7 is recorded
above as Stage D at the earliest and in the builder report as M1, so both
defer it past M0 and the stage that first edits a library dune file puts it
to the user.
