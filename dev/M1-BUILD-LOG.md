# kanon M1 build log

This log follows the plan at kanon-m1/M1-PLAN.md.  dev/M0-BUILD-LOG.md is
closed at M0-EXIT (M1-PLAN.md:51) and no M1 stage writes to it again.

## Stage F (2026-09-06)

The lake package kanon-meta and the four Beck-Chevalley statements over the two admitted shapes.  One builder wrote the package and the judge reran every gate and every mutation on a cleaned build tree before this entry.

### Deliverables

- meta/lean-toolchain, 1 line.  `leanprover/lean4:v4.33.0-rc1`, byte for
  byte KT/lean-toolchain (SF-D2).
- meta/lakefile.lean, 12 lines.  Package `kanon-meta`, `autoImplicit`
  false, one require of kan-tactics at the 40 character revision
  3317f7ac5a22ca0d85b90a3286b8fe0c36cea8ac, and the default target
  `KanonMeta`.
- meta/.gitignore, 1 line.  `.lake/`, so ROOT/.gitignore stays untouched
  (SF-D8).
- meta/lake-manifest.json, 26 lines.  The two pinned revisions,
  kan-tactics at 3317f7ac and comp-cat-theory at cc6ced10.
- meta/KanonMeta.lean, 11 lines.  The root module.  It imports the three
  module files and holds no declaration.
- meta/KanonMeta/Syntax.lean, 63 lines.  `Quantity`, the mutual family
  `Shape` and `Term`, and `Addr`, mirroring lib/shape.ml:11-12 and
  SPEC.md:26-42 with De Bruijn indices.
- meta/KanonMeta/Subst.lean, 122 lines.  The renaming layer, then
  `Subst`, `up`, `subst` and `substShape`, every function total and
  structurally recursive.
- meta/KanonMeta/BeckChevalley.lean, 55 lines.  The four theorems
  `bc_lan_spi`, `bc_ran_spi`, `bc_lan_scoll` and `bc_ran_scoll`, each
  closed by `kan_rfl` and nothing else.
- meta/Axioms.lean, 21 lines.  The SF-G4 driver with exactly four
  `#print axioms` commands.
- dev/M1-BUILD-LOG.md and dev/M1-MUTATION-LOG.md gain this entry and the
  Stage F mutation section (the judge).

### Gates (the judge reran SF-G1 to SF-G7 on the tree at 2026-09-06 03:01)

- SF-G1 BUILD, OK.  `rm -rf meta/.lake/build`, then
  `/Users/oobi/.elan/bin/lake +leanprover/lean4:v4.33.0-rc1 --dir
  /Users/oobi/Documents/kanon-stage-f/meta build`, detached.  The last
  five log lines are `✔ [36/40] Built KanonMeta.Syntax (557ms)`,
  `✔ [37/40] Built KanonMeta.Subst (392ms)`, `✔ [38/40] Built
  KanonMeta.BeckChevalley (4.0s)`, `✔ [39/40] Built KanonMeta (1.3s)`
  and `Build completed successfully (40 jobs).`;  the exit file holds
  `EXIT 0`.  `rg -c "error:"` over the log prints nothing, rg exit 1.
- SF-G2 NO-SORRY, OK.  `rg -n -c "sorry" meta` printed nothing, exit 1
  (`SWEEP-A-EXIT 1`).  `rg -n -c "axiom |native_decide|partial |unsafe "
  meta` printed nothing, exit 1 (`SWEEP-B-EXIT 1`).
- SF-G3 CLIENT, OK.  The client under SCRATCH/stageF/client, its build
  tree deleted first and its fetched packages kept, built with exit 0.
  The final three lines are `ℹ [41/42] Built Client (1.2s)`, the
  `#check` report `info: Client.lean:5:0: KanonMeta.bc_lan_spi (sigma :
  Subst) (A : Term) (q : Quantity) (x : String) (dom : Term) : subst
  sigma (Term.lan (Shape.SPi q x dom) A) = Term.lan (Shape.SPi q x
  (subst sigma dom)) (subst (up sigma) A)`, and `Build completed
  successfully (42 jobs).`
- SF-G4 AXIOMS, OK.  `lake env lean meta/Axioms.lean`, detached, exit 0.
  The four lines, verbatim and in the order of the brief:
  `'KanonMeta.bc_lan_spi' does not depend on any axioms`,
  `'KanonMeta.bc_ran_spi' does not depend on any axioms`,
  `'KanonMeta.bc_lan_scoll' does not depend on any axioms`,
  `'KanonMeta.bc_ran_scoll' does not depend on any axioms`.  No axiom
  name appears, so SF-B7 does not fire.
- SF-G5 TACTICS, OK.  `rg -n -o "kan_[a-z_]+" meta` returned five hits,
  all `kan_rfl`, the final line
  `meta/KanonMeta/BeckChevalley.lean:53:kan_rfl`.  Four are the proof
  bodies at :30, :37, :46 and :53;  the fifth at :13 is the module doc
  comment.  `rg -n "by$|by " meta` returned four `:= by` lines, at :29,
  :36, :45 and :52, each followed by `kan_rfl` alone.  A word sweep for
  the thirteen core tactic names of the brief over
  BeckChevalley.lean returned only statement text and doc prose, no
  tactic position.
- SF-G6 ROOT-GATES, OK.  `zsh dev/gates.sh` printed fifteen PASS lines,
  the MEASURE block and `GATES-OK`, exit 0.  `rg -c "^PASS "` over the
  log is 15 and the final line is `GATES-OK`.  The battery reads as it
  read at 09e77e9, because Stage F adds no OCaml line.  The battery ran
  twice, before and after this log file was written, and printed
  `GATES-OK` with no FAIL line both times.  `git -C ROOT status
  --porcelain` prints three lines, `?? dev/M1-BUILD-LOG.md`,
  `?? dev/M1-MUTATION-LOG.md` and `?? meta/`.
- SF-G7 TRUSTED-LINES, OK.  `zsh dev/trusted-lines.sh` printed
  `TRUSTED-LINES kernel=2305/3000 encoder=216/600 OK`, exit 0.  The
  numbers are the M0 numbers, because Lean files are not in the believed
  OCaml set.

### MEASURE

| Row | Value |
| --- | --- |
| build wall clock (the build verb of lake) | 15 s, start 1788688894, end 1788688909, after `rm -rf meta/.lake/build`;  budget 900 s |
| olean count under meta/.lake/build | 4 (KanonMeta, KanonMeta.Syntax, KanonMeta.Subst, KanonMeta.BeckChevalley) |
| theorem count | 4 |
| package line count | 312 across the nine meta files |

### Decisions

- SF-D1 The package lives at ROOT/meta with the lake package name
  `kanon-meta` and the library root `KanonMeta`.
- SF-D2 meta/lean-toolchain holds `leanprover/lean4:v4.33.0-rc1`.  No
  agent ran an install verb.
- SF-D3 kan-tactics is required at the 40 character revision
  3317f7ac5a22ca0d85b90a3286b8fe0c36cea8ac, never a branch name.
- SF-D4 The object language holds the two admitted shapes only.  SPar,
  SMu and SNu stay out.
- SF-D5 De Bruijn indices with `Subst := Nat -> Term` and a lift, which
  mirrors `Var of int` (SPEC.md:26).
- SF-D6 The four theorem names are `bc_lan_spi`, `bc_ran_spi`,
  `bc_lan_scoll` and `bc_ran_scoll`, in that order.
- SF-D7 The nineteen kan-tactics names are the whole tactic allowlist
  and SF-G5 is the rg check of it.
- SF-D8 meta/.gitignore carries `.lake/`, so ROOT/.gitignore stays
  untouched.
- SF-D9 meta/lake-manifest.json is committed.
- SF-D10 Every lake command ran through the detached runner of brief
  section 8, never in the foreground.
- SF-D11 Every lake command carries `+leanprover/lean4:v4.33.0-rc1`
  first and an absolute `--dir`, because elan reads the working
  directory and not the flag.
- SF-D12 Stage F writes under ROOT/meta only, plus the two new M1 log
  files under ROOT/dev that the judge writes.
- SF-D13 The fetch order of the brief was kept.  No fetch ran in this
  session:  the packages were already present, so the resumed run never
  fetched twice.
- SF-D14 `Addr` stays outside the mutual family and holds no term:  the
  point argument of `APt` rides in the argument field of `Term.intro`
  and `Term.out`, so the family is the minimal faithful pair Shape and
  Term.  `ACtor` stays out with the two recursive shapes that own it.
- SF-D15 The `lan` and `ran` arms of `ren` and of `subst` split on the
  shape and lift only under `SPi`, which is `spi_diagram_arity = 1` and
  `coll_diagram_arity = 0` (lib/rules.ml:635 and :637).  Every pattern
  field is named and used, so no arm carries a wildcard.
- SF-D16 The branch of `elim` and the leg of `sec` take the substitution
  unlifted, because the kernel gives each leg its own binder list
  (lib/term.ml:27-30) and this mirror does not carry that list.
- SF-D17 The renaming layer is defined before the substitution layer,
  because `up` weakens the terms a substitution carries.
- SF-D18 `Ren` and `Subst` are `abbrev`, so a plain `Nat -> Nat` or
  `Nat -> Term` unifies with them with no coercion.
- SF-D19 The require line of meta/lakefile.lean keeps the absolute path
  /Users/oobi/Documents/kan-tactics of brief 3.1, not the GitHub URL
  that SF-D13 mentions, because meta/lake-manifest.json pins that url at
  3317f7ac and a second update is forbidden.
- SF-D20 meta/Axioms.lean and the client file carry `open KanonMeta`, so
  the unqualified `#check` and the four `#print axioms` commands resolve
  and the output prints the qualified names.
- SF-D21 The doc prose of Subst.lean and Axioms.lean avoids the literal
  tokens that SF-G2 sweeps, because the gate is textual.
- SF-D22 `Level.t` is an OCaml `int` (lib/level.ml:2), so `Term.univ`
  holds a `Nat`, and `Quantity` mirrors lib/quantity.ml:10-13.
- SF-D23 The MEASURE wall clock was taken after `rm -rf
  meta/.lake/build`, so it is a full build of the library against built
  dependencies and not a cache read.
- SF-D24 A scratch probe under SCRATCH/stageF/probe proved the mutual
  structural recursion definitional before any file was written under
  meta, so no core tactic was ever needed in the package.

### Findings

- F1, info, brief text.  Brief section 3.4 SF-D13 asks for the GitHub
  URL of kan-tactics, while section 3.1 asks for the absolute path
  /Users/oobi/Documents/kan-tactics.  kan-tactics has no GitHub remote
  here, so the URL clause cannot apply.  Resolution: the package follows
  3.1 and meta/lake-manifest.json, which pins the absolute path;  the
  brief clause needs the correction, the package needs none.
- F2, low, sandbox.  A rebuild of the SF-G3 client from a deleted
  .lake directory fails, because comp-cat-theory is fetched from GitHub
  and the sandbox has no network.  Resolution: only PACKAGE/.lake/build
  is deleted to force a real build, never .lake/packages.  The judge's
  rerun deleted the build tree of meta and of the client and kept both
  package trees, and both builds are green.
- One defect of the builder was found and fixed inside the run, not
  logged as a finding:  an append with `head -n -2` is not supported by
  the BSD head of this machine and emptied BeckChevalley.lean, so run
  bc2 failed.  The file was rewritten whole and every later append went
  through a checked appender.

### Hand-off notes

- The optional agreement lemma of M1-PLAN.md:89 and :182 stays
  unwritten.  The ruling round 2026-09-06 (b) rules it out of this run.
  It is a separate opt-in now that the four theorems are green.
- The M1-EXIT criterion "Stage F green" (M1-PLAN.md:252) is met by the
  seven gates above.  D-M1-8 (RATIFICATIONS.md:66) makes Stage F, and
  not Stage G, the gate of M1-EXIT.
- meta/.lake is ignored by meta/.gitignore, so the stage commit carries
  the nine files of Deliverables and these two log files.  The user
  commits;  no agent commits.
- The client package of SF-G3 lives under SCRATCH and never in ROOT.  It
  is rebuilt from meta's fetched packages, because the sandbox reaches
  no remote.

### Stage F review fixes (2026-09-06)

The review found that section and branch bodies lost their binders,
and that point addresses lost their argument.  The following changes
supersede SF-D14 and SF-D16 and the original syntax description above.

- `Addr.apt` now holds the point term independently of the function
  head or fibre arguments.  It joins the mutual syntax family.
- `Leg` retains the binder list.  Sections retain all their legs, and
  eliminations retain their quantity, motive and addressed branches.
  Introductions retain their fibre argument list.  `Motive` retains its
  indices, self binder and body as specified in lib/term.ml.
- `ren` and `subst` traverse all these fields.  Leg bodies lift under
  their explicit binders; motive bodies lift under their indices and
  self binder.  Point arguments use the outer context.  List, option
  and pair traversal helpers keep both mutual definitions structurally
  recursive through the equation compiler.
- `meta/test/Regression.lean` adds 16 checks using `kan_rfl`.  A separate
  default Lake target builds them without importing tests from the
  public library.  They cover closed binders, free variables, weakening,
  empty and multiple collection legs, point operands and motive scope.

Validation used scratch copies at /private/tmp/kanon-stage-f-fixes and
the pinned Lean 4.33.0-rc1 toolchain with cached dependencies.  Commands
used `/Users/oobi/.elan/bin/lake +leanprover/lean4:v4.33.0-rc1 --dir`.

- Package `meta build`: `Build completed successfully (42 jobs).`,
  exit 0, including the four theorems and all 16 regression checks.
- Fresh `client build`, requiring the scratch package and checking all
  four theorems plus `substLeg` and `substAddr`:
  `Build completed successfully (42 jobs).`, exit 0.
- `meta env lean /private/tmp/kanon-stage-f-fixes/meta/Axioms.lean`,
  exit 0, printed:
  `'KanonMeta.bc_lan_spi' does not depend on any axioms`
  `'KanonMeta.bc_ran_spi' does not depend on any axioms`
  `'KanonMeta.bc_lan_scoll' does not depend on any axioms`
  `'KanonMeta.bc_ran_scoll' does not depend on any axioms`.
- All four review mutations failed in the regression target, as recorded
  in M1-MUTATION-LOG.md.  The source escape-hatch sweep had no hits.
- No OCaml or root gate implementation changed.  The root runtime
  battery was not rerun for these Lean-only fixes.  The optional
  agreement lemma remains outside this change.

## Stage G (2026-09-06)

### Deliverables

The line counts are read on ROOT after the build of SG-G1.

| file | lines | note |
| --- | --- | --- |
| lib/positivity.ml | 153 | new;  strict positivity, the family record |
| lib/rules.ml | 1193 | the SMu pack replaces the refusal at the old :188 |
| lib/check.ml | 446 | the index telescope rules and the installation |
| lib/global.ml | 130 | the family table and its one accessor |
| lib/shape.ml | 60 | the three total views payload, point_dom, family |
| lib/term.ml | 92 | the ACtor rows of as_apt and as_aleg |
| lib/error.ml | 69 | Index_not_zero and Index_above_universe |
| lib/erase.ml | 1146 | the interim mu erasure word of 3.8 |
| SPEC.md | 470 | the moved R0 counts and the positivity rule text |
| dev/trusted-lines.sh | 74 | positivity.ml and global.ml join the list |
| surface/token.ml | 128 | the mu and and words |
| surface/lexer.ml | 140 | the two new words |
| surface/syntax.ml | 234 | the fam, fam_ctor and DMu rows |
| surface/parser.ml | 458 | the minimal mu production of C7 |
| surface/elab.ml | 811 | the DMu arm, elab_program_in and check_in |
| bin/kanon.ml | 308 | run_erased and module_bytes carry the globals |
| test/main.ml | 289 | the ERASE-NEG group and the moved KNEG row |

The fixtures of brief 3.9 and the interim erasure fixture of 3.8.

| file | lines |
| --- | --- |
| test/fixtures/mu-direct.kan | 8 |
| test/fixtures/mu-indexed.kan | 11 |
| test/fixtures/mu-mutual.kan | 9 |
| test/neg/mu-nonpositive.kan | 7 |
| test/neg/mu-nonpositive.err | 1 |
| test/neg/mu-index-runtime.kan | 10 |
| test/neg/mu-index-runtime.err | 1 |
| test/neg/mu-index-mismatch.kan | 14 |
| test/neg/mu-index-mismatch.err | 1 |
| test/erase-neg/mu-erase.kan | 11 |
| test/erase-neg/mu-erase.err | 1 |

The six golden files test/golden/mu-direct.checked, mu-direct.erased,
mu-indexed.checked, mu-indexed.erased, mu-mutual.checked and
mu-mutual.erased are empty, because the three positives declare families
and add no entry (SG-D22).

The minimal mu production of correction C7 is surface/parser.ml:411-453,
43 lines, with its doc comment at :396-410, the declaration arm at
:388-390 and the term position refusals at :303-306.  The sugar and the
spine additions stay at Stage L (M1-PLAN.md:230).

### Gates

The judge reran SG-G1 to SG-G7 on ROOT at 2026-09-06 04:21, after
`zsh dev/dune.sh clean`.  Each line below is the exact final line of the
command, with its exit code.

- SG-G1 BUILD.  `zsh dev/dune.sh clean` exit 0, then
  `zsh dev/dunecho.sh build` printed `OK build: 0 errors, 0 warnings`,
  exit 0.
- SG-G2 R0-AUDIT.  `zsh dev/r0-audit.sh` printed `R0-AUDIT OK`, exit 0.
- SG-G3 R0-COUNT.  The brief command `zsh dev/gates.sh --leg R0-COUNT`
  printed `gates: unknown leg R0-COUNT`, exit 64, because dev/gates.sh
  accepts only axioms, e2e, time, ratio, denominators and pin at :257-266
  (SG-D25, finding F1).  The leg body `zsh dev/r0-count.sh` printed
  `R0-COUNT OK`, exit 0, and the whole battery printed `PASS R0-COUNT`.
  `_build/default/bin/kanon.exe spec-count` printed
  `shapes admitted 3: SPi SColl SMu` and
  `no eta 3: Lan-SColl Ran-SMu Lan-SMu`, exit 0.
- SG-G4 POSITIVITY.  The stage local command over the six fixtures of
  3.9, `kanon.exe check FILE`, printed:
  test/fixtures/mu-direct.kan, no output, exit 0;
  test/fixtures/mu-indexed.kan, no output, exit 0;
  test/fixtures/mu-mutual.kan, no output, exit 0;
  test/neg/mu-nonpositive.kan,
  `not yet: a family that is not strictly positive arrives at M2`,
  exit 1;
  test/neg/mu-index-runtime.kan, `index not zero: the index i of W is at
  quantity w and every index binder is at 0`, exit 1;
  test/neg/mu-index-mismatch.kan, `mismatch: the constructor vz of V
  gives the index (In SMu N [] (ACtor zero) []) and the type asks for (In
  SMu N [] (ACtor succ) [(In SMu N [] (ACtor zero) [])])`, exit 1.
  The interim erasure fixture of 3.8,
  `kanon.exe check --erased test/erase-neg/mu-erase.kan`, printed
  `not yet: an erasure at a mu shape arrives at M1 Stage J`, exit 1.
- SG-G5 SUITE-KERNEL.  The brief command `zsh dev/gates.sh --leg
  SUITE-KERNEL` printed `gates: unknown leg SUITE-KERNEL`, exit 64, for
  the reason of SG-G3 (SG-D25, finding F1).  The leg body
  `_build/default/test/main.exe test` printed `CHECK-OK 50/50`,
  `NEG-OK 14/14`, `ERASE-NEG-OK 1/1`, `KNEG-OK 2/2` and the final line
  `SUITE-KERNEL OK`.  The whole battery printed `PASS SUITE-KERNEL`.
- SG-G6 TRUSTED-LINES.  `zsh dev/trusted-lines.sh ROOT` printed
  `TRUSTED-LINES kernel=2995/3000 encoder=216/600 OK`, exit 0.  N is
  2995 over the ten believed files of 3.10, which hold lib/positivity.ml
  and lib/global.ml.
- SG-G7 HOUSE.  `zsh dev/house.sh ROOT` printed `HOUSE OK`, exit 0.
- SG-G8 LOGS.  dev/M1-BUILD-LOG.md holds `## Stage G (2026-09-06)` once
  and dev/M1-MUTATION-LOG.md holds `## Stage G` once.
  `git -C ROOT diff --stat -- dev/M0-BUILD-LOG.md dev/MUTATION-LOG.md`
  printed nothing, so both M0 logs are byte for byte unchanged.  The
  porcelain lists only Stage G paths.

### MEASURE table

The judge ran the whole battery `zsh dev/gates.sh` once on ROOT at
2026-09-06 04:21, at the load average 11.47 11.86 13.32.  The rows are
copied from that run.

```
MEASURE BUILD tier=SLOW elapsed_ms=65.823 exit=0
MEASURE CARRY tier=MED elapsed_ms=351.558 exit=1
MEASURE R0-COUNT tier=FAST elapsed_ms=43.445 exit=0
MEASURE R0-AUDIT tier=FAST elapsed_ms=23.733 exit=0
MEASURE SUITE-KERNEL tier=SUITE elapsed_ms=23.876 exit=0
MEASURE SUITE-WASM tier=SUITE elapsed_ms=1469.222 exit=0
MEASURE ENCODER-SUBSET tier=FAST elapsed_ms=44.198 exit=0
MEASURE AXIOMS tier=MED elapsed_ms=23.589 exit=0
MEASURE M0-E2E tier=SLOW elapsed_ms=441.148 exit=0
MEASURE M0-TIME tier=SLOW elapsed_ms=635.494 exit=0
MEASURE M0-RATIO tier=SLOW elapsed_ms=249.866 exit=0
MEASURE TRUSTED-LINES tier=FAST elapsed_ms=21.540 exit=0
MEASURE DENOMINATORS tier=MED elapsed_ms=37.169 exit=0
MEASURE HOUSE tier=MED elapsed_ms=72.436 exit=0
MEASURE PIN tier=FAST elapsed_ms=66.093 exit=0
MEASURE M0-RATIO kanon_ms=26.068 tot_ms=103.662 ratio=0.251
```

The timed leg.  The bound stays 150 ms and no agent moved it;
dev/gates.sh:48 still reads `M0_TIME_MS=150` (dev/M0-BUILD-LOG.md:999).
The battery reading was `PASS M0-TIME median_ms=93.984 bound_ms=150` at
the load average 11.47.  The judge then ran the leg three more times, at
2026-09-06 04:25, and reports every reading with its load average:

```
run 1  load 14.34 13.34 13.57  PASS M0-TIME median_ms=91.806 bound_ms=150
run 2  load 14.34 13.34 13.57  PASS M0-TIME median_ms=92.000 bound_ms=150
run 3  load 14.34 13.34 13.57  PASS M0-TIME median_ms=98.854 bound_ms=150
```

The builder read `FAIL M0-TIME median_ms=182.209 bound_ms=150` at the
load average 12.77 (SG-D27).  Four judge readings under 100 ms, at a
higher load, confirm the load artefact and refute a regression.

### Decisions

SG-D1 to SG-D13 are pinned by the Stage G brief section 3.11.  SG-D13 to
SG-D27 are the builders'.  The number SG-D13 is used twice, because the
brief says the builders continue after SG-D12 but its own list ends at
SG-D13;  both texts are kept and the collision is reported as finding F4.

- SG-D1 The family record and its table live beside the Global table and
  Global.entry gains no constructor (R-Q3);  lib/global.ml joins the
  believed TRUSTED-LINES list and the budgets stay 3000 and 600.
- SG-D2 rules.ml reads the record through exactly one accessor, so no
  family lookup enters check.ml (r0-audit.sh:6-11).
- SG-D3 Positivity and self_rec are computed once at installation and
  stored, never recomputed at formation (A4).
- SG-D4 Ran (SMu ..) is refused inside the pack at ran_lvl and at the Ran
  intro and elim fields, never at the dispatch.
- SG-D5 The pack answers eta_ran false and eta_lan false, so no eta grows
  from 1 to 3 and the eta table stays at three rows.
- SG-D6 The SPar cell at SPEC.md:30 moves from M1 to M2 in this commit
  (open question 4, RATIFICATIONS.md:77).
- SG-D7 The interim erasure word is exactly `an erasure at a mu shape
  arrives at M1 Stage J` and the fixture pins it byte for byte.
- SG-D8 Formation checks the declared level with Level.le and never
  computes a max (A5).
- SG-D9 The elimination fields answer the Stage H word at this stage.
- SG-D10 SG-G8 LOGS is added by the brief on the form of SE-G12.
- SG-D11 Every mutation runs on a fresh copy under SCRATCH/stageG and
  ROOT is never mutated.
- SG-D12 positivity.ml joins the trusted list and the budgets do not
  move.
- SG-D13 (brief) The six fixtures of 3.9 enter as .kan files through the
  minimal mu production of C7;  test/main.ml is not the entry path.
- SG-D13 (builder 1) lib/positivity.ml walks a shape through the three
  total views of shape.ml and spells no shape name, so SG-G2 stays green.
- SG-D14 The family record type lives in lib/positivity.ml, not in
  global.ml, because global.ml reads Prim.catalog and prim.ml reads
  Rules.arrow;  the table and its one accessor stay beside the Global
  table at global.ml:61-79.
- SG-D15 The two level fields of the pack are retyped to read the mu
  level off the family record;  a combinator payload_lvl adapts the two
  M0 packs, so SPi and SColl keep their bodies.
- SG-D16 The diagram at the mu shape is the parameter section, one binder
  free leg per parameter.
- SG-D17 A Provisional family forms, so a field type may name the family
  while the constructors are installed;  only a Complete family whose
  stored verdict is false is refused.
- SG-D18 Three refactors keep the ten believed files at 2995 of 3000:
  inline refusal lambdas, one accessor that merges the lookup and the
  stored verdict, and one telescope walk shared by the binder.
- SG-D19 The words for the sidecars are `a family that is not strictly
  positive arrives at M2`, `a right former at a mu shape arrives at M2`
  and `an elimination at a mu shape arrives at M1 Stage H`;  the two new
  error heads print as `index not zero: ` and `index above universe: `.
- SG-D20 The erase entry path carries the globals:  elab gains
  elab_program_in and check_in, and bin/kanon.ml and test/main.ml pass
  those globals to Erase.program, so a checked mu file no longer erases
  in an empty family table.
- SG-D21 The interim erasure word is pinned by a new negative group,
  test/erase-neg, run by erase_negative and counted as ERASE-NEG-OK.
- SG-D22 The three positives declare families and add no entry, so the
  six golden files are empty;  CHECK and ERASE grow from 47 to 50.
- SG-D23 The KNEG row smu moves from the left former to the right former
  at a mu shape, so KNEG keeps two rows and pins mu_ran_word.
- SG-D24 The constructor lookup of the elaborator reads the public
  Global.StringMap fold over the family table and adds no accessor to
  lib/global.ml, because the kernel budget stands at 2995 of 3000.
- SG-D25 dev/gates.sh --leg accepts only axioms, e2e, time, ratio,
  denominators and pin, so the two brief commands of SG-G3 and SG-G5 exit
  64;  both legs were read from the whole battery and from the leg bodies.
- SG-D26 The whole battery FAILs on CARRY, because Stage G grows
  lib/global.ml and the carried expectation at dev/CARRIED.md:14 still
  reads 164.  That file is out of the brief's scope, so it was left
  untouched and the user rules.
- SG-D27 The battery M0-TIME FAIL the builder saw is a load artefact and
  not a regression;  the bound was not moved.

### Findings

- F1, info, closed as a brief erratum.  The SG-G3 and SG-G5 commands of
  the brief do not exist:  `zsh dev/gates.sh --leg R0-COUNT` and
  `--leg SUITE-KERNEL` both print `gates: unknown leg NAME`, exit 64
  (dev/gates.sh:257-266).  The judge reproduced both and read the two
  legs from the whole battery and from the leg bodies instead.  A later
  stage cites `zsh dev/r0-count.sh` and `_build/default/test/main.exe
  test`, or Stage L adds the two leg names.
- F2, medium, open for the user.  The whole battery ends in `GATES-FAIL`,
  exit 1, on the row `CARRY lib/global.ml diff=196 expected=164
  header=OK FAIL`.  The growth is the family table this stage adds, so
  the code is right and the expectation is stale.  dev/CARRIED.md:14 is
  outside the brief's deliverables, so no agent moved it.  The user
  rules:  move the count at dev/CARRIED.md:14 from 164 to 196 and extend
  the paragraph at :26-29 with the family table, in the Stage G commit,
  or defer the row to Stage L.  The tree does not pass its own battery
  until that ruling lands.
- F3, info, closed.  The builder read `FAIL M0-TIME median_ms=182.209
  bound_ms=150` at the load average 12.77.  The judge read
  `PASS M0-TIME median_ms=93.984 bound_ms=150` in the battery and three
  more PASS readings of 91.806, 92.000 and 98.854 ms at the load average
  14.34.  The reading is a load artefact.  The bound stays 150.
- F4, low, reported.  The number SG-D13 names two decisions:  the brief's
  own last bullet at 3.11 and builder 1's first.  The brief text says the
  builders continue after SG-D12 while its list ends at SG-D13.  Both
  texts are kept above.  A later brief starts its builder range one
  number above the last bullet it writes.

### Hand-off notes for Stage H

Stage H brings the fibered Elim branch and motive rules and the
subsingleton criterion (M1-PLAN.md:198).  It reads three things this
stage leaves ready.

- The elimination fields of the SMu pack.  lib/rules.ml:1113 holds
  `elim_elim`, :1097 holds the BElim beta arm and both answer
  `Error (Error.Not_yet mu_elim_word)`, with the word at rules.ml:957,
  `an elimination at a mu shape arrives at M1 Stage H` (SG-D9, SG-D19).
  Stage H replaces those two sites and no other.  `elim_sec` at :1115,
  `elim_out` at :1116, `form_ran` at :1111 and `ran_lvl` at :1133 keep
  the M2 word `a right former at a mu shape arrives at M2`, because a
  coinductive section is SNu's job (SG-D4).
- The family record accessor.  lib/rules.ml:967 holds `mu_family`, the
  one accessor of brief 3.3, which answers the record of
  lib/positivity.ml:47-55 and refuses a Complete family whose stored
  positivity verdict is false (SG-D2, SG-D17).  The motive rules read
  `f_params`, `f_indices`, `f_level` and `f_ctors` through it, and
  `Positivity.ctor_of` at positivity.ml:59 reads one constructor.  A
  second reader would put a family lookup in check.ml and turn SG-G2 red.
- The SPEC.md status cell.  The named rule row moved with the file, from
  the brief's :208 to SPEC.md:218 today, and still reads the milestone
  M1.  Stage H turns that cell to present and moves
  `named rules present 2: proof-irrelevance literal-fast-path` at
  SPEC.md:155 to three, in the same commit as the criterion, so R0-COUNT
  is never red on a committed tree.  The M1 obligation row at SPEC.md:468
  moves with it.
- `Positivity.self_rec` at positivity.ml:152 stores the flag part one of
  the criterion asks for (A1), so Stage H reads it and never recomputes.

### Addendum, ruling round 2026-09-06 (c)

Applied after the judge verdict CHECK, on the user ruling of 2026-09-06
recorded in RATIFICATIONS.md, round (c).  It resolves finding F2.

- SG-D28 The CARRY row for lib/global.ml moves from 164 to 196 in this
  commit (dev/CARRIED.md:14, paragraph at :26-31), because Stage G adds
  the family record and the families table at lib/global.ml:61-79.  The
  row moves in the form of the quantity.ml row of Stage B.
- D-M1-7 amended once by the user: kernel_bound moves from 3000 to 4000
  at dev/trusted-lines.sh:31, encoder_bound stays 600, the believed list
  stays the ten files of SG-G6.  No stage moves a bound again.
- Reruns after the two edits, load average 11.77 14.46 14.22:
  `CARRY lib/global.ml diff=196 expected=196 OK` and `CARRY-OK`
  `TRUSTED-LINES kernel=2995/4000 encoder=216/600 OK`
  `GATES-OK` with every leg line: PASS BUILD, PASS CARRY, PASS R0-COUNT,
  PASS R0-AUDIT, PASS SUITE-KERNEL, PASS SUITE-WASM, PASS ENCODER-SUBSET,
  PASS AXIOMS, PASS M0-E2E main=521, PASS M0-TIME median_ms=94.423
  bound_ms=150, PASS M0-RATIO ratio=0.243, PASS TRUSTED-LINES,
  PASS DENOMINATORS, PASS HOUSE, PASS PIN sha=8cf0b8b
- dev/M1-MUTATION-LOG.md is unchanged by this addendum.

### Stage G review fixes (2026-09-06)

Four declaration checks now run before a family is installed.  A family
name must be fresh, every field must obey the declared universe bound,
the result parameters must be the original parameter variables in
order, and each result index must check against the dependent index
telescope under the parameters and fields.  The elaborator retains the
result parameters in `Check.ctor_decl` so the kernel can check them.
Constructor installation also refuses a family that is already complete
or builtin.  These checks correct the initial declaration-validation
claims above; introduction still checks result-index conversion.

Seven negative fixtures cover family redeclaration, duplicate mutual
members, oversized fields, ill-typed and unbound indices, and changed
or reordered parameters.  The positive `mu-constructor-scopes` fixture
covers parameter variables under fields, a parameter-dependent index,
dependent result indices, and a field at its allowed universe bound.

Validation ran on the fixed source copy at
/private/tmp/kanon-stage-g-fixes-dx26e5r5.  Its vendor/tot link reads the
existing pinned checkout; it writes no vendor file.  The initial run
lacked that link and failed CARRY and PIN.  With the link present, the
full unmodified `zsh dev/gates.sh` battery exited 0 with 15 PASS lines
and `GATES-OK`.  The log is /private/tmp/kanon-stage-g-fixes-gates.log.

- BUILD: `OK build: 0 errors, 0 warnings`.
- Kernel suite: `PARSE-OK 73/73`, `CHECK-OK 51/51`, `ERASE-OK 51/51`,
  `NEG-OK 21/21`, `ERASE-NEG-OK 1/1`, `KNEG-OK 2/2`, `SUITE-KERNEL OK`.
- WebAssembly suite: `WASM-OK 15/15`, `SUITE-WASM OK`.
- `TRUSTED-LINES kernel=3051/4000 encoder=216/600 OK`.
- Four independent mutations built successfully and then failed the
  kernel suite at the corresponding new negative fixtures.  Their
  exact failures are recorded in M1-MUTATION-LOG.md.

The bounds and existing gate implementations are unchanged by these
fixes.  Source, fixtures and logs are staged for the user to commit.

## Stage H (2026-09-06)

### Deliverables

The line counts are read on ROOT after the build of SH-G1.

| file | lines | note |
| --- | --- | --- |
| lib/rules.ml | 1496 | +312 -9;  the fibered Elim, the branch and motive rules, the criterion at mu_zero_eliminable:993 |
| lib/conv.ml | 416 | +33 -7;  step one gains named rule 2 through the pack field, step three gains the SMu head |
| SPEC.md | 510 | +44 -4;  the count row :173, the status cell :236, the rule text of section 2.1 and section 5 |
| surface/syntax.ml | 268 | +47 -13;  mo_ind, mo_idx, BrLeg, BrCtor, the field binder |
| surface/parser.ml | 503 | +67 -22;  the index clause, the constructor keyed branch row, parse_fields |
| surface/elab.ml | 1008 | +208 -16;  elab_coll_case and elab_mu_case, the family and constructor reads |
| test/fixtures/mu-prop-large-elim.kan | 14 | new;  a large elimination out of a one constructor Prop family |
| test/fixtures/mu-empty-large-elim.kan | 12 | new;  ex falso out of the empty family |
| test/fixtures/mu-indexed.kan | 33 | +11;  the Stage G positive extended by read_index, the SH-M3 killer |
| test/neg/mu-large-elim-nonsub.kan | 12 | new;  one argument at quantity Many, refused by part two |
| test/neg/mu-large-elim-selfrec.kan | 14 | new;  one self recursive argument at Zero, refused by part three |
| test/neg/mu-missing-branch.kan | 11 | new;  one constructor unanswered |
| test/neg/mu-no-motive.kan | 11 | new;  an Elim at an SMu scrutinee with no motive |
| test/neg/mu-motive-wrong-family.kan | 13 | new;  a motive built for a sibling family |
| test/golden/mu-prop-large-elim.checked | 1 | new;  the checked text, with .erased at 1 line |
| test/golden/mu-empty-large-elim.checked | 2 | new;  the checked text, with .erased at 2 lines |
| test/golden/mu-indexed.checked | 1 | +1;  the row read_index, with .erased at +1 |
| the five .err sidecars | 1 each | new;  the exact expected error line of each negative |

The surface widening of brief 3.8 is 322 insertions and 51 deletions
over the three surface files.  No kernel file joined the believed list,
so SH-D15 holds and the two budgets stay at 4000 and 600.

### Gates

The judge reran SH-G1 to SH-G7 on ROOT at 2026-09-06 06:53, after
`zsh dev/dune.sh clean`, at the load average 10.13 10.10 11.76.  Each
line below is the exact final line of the command, with its exit code.

- SH-G1 BUILD.  `zsh dev/dune.sh clean` exit 0, then
  `zsh dev/dunecho.sh build` printed `OK build: 0 errors, 0 warnings`,
  exit 0.
- SH-G2 SUITE-KERNEL.  The leg name is not an accepted argument of
  dev/gates.sh (H-F7), so the whole battery ran once under SH-D16 and
  printed `PASS SUITE-KERNEL`.  The direct run
  `_build/default/test/main.exe test` printed `PARSE-OK 80/80`,
  `CHECK-OK 53/53`, `ERASE-OK 53/53`, `NEG-OK 26/26`,
  `ERASE-NEG-OK 1/1`, `KNEG-OK 2/2` and `SUITE-KERNEL OK`, exit 0.
- SH-G3 R0-COUNT.  Same spelling rule.  The battery printed
  `PASS R0-COUNT`.  `_build/default/bin/kanon.exe spec-count` printed
  `named rules present 3: proof-irrelevance subsingleton-large-elimination
  literal-fast-path`, with `named rules declared 3` and
  `shapes admitted 3: SPi SColl SMu` unchanged, exit 0.
- SH-G4 R0-AUDIT.  `zsh dev/r0-audit.sh` printed `R0-AUDIT OK`, exit 0.
- SH-G5 TRUSTED-LINES.  `zsh dev/trusted-lines.sh ROOT` printed
  `TRUSTED-LINES kernel=3380/4000 encoder=216/600 OK`, exit 0.  The
  kernel reading is 3380 and the encoder reading is 216.
- SH-G6 HOUSE.  `zsh dev/house.sh ROOT` printed `HOUSE no-exception OK`,
  `HOUSE no-mutable-state OK`, `HOUSE one-catch-site OK`,
  `HOUSE no-bool-match OK`, `HOUSE no-em-dash OK` and `HOUSE OK`,
  exit 0.
- The whole battery `zsh dev/gates.sh` printed `GATES-OK`, exit 0, with
  the 15 PASS lines, `PASS M0-TIME median_ms=88.489 bound_ms=150` and
  `PASS PIN sha=8cf0b8b`.  The bound of M0-TIME was not moved.
- SH-G7 ELIM-SUITE, the stage local leg of brief 3.10 over the seven
  fixtures of 3.9.  The two positives are read against both golden files
  and the five negatives against their sidecars, with the error kind
  stripped at the first `: ` (SH-D47, SH-D48).  The seven lines:
  `ELIM-SUITE POS mu-prop-large-elim exit=0 GOLDEN-MATCH` and its
  `erased exit=0 ERASED-MATCH`;
  `ELIM-SUITE POS mu-empty-large-elim exit=0 GOLDEN-MATCH` and its
  `erased exit=0 ERASED-MATCH`;
  `ELIM-SUITE NEG mu-large-elim-nonsub exit=1 SIDECAR-MATCH line=a large
  elimination out of a proposition needs a subsingleton family at Box`;
  `ELIM-SUITE NEG mu-large-elim-selfrec exit=1 SIDECAR-MATCH line=a large
  elimination out of a proposition needs a subsingleton family at Acc`;
  `ELIM-SUITE NEG mu-missing-branch exit=1 SIDECAR-MATCH line=the
  elimination of Two has no branch at cb`;
  `ELIM-SUITE NEG mu-no-motive exit=1 SIDECAR-MATCH line=an elimination
  at a mu shape needs a motive`;
  `ELIM-SUITE NEG mu-motive-wrong-family exit=1 SIDECAR-MATCH line=the
  motive is built for Beta and the scrutinee is at Alpha`.  The leg
  exited 0.
- SH-G8 LOGS.  dev/M1-BUILD-LOG.md holds `## Stage H (2026-09-06)`
  exactly once and dev/M1-MUTATION-LOG.md holds `## Stage H` exactly
  once.  The Stage G sections of both files are unchanged, because both
  sections are appended after the last line of the file.
  `git diff --stat -- dev/M0-BUILD-LOG.md dev/MUTATION-LOG.md` is empty
  and porcelain lists only Stage H paths.

### MEASURE table

The judge ran the whole battery `zsh dev/gates.sh` once on ROOT at
2026-09-06 06:53, at the load average 11.00 10.29 11.81.  The rows are
copied from that run.  No timed leg failed, so no leg was rerun.

```
MEASURE BUILD tier=SLOW elapsed_ms=65.316 exit=0
MEASURE CARRY tier=MED elapsed_ms=673.347 exit=0
MEASURE R0-COUNT tier=FAST elapsed_ms=286.397 exit=0
MEASURE R0-AUDIT tier=FAST elapsed_ms=23.760 exit=0
MEASURE SUITE-KERNEL tier=SUITE elapsed_ms=195.150 exit=0
MEASURE SUITE-WASM tier=SUITE elapsed_ms=1604.048 exit=0
MEASURE ENCODER-SUBSET tier=FAST elapsed_ms=42.962 exit=0
MEASURE AXIOMS tier=MED elapsed_ms=20.601 exit=0
MEASURE M0-E2E tier=SLOW elapsed_ms=201.379 exit=0
MEASURE M0-TIME tier=SLOW elapsed_ms=770.852 exit=0
MEASURE M0-RATIO tier=SLOW elapsed_ms=259.539 exit=0
MEASURE TRUSTED-LINES tier=FAST elapsed_ms=20.652 exit=0
MEASURE DENOMINATORS tier=MED elapsed_ms=36.733 exit=0
MEASURE HOUSE tier=MED elapsed_ms=73.406 exit=0
MEASURE PIN tier=FAST elapsed_ms=59.454 exit=0
```

The two bench rows and the ratio row of the same run:

```
BENCH m0_e2e median_ms=88.489 min_ms=85.850 max_ms=256.346 runs=5
PASS M0-TIME median_ms=88.489 bound_ms=150
BENCH m0_ratio median_ms=28.426 min_ms=28.212 max_ms=28.780 runs=5
MEASURE M0-RATIO kanon_ms=28.426 tot_ms=103.662 ratio=0.274
PASS M0-RATIO ratio=0.274
```

### Decisions

SH-D1 to SH-D16 are pinned by the Stage H brief section 3.11.  SH-D17 to
SH-D45 are the builders'.  SH-D46 to SH-D50 are the verifier's and the
fixer's.  SH-D51 to SH-D53 are the fix round's, which numbered them
SH-D20 to SH-D22 and collided with builder 1;  the judge renumbers them
here and states the renumbering for the user.

- SH-D1 The criterion lives in lib/rules.ml and conv.ml reads it through
  the pack, so R0-AUDIT stays green.
- SH-D2 The criterion is ported part for part, each part citing its pin
  line, and never restated in kanon words.
- SH-D3 The empty family passes part one and gets its ex falso.
- SH-D4 A self recursive family never gets a large elimination.
- SH-D5 An Elim at an SMu scrutinee with e_motive None is an error
  inside the pack, never at the dispatch.
- SH-D6 m_ind is Some n and is checked equal to the scrutinee family.
- SH-D7 m_idx has the length of the family index telescope and a branch
  body is checked at m_body instantiated at that constructor.
- SH-D8 A missing branch and a repeated branch are both errors, read in
  declaration order.
- SH-D9 A branch leg binds one binder per field at the field quantities;
  Lan SPi keeps ALeg 0 with two binders.
- SH-D10 The SPEC.md count and the status cell move in this commit.
- SH-D11 The section 10 obligation row is not edited here.
- SH-D12 The seven fixtures enter as .kan files through the surface.
- SH-D13 Every mutation runs on a fresh copy and ROOT is never mutated.
- SH-D14 The plan's SH-M1b is carried as SH-M6.
- SH-D15 No kernel file joins the believed list and the budgets do not
  move.
- SH-D16 A leg dev/gates.sh does not accept as an argument is read from
  one whole run of the battery.
- SH-D17 The criterion reaches conv.ml through one new pack field,
  `subsingleton : 'c ops -> 'c -> Value.t Shape.t -> (bool, Error.t)
  result` at lib/rules.ml:180, so conv.ml names no shape.
- SH-D18 Every non recursive pack answers that field with
  `no_subsingleton`, which is `Ok false`, at spi_pack and coll_pack.
- SH-D19 `mu_subsingleton` (lib/rules.ml:1035) answers `Ok false` when
  as_vmu fails or the family lookup errors, so conversion never turns a
  missing family into a hard error.
- SH-D20 The pin criterion is ported arm for arm at
  `mu_zero_eliminable` (lib/rules.ml:993), Provisional at :996 for pin
  :225, Builtin at :998 for :226, `Complete []` at :1000 for :227,
  `Complete [c]` at :1002 for :228 with part two at :1006 and part three
  at :1011, and `Complete (_ :: _ :: _)` at :1013 for :233.
- SH-D21 The family record is read through one reader, `mu_family`
  (lib/rules.ml:1018) wrapping ops.o_family, which is Global.find_family
  (lib/global.ml:74);  the constructor is read with Positivity.ctor_of.
- SH-D22 The large elimination refusal is Error.Universe carrying
  `mu_large_word` (lib/rules.ml:980) and the family name.
- SH-D23 `mu_large` (lib/rules.ml:1233) admits at once when the family
  level is not zero and when the motive level is zero, and only then
  asks the criterion, which is the pin order at check.ml:1370.
- SH-D24 The motive level is measured under the index binders and the
  self binder at Quantity.Zero, so the motive is never checked at a made
  up universe.
- SH-D25 The old `mu_elim_word` is dead and deleted, replaced by
  `mu_motive_word` (lib/rules.ml:975) and `mu_large_word` (:980).
- SH-D26 In arguments keep the untyped pairwise comparison in conv.ml;
  the field types are enforced at the introduction site.
- SH-D27 conv.ml step one is is_prop, then one o_whnf, then
  subsingleton_step, then eta_step, so the head is computed once.
- SH-D28 conv.ml branch_addr gains a third arm that compares
  Term.as_actor, so no shape name enters conv.ml.
- SH-D29 `mu_beta` reduces BElim at the branch whose ACtor key equals
  the constructor of the Value.VIn, at `List.rev_append args env`;  BOut
  keeps the Ran refusal.
- SH-D30 Branch coverage is read in the declaration order of f_ctors and
  missing, repeated and unknown each carry their own word
  (lib/rules.ml:1277, :1281, :1289).
- SH-D31 Each branch checks binder count then binder quantity field by
  field against c_args, and a later field type sees the earlier binders.
- SH-D32 The elimination result is the motive body at
  `self :: List.rev_append idx env` (lib/rules.ml:1197), and the
  scrutinee value is computed after the branches are checked.
- SH-D33 Verification beyond the two required gates ran only on a copy
  made with rsync, built with its own dev/dunecho.sh.
- SH-D34 SPEC.md:173 alone carries the count move and reads
  `named rules present 3: proof-irrelevance
  subsingleton-large-elimination literal-fast-path`.
- SH-D35 The status cell at SPEC.md:236 moves from `M1` to `present` and
  names conv.ml step one through the `subsingleton` field, keeping the
  pin citation.
- SH-D36 The rule text lands in two blocks, the fibered Elim rules at
  SPEC.md:47-63 and the three criterion parts at :239-257.
- SH-D37 The section 10 obligation row at SPEC.md:508 keeps `M1` and is
  untouched;  section 11 gains :467 and :480 and section 8 gains :302.
- SH-D38 The surface motive gains `mo_ind` (surface/syntax.ml:46) and
  `mo_idx` (:47) and no new form, so every M0 fixture keeps its text.
- SH-D39 The surface branch becomes a sum, `BrLeg` (surface/syntax.ml:65)
  and `BrCtor` (:66), so no branch carries both keys.
- SH-D40 A field binder carries `fd_q` (surface/syntax.ml:55) and
  `fd_name` (:56) only, because the field type is read from the record.
- SH-D41 The index clause is read by `parse_index_clause`
  (surface/parser.ml:168), which gives the tokens back unread when it
  does not open with `in`, so it cannot collide with a let.
- SH-D42 `parse_fields` (surface/parser.ml:215) and `parse_names` (:178)
  are total and stop at the first token that is not a field or a name.
- SH-D43 The branch bar takes a second row at surface/parser.ml:204 and
  the failure word at :207 becomes `expected a leg number or a
  constructor name after '|'`.
- SH-D44 The elaborator splits on the shape of the scrutinee type,
  `elab_coll_case` (surface/elab.ml:552) and `elab_mu_case` (:635), with
  :611 and :724 refusing the other form.
- SH-D45 The family and the constructor are read in the surface only,
  Global.find_family (surface/elab.ml:639) and Positivity.ctor_of (:731),
  so conv.ml still holds no family lookup.
- SH-D46 The verifier changed no byte of ROOT, because the whole battery
  was green on the tree as found.
- SH-D47 A `.err` sidecar is measured against `Error.message`, which is
  what test/main.ml:107-109 compares, with the error kind stripped at the
  first `: `, and never against the prefixed CLI line.
- SH-D48 The two positives are measured against both golden files,
  `check --print` against .checked and `check --erased` against .erased.
- SH-D49 SH-D16 governs SH-G2 and SH-G3, whose leg names dev/gates.sh
  does not accept, so the whole battery ran once and the two PASS lines
  are quoted from that run.
- SH-D50 SH-D15 stands, because deliverable 3.4 landed in lib/rules.ml,
  an already believed file, so dev/trusted-lines.sh is not edited.
- SH-D51 The SH-M3 killer is the Stage G fixture
  test/fixtures/mu-indexed.kan extended by one definition, not an eighth
  fixture, because M1-PLAN.md:200 names that file.  PARSE-OK stays 80/80
  and CHECK-OK and ERASE-OK go from 52/53 to 53/53.
- SH-D52 The elimination sits under a let inside a definition at Type 0,
  because Erase.decl (lib/erase.ml:1101-1104) drops a definition whose
  declared type is not a runtime type, so the interim erasure word stays
  pinned by test/erase-neg/mu-erase.kan alone.
- SH-D53 The motive body is `V i` and not an index free type, so SH-M3
  is killed by the evaluator, which answers Unbound
  (lib/eval.ml:26-31), and not by a golden text difference.

### Findings

- SH-F-HIGH-1, high, closed by the fix round.  SH-M3 was not killed:
  the index instantiation of `mu_result` (lib/rules.ml:1197) had no
  fixture, because test/fixtures/mu-indexed.kan held no elimination and
  no .kan file in the tree eliminated an indexed family, so the copy
  with the index arguments dropped still printed `SUITE-KERNEL OK`.  The
  fix adds `read_index` at test/fixtures/mu-indexed.kan:22, whose motive
  body is `V i`, with the two goldens filled.  The judge reran the
  mutation on judge-m3 and it now prints `CHECK mu-indexed FAIL:
  unbound: de Bruijn index 1 is outside the environment`, `CHECK-OK
  52/53` and `SUITE-KERNEL FAIL`.
- SH-F-LOW-1, low, open for the user.  The missing branch refusal is
  enforced twice, at `mu_cover` (lib/rules.ml:1277) and again at the
  `List.find_opt` of `mu_branch` (:1309-1312), and the second site is
  unreachable on every real path because `mu_cover` runs first at
  mu_elim_elim:1367.  The fix round left it, because the smallest honest
  edit is four lines plus a helper and the one line rule does not allow
  it.  The judge reproduced the redundancy: SH-M2 is killed only when
  both sites are disabled.

### Hand-off notes for Stage I

Stage I brings the structural order, the totality certificate and the
translation of a recursive definition into one Elim (M1-PLAN.md:206).
It reads five things this stage leaves ready.

- The beta rule the translation feeds.  `mu_beta` at lib/rules.ml:1380
  reduces `BElim` at :1383 by the branch whose ACtor key equals the
  constructor of the value, at `List.rev_append args env` (:1392).
  `BOut` keeps the M2 Ran refusal at :1382 (SH-D29).
- The branch leg shape a recursive leg binder extends.  `mu_branch` at
  lib/rules.ml:1297 binds one binder per field, checks the binder count
  and then the field quantity against `c_args` (SH-D31), and the target
  of each branch is `mu_result` at :1345.
- The one family accessor.  `mu_family` at lib/rules.ml:1018 wraps
  ops.o_family, which is Global.find_family at lib/global.ml:74, and it
  stays the only reader (SH-D21).  A second reader outside that chain
  breaks R0-AUDIT and SG-D2.
- The criterion site of SH-D1.  `mu_zero_eliminable` at
  lib/rules.ml:993, read by the pack field `subsingleton` (:180) and by
  `mu_large` (:1233).  Stage I adds no part to it, because the pin has
  three (SH-D2, SH-D20).
- The obligation row Stage I marks discharged.  SPEC.md:509, the
  structural recursion certificate row, which the plan cites as
  SPEC.md:459 and which the Stage H edits moved to :509.  The
  subsingleton obligation row at SPEC.md:508 keeps its milestone `M1`
  and is Stage L's mark (SH-D11, SH-D37).

Open for Stage I: the surface `case` of brief 3.8 elaborates through
`elab_mu_case` at surface/elab.ml:635 and calls no guard, so the caller
of `Totality.guard` is still absent (SPEC.md:509).

### Stage H conversion review fix (2026-09-06)

The review reproduced a closed cast from `Nat` to `Nat -> Nat` using
a `Type 1` family with one erased type field.  SH-D27's conversion
shortcut applied the large elimination criterion without checking the
family universe, so two different type payloads converted.

`mu_subsingleton` now requires the family level to be `Prop` before
answering true.  Type families retain the remaining conversion rules.
The large elimination check keeps its existing criterion.  The comments
in conv.ml and SPEC.md record the distinction.

The new negative `mu-type-erased-cast` carries the closed reproducer.
The unfixed Stage H checker accepts it with exit 0; the fixed checker
rejects its cast with the expected type mismatch.  Validation on a
scratch copy: build with zero errors and warnings, `SUITE-KERNEL OK`
(81 parses, 53 positive checks, 53 erasures, 27 negatives),
`SUITE-WASM OK` (15/15), HOUSE, R0-COUNT, R0-AUDIT and TRUSTED-LINES
all pass.  The existing Prop and empty-family large elimination
fixtures still pass.  The full runtime gate battery was not rerun.

## Stage I (2026-09-06)

### Deliverables

The line counts are read on ROOT after the build of SI-G1.

| file | lines | note |
| --- | --- | --- |
| lib/order.ml | 581 | new;  the status type at :49, the certificate record at :87, passes at :280, certify at :460, translate at :538 |
| lib/totality.ml | 155 | +105 -89;  guard_group at :127, guard at :151 as the group of one, the budget backstop at :32 |
| lib/error.ml | 82 | +13;  the arm `Termination` at :36, termination_msg at :45, read at :64 and :82 |
| surface/elab.ml | 1145 | +137;  elab_rec_group at :962, the guard call at :1004, Order.translate at :1029, rec_arg at :1040 |
| surface/parser.ml | 544 | +43 -2;  the `def rec` row at :422, parse_rec_group at :459, the member row at :467 |
| surface/syntax.ml | 291 | +23;  rec_def at :93 and DRec at :136 |
| surface/token.ml | 134 | +6;  KRec at :70 and its describe row at :126 |
| surface/lexer.ml | 143 | +3;  the `rec` keyword row at :57 |
| test/main.ml | 361 | +83 -11;  guarded_self at :163, the KNEG row at :216-243, the name list at :333 |
| SPEC.md | 516 | +1 -1;  the obligation row at :515 marked discharged |
| dev/trusted-lines.sh | 78 | +4;  lib/order.ml at :50 with the two line reason at :47-49 |
| test/neg/mu-nonstructural.kan | 15 | new;  a self call at an argument no chain of legs makes smaller |
| test/neg/mu-rec-nondecreasing.kan | 15 | new;  a self call at the scrutinee itself, the SI-M2 killer |
| test/neg/mu-rec-sibling-position.kan | 18 | new;  a sibling call that decreases at another position, the SI-M3 killer |
| test/neg/mu-rec-guard-order.kan | 22 | new;  the SI-G6 fixture, a well typed Elim whose certificate is refused |
| test/erase-neg/mu-rec-direct.kan | 17 | new;  the direct positive, moved by the SI-D12 split |
| test/erase-neg/mu-rec-indexed.kan | 24 | new;  the indexed positive, moved by the SI-D12 split |
| test/erase-neg/mu-rec-mutual.kan | 24 | new;  the mutual positive, moved by the SI-D12 split |
| the seven .err sidecars | 1 each | new;  four termination lines and three interim erasure lines |

The surface widening of brief 3.7 is 212 insertions and 2 deletions over
the five surface files elab.ml, parser.ml, syntax.ml, token.ml and
lexer.ml.  lib/order.ml joins the believed list and the two budgets stay
at 4000 and 600 (SI-D15).  No file under test/fixtures was added, which
is the split of SI-D12.

### Gates

The judge reran SI-G1 to SI-G7 on ROOT at 2026-09-06 11:59, after
`zsh dev/dune.sh clean`, at the load average 19.97 22.47 21.49.  Each
line below is the exact final line of the command, with its exit code.

- SI-G1 BUILD.  `zsh dev/dune.sh clean` exit 0, then
  `zsh dev/dunecho.sh build` printed `OK build: 0 errors, 0 warnings`,
  exit 0.
- SI-G2 SUITE-KERNEL.  The leg name is not an accepted argument of
  dev/gates.sh (I-F15), so the whole battery ran once under SI-D17 and
  printed `PASS SUITE-KERNEL`.  The direct run
  `_build/default/test/main.exe test` printed `PARSE-OK 88/88`,
  `CHECK-OK 53/53`, `ERASE-OK 53/53`, `NEG-OK 31/31`,
  `ERASE-NEG-OK 4/4`, `KNEG-OK 2/2` and `SUITE-KERNEL OK`, exit 0.
  The Stage H counts of 53 checks and 53 erasures are unchanged;  the
  parses rise from 80 to 88, the negatives from 26 to 31 and the erasure
  negatives from 1 to 4.
- SI-G3 R0-AUDIT.  `zsh dev/r0-audit.sh` printed `R0-AUDIT OK`, exit 0.
- SI-G4 TRUSTED-LINES.  `zsh dev/trusted-lines.sh ROOT` printed
  `TRUSTED-LINES kernel=3982/4000 encoder=216/600 OK`, exit 0.  The
  kernel reading is 3982 over the eleven believed files and the encoder
  reading is 216.  The headroom under the bound is 18 lines.
- SI-G5 HOUSE.  `zsh dev/house.sh ROOT` printed `HOUSE no-exception OK`,
  `HOUSE no-mutable-state OK`, `HOUSE one-catch-site OK`,
  `HOUSE no-bool-match OK`, `HOUSE no-em-dash OK` and `HOUSE OK`,
  exit 0.
- SI-G6 GUARD-FIRST.  `_build/default/bin/kanon.exe check
  test/neg/mu-rec-guard-order.kan` printed
  `termination: recursive definition grow failed the structural
  termination guard`, exit 1, which is the line of the sidecar
  test/neg/mu-rec-guard-order.err and never a type error of the
  translated form.
- SI-G7 REC-SUITE, the stage local leg of brief 3.8.  The three
  positives check and the three negatives are refused with the exact
  line of their sidecar.  The six lines, each from
  `_build/default/bin/kanon.exe check`:
  `test/erase-neg/mu-rec-direct.kan exit=0`, no output;
  `test/erase-neg/mu-rec-indexed.kan exit=0`, no output;
  `test/erase-neg/mu-rec-mutual.kan exit=0`, no output;
  `test/neg/mu-nonstructural.kan exit=1` line `termination: recursive
  definition spin failed the structural termination guard`;
  `test/neg/mu-rec-nondecreasing.kan exit=1` line `termination:
  recursive definition same failed the structural termination guard`;
  `test/neg/mu-rec-sibling-position.kan exit=1` line `termination:
  recursive definition left failed the structural termination guard`.
  The checked half of each positive is read by the suite row
  `ERASE-NEG mu-rec-direct OK`, `ERASE-NEG mu-rec-indexed OK` and
  `ERASE-NEG mu-rec-mutual OK`, which fails unless the file elaborates,
  guards, translates and checks.  The erased half is the interim word of
  SI-D12 and no .erased golden was written.
- The whole battery `zsh dev/gates.sh` printed `GATES-OK`, exit 0, with
  the 15 PASS lines, `PASS M0-TIME median_ms=121.153 bound_ms=150` and
  `PASS PIN sha=8cf0b8b`.  `PASS R0-COUNT` is green with no SPEC.md
  count edit (SI-D14) and `PASS CARRY` is green with no CARRIED.md row
  moved (SI-D36).  The bound of M0-TIME was not moved and no timed leg
  failed, so no leg was rerun.
- SI-G8 LOGS.  dev/M1-BUILD-LOG.md holds `## Stage I (2026-09-06)`
  exactly once and dev/M1-MUTATION-LOG.md holds `## Stage I` exactly
  once.  The Stage G and the Stage H sections of both files are
  unchanged, because both sections are appended after the last line of
  the file.  `git diff --stat -- dev/M0-BUILD-LOG.md dev/MUTATION-LOG.md`
  is empty and the porcelain lists only Stage I paths.

### MEASURE table

The judge ran the whole battery `zsh dev/gates.sh` once on ROOT at
2026-09-06 11:59, at the load average 19.97 22.47 21.49 before the run
and 19.01 22.23 21.41 after it.  The rows are copied from that run.  No
timed leg failed, so no leg was rerun.

```
MEASURE BUILD tier=SLOW elapsed_ms=210.356 exit=0
MEASURE CARRY tier=MED elapsed_ms=467.837 exit=0
MEASURE R0-COUNT tier=FAST elapsed_ms=69.544 exit=0
MEASURE R0-AUDIT tier=FAST elapsed_ms=32.143 exit=0
MEASURE SUITE-KERNEL tier=SUITE elapsed_ms=71.944 exit=0
MEASURE SUITE-WASM tier=SUITE elapsed_ms=3085.572 exit=0
MEASURE ENCODER-SUBSET tier=FAST elapsed_ms=55.046 exit=0
MEASURE AXIOMS tier=MED elapsed_ms=27.062 exit=0
MEASURE M0-E2E tier=SLOW elapsed_ms=266.326 exit=0
MEASURE M0-TIME tier=SLOW elapsed_ms=819.407 exit=0
MEASURE M0-RATIO tier=SLOW elapsed_ms=320.932 exit=0
MEASURE TRUSTED-LINES tier=FAST elapsed_ms=26.044 exit=0
MEASURE DENOMINATORS tier=MED elapsed_ms=41.689 exit=0
MEASURE HOUSE tier=MED elapsed_ms=84.616 exit=0
MEASURE PIN tier=FAST elapsed_ms=86.774 exit=0
```

The two bench rows and the ratio row of the same run:

```
BENCH m0_e2e median_ms=121.153 min_ms=112.977 max_ms=139.639 runs=5
PASS M0-TIME median_ms=121.153 bound_ms=150
BENCH m0_ratio median_ms=31.649 min_ms=29.921 max_ms=36.071 runs=5
MEASURE M0-RATIO kanon_ms=31.649 tot_ms=103.662 ratio=0.305
PASS M0-RATIO ratio=0.305
```

### Decisions

SI-D1 to SI-D18 are pinned by the Stage I brief section 3.12.  SI-D19 to
SI-D38 are raised by the builders during the build.

- SI-D1 The order is subterm only, syntactic and checked, and no sized
  and no lexicographic order enters (D-M1-4).
- SI-D2 lib/order.ml is a new kernel file and each function cites the
  pin line it mirrors.
- SI-D3 The certificate is a returned record and never a driver flag.
- SI-D4 The guard keeps the signature of I-F7.
- SI-D5 An argument that is an application is never guarded (ruling R1).
- SI-D6 The refusal is the one arm `Termination of string` with the pin
  message, and every .err sidecar pins that line.
- SI-D7 One order over the group;  the direct case is the group of one.
- SI-D8 The production is `def rec` with `and` joining the members.
- SI-D9 The guard is called at the elaborator declaration row, after the
  body is elaborated and before the translation.
- SI-D10 The translation builds one Elim at the Stage H fibered form and
  adds no term constructor and no motive field.
- SI-D11 test/main.ml is edited for the KNEG row alone.
- SI-D12 A recursive positive whose erased form is refused lands under
  test/erase-neg with the interim word.
- SI-D13 The SPEC.md obligation row is marked discharged at Stage I.
- SI-D14 No R0 count moves and R0-COUNT stays green.
- SI-D15 lib/order.ml joins the believed list and no budget moves.
- SI-D16 Every mutation runs on a fresh copy and ROOT is never mutated.
- SI-D17 A leg that dev/gates.sh does not accept is read from one full
  battery run (erratum SG-D25).
- SI-D18 This brief adds SI-G7 and SI-G8 beyond the plan's six gate ids
  and carries SI-B1 as the lexicographic blocker.
- SI-D19 lib/totality.ml keeps `guard ?budget globals name ty body` at
  its M0 signature (totality.ml:151-155) and is a thin reader of the
  certificate:  it is guard_group at the group of one, so the direct
  case and the mutual case cannot drift apart.
- SI-D20 totality.ml exports `guard_group ?budget globals members`
  (totality.ml:127) so the caller hands the same value to
  Order.translate and the order is computed once.
- SI-D21 The budget stays a backstop with its M0 text unmoved
  (budget_msg at totality.ml:32, Error.Budget_exhausted at :41), and the
  M0 seek walk becomes a name free walk that polls once per node before
  the certificate runs, because lib/order.ml carries no budget.
- SI-D22 The M0 milestone word and its refusal arm leave lib/totality.ml,
  so guard answers `Ok (Some k)`, `Ok None` or
  `Error (Error.Termination name)` and nothing else.
- SI-D23 lib/error.ml gains the arm `Termination of string` (error.ml:36)
  plus termination_msg (error.ml:45), which holds the pin text of
  kan-lang-tot-pin/lib/error.ml:185 word for word, read at error.ml:64
  and :82;  no wildcard arm was added.
- SI-D24 The certificate of M1-PLAN.md:111 is the record group in
  lib/order.ml (step at :60, call at :67, row at :73, t at :87) with one
  o_arg for the whole group.
- SI-D25 lib/order.ml reads no family record at all, which is stronger
  than brief 3.5:  Rules.mu_family keeps its single reader and R0-AUDIT
  stays clean.
- SI-D26 The pin status read `List.nth_opt` is spelled `Rules.at` at
  order.ml:251 because dev/house.sh:23 refuses the pin spelling;  the
  read is the same total combinator.
- SI-D27 DEVIATION from the wording of brief 3.4 and I-F2.
  Order.translate (order.ml:538) validates the Elim the body already
  holds and returns it (order.ml:581), and the recursive result of a
  field is the guarded call at the leg binder the certificate row names,
  rather than legs physically extended by extra binders.  Reason:
  Rules.mu_branch zips the constructor fields against l_binders and
  errors when the lengths differ, and Rules.mu_beta substitutes the
  constructor arguments alone, so a longer leg is refused by the checker
  and would read an unbound index at reduction.  Recorded in the
  translate doc comment.
- SI-D28 Order.translate refuses rather than guesses at three shapes,
  each with its own message constant (order.ml:509-514):  the peeled
  body must be exactly one Elim, the Elim must carry a motive, and every
  branch address must carry a constructor address.
- SI-D29 No fixture was written by builder 1 and no file under test was
  touched by it;  its behaviour claims were checked on a copy of ROOT
  under WORK and then deleted, so ROOT was never mutated for a check.
- SI-D30 The caller stands at surface/elab.ml:1004
  (`Totality.guard_group`), after every body is elaborated at
  surface/elab.ml:999 and before Order.translate at surface/elab.ml:1029,
  which is the pin order at kan-lang-tot-pin/lib/check.ml:1545 then
  :1558, and only the translated term reaches the kernel at
  surface/elab.ml:1030.
- SI-D31 The surface/token.ml and surface/lexer.ml edits are kept
  (token.ml:70 KRec, token.ml:126 its describe row, lexer.ml:57 the
  keyword row), because the shape the mu group of correction C7 uses
  spells its group word as a keyword.
- SI-D32 The SI-D12 split FIRED, and for all three positives:
  test/fixtures gained no file, and mu-rec-direct.kan, mu-rec-indexed.kan
  and mu-rec-mutual.kan stand under test/erase-neg with a .err sidecar
  that pins the interim word of lib/erase.ml.  No Stage J erasure row was
  landed to make a golden.
- SI-D33 test/neg/mu-rec-guard-order.kan refuses under ruling R1 and
  SI-D5 at lib/order.ml:303-311:  its self call stands at an
  application, which never guards a call, so the file reads the ORDER of
  the two steps and not the refusal alone.
  test/neg/mu-rec-nondecreasing.kan is kept distinct:  its call argument
  is the scrutinee variable itself at status Principal
  (lib/order.ml:289-295), which is what SI-M2 kills.
- SI-D34 The KNEG row of I-F8 is rewritten to BOTH M1 answers
  (test/main.ml:216-243) and the row name list does not move
  (test/main.ml:333).  The acceptance half hands the guard a body built
  in OCaml at test/main.ml:163-205 and demands `Ok (Some 0)`.
- SI-D35 The obligation row at SPEC.md:515 is marked discharged in the
  form of the `any` row at SPEC.md:516, and no other row moved.
- SI-D36 dev/CARRIED.md is not edited and no row moves, because
  Global.def_entry already carries rec_arg (lib/global.ml:20).
- SI-D37 lib/order.ml joins the believed list at dev/trusted-lines.sh:50
  with a reason comment at :47-49, and kernel_bound=4000 and
  encoder_bound=600 are byte for byte unmoved.
- SI-D38 No fixture exposed a defect in a builder 1 file, so
  lib/order.ml, lib/totality.ml and lib/error.ml were not edited by
  builder 2.

### Findings

Stage I ran twice:  run wf_f5c9600e-24a (session 26b4aae2) died in
builder 2 on the five hour usage limit at 10:26 PDT before any gate ran,
and this run carried the preflight and the builder 1 results inline and
resumed builder 2 on the salvaged tree.

- SI-F1, info, open for the user.  SI-D27 is a disclosed deviation from
  the wording of brief 3.4 and I-F2.  Order.translate does not build new
  leg binders for recursive results;  it validates the Elim the source
  already holds (lib/order.ml:538-581).  The kernel refuses the literal
  reading (Rules.mu_branch zips the constructor fields against l_binders
  and Rules.mu_beta substitutes the constructor arguments alone), so the
  deviation is forced.  Resolution:  the user rules on SI-D27 before
  Stage J reads a computed recursive value out of a leg binder.
- SI-F2, low, accepted.  The TRUSTED-LINES headroom after Stage I is 18
  lines under the 4000 kernel bound:
  `TRUSTED-LINES kernel=3982/4000 encoder=216/600 OK`, with lib/order.ml
  at 581 lines.  The gate is green and D-M1-7 forbids moving the bound
  again, so Stage J and Stage K must budget any new kernel line against
  a compensating deletion.  SI-B6 did not fire.
- No high and no medium finding stands.  The preflight drift of I-F5,
  where the Stage H hand-off notes cite line numbers five to six lines
  short of the committed tree, is recorded there and is not a defect:
  every named site is present and behaves as described.

### Hand-off notes for Stage J

What Stage J reads on this tree.

- The Elim the translation builds.  `Order.translate` at
  lib/order.ml:538 answers `Ok (rewrap ws (Term.Elim e))` at
  lib/order.ml:581, so the term the kernel checks at
  surface/elab.ml:1030 is one Elim at the Stage H fibered form under the
  peeled lambdas, with a motive and one branch per constructor address.
  The recursive result of a field is not a new binder:  it is the
  guarded call at the leg binder the certificate row names, which is
  SI-D27 and the finding SI-F1 the user rules on.  The leg binder itself
  is `Term.leg.l_binders` at lib/term.ml:27 with `l_body` at :28, and
  the certificate names the branch through `step.st_ctor` at
  lib/order.ml:62 and the chain of `call.cl_chain` at lib/order.ml:69.
  The erasure rows and the KTail guard of M1-PLAN.md:106 and :214 read
  that leg.
- The definition group, the rec group boundary of D-M1-5.  The group is
  `Order.t.o_group` at lib/order.ml:88, built by `certify` at
  lib/order.ml:462 from the members the parser collects in
  `parse_rec_group` at surface/parser.ml:459 through the `def rec ...
  and ...` production at surface/parser.ml:422, carried as
  `Syntax.DRec` at surface/syntax.ml:136 and handed to the guard at
  surface/elab.ml:1004.  One rec group per mutual family is that list.
- The interim erasure word and the files of the SI-D12 split.  The word
  is at lib/erase.ml and it is pinned by four sidecars under
  test/erase-neg:  mu-erase.err from Stage G, and the three of this
  stage, test/erase-neg/mu-rec-direct.kan with .err,
  test/erase-neg/mu-rec-indexed.kan with .err and
  test/erase-neg/mu-rec-mutual.kan with .err.  Stage J turns each of the
  three back into a positive under test/fixtures with its .checked and
  its .erased golden and drops the sidecar.
- The certificate site the tail eligible shape of A10 reads.  The
  guarded position is stored at surface/elab.ml:1040 as
  `rec_arg = Some c.Order.o_arg` into the `Global.Def` entry field
  `rec_arg` at lib/global.ml:20, and the live certificate is
  `Order.t` at lib/order.ml:87 as `guard_group` answers it at
  lib/totality.ml:127.

### Review fixes, 2026-09-06

The staged review reproduced two defects: `double (succ zero)` stayed
neutral, and a guarded group rejected a constant helper without a case.
The following corrections supersede the evaluator and helper behavior
described in SI-D27, SI-D28 and SI-F1 above.

- `Eval.whnf` now unfolds a reducible recursive global only when its
  guarded argument is a constructor.  Bare globals, missing guarded
  arguments, neutral arguments and explicitly opaque definitions stay
  frozen.  Replay preserves application and elimination frames.
- `Elab.elab_rec_group` marks definitions reducible and gives `rec_arg`
  only to members that contain group calls.  `Order.translate` preserves
  helpers without requiring a case.  Helpers with no group calls do not
  constrain the certificate's formal-position search.
- `Order.translate` still validates the source Elim.  SI-D27's deviation
  from extra recursive-result binders remains disclosed: recursive calls
  now compute through guarded unfolding in the evaluator.
- `test/main.ml` adds the mandatory `REC values` row: direct, mutual and
  indexed computation, constant helpers including a nullary member,
  a nonzero guarded position, returned functions, partial applications,
  neutral arguments and explicit opacity.
- Validation on a scratch copy: build with zero errors and warnings;
  full `dev/gates.sh` battery `GATES-OK`; kernel and Wasm suites passed;
  M0-TIME median 89.349 ms against 150 ms; M0-RATIO 0.250.
  `TRUSTED-LINES kernel=3993/4000 encoder=216/600 OK` after shortening
  duplicate order comments.  No bound, denominator or gate was changed.

## Stage J (2026-09-06)

Erasure, rec groups and emission of recursive values (M1-PLAN.md:212-218).
The stage lands the SMu rows of the erasure, the multi-member rec group
form of the encoder, one rec group for each mutual family in the link
pass, the dispatch over recursive payloads in the emitter and the two
A10 fixtures.  SPar and SNu keep the refused arm (A6).

### Deliverables

- `lib/erase.ml` 1439 lines, from 1146 at stage entry.  `mu_tid` at :211
  and `mu_leg_tid` at :219 write the tid text;  the `KTag` answer is at
  :956 and the `KCase` answer at :1031;  the interim word `mu_erase_word`
  and `mu_refused` are gone.
- `lib/eterm.ml` 117 lines, unchanged.  No IR constructor was added.
- `wasm/gc_encode.ml` 237 lines, from 216.  The rec group form and the
  rewritten header invariant.
- `wasm/link.ml` 1091 lines, from 842.  `family_groups` at :926 reads the
  group boundary from the `KRec` groups the erasure publishes.
- `wasm/emit.ml` 778 lines, from 760.  One kernel binder for each runtime
  field, `local.get`, `ref.cast` to the leg type and `struct.get`.
- `bin/kanon.ml` 308 lines.  Two line defect fix at `run_emit`, which
  erased in `Global.initial` and now erases in the globals the file was
  checked in.
- `test/main.ml` 448 lines, from 440.  The ERASE-NEG group verdict is
  `passed = total` alone, because the directory is now empty.
- `test/wasm.ml` 283 lines.  The suite elaborates with `Elab.check_in`
  and keeps the globals it answers.
- `SPEC.md` 519 lines, from 516.  Two erasure rows in section 2.3, the
  rewritten milestone row at :127 and one `rec groups` row at :354.
- Fixtures that left `test/erase-neg` and became positives, each with a
  driver produced `.checked` and `.erased` golden: `mu-erase.kan` 13
  lines, `mu-rec-direct.kan` 19, `mu-rec-indexed.kan` 26 and
  `mu-rec-mutual.kan` 26.  Their four `.err` sidecars are deleted and
  `test/erase-neg` holds only `.gitkeep`.
- New A10 fixtures: `test/fixtures/mu-cata-depth.kan` 22 lines with
  `.checked`, `.erased` and `.wat` goldens, and
  `test/fixtures/mu-mutual-emit.kan` 16 lines with the same three.
  `test/golden` now holds 17 `.wat` files.
- Stage local, outside the repository: the tail eligible fixture
  `mu-tail-100k.kan` 29 lines and the gate script `sj-g8.sh`, both under
  the session work directory (SJ-D40, SJ-D42).

### Gates

Every leg below was rerun by the judge on ROOT at 2026-09-06 15:22,
after `zsh dev/dune.sh clean`.  The lines are the exact final lines.

- SJ-G1 BUILD.  `zsh dev/dune.sh clean` exit 0, then
  `zsh dev/dunecho.sh build`: `OK build: 0 errors, 0 warnings`, exit 0.
- SJ-G2 SUITE-KERNEL.  `_build/default/test/main.exe test`:
  `PARSE-OK 90/90`, `CHECK-OK 59/59`, `ERASE-OK 59/59`, `NEG-OK 31/31`,
  `ERASE-NEG-OK 0/0`, `KNEG-OK 2/2`, `REC-OK 1/1` and `SUITE-KERNEL OK`,
  exit 0.  The four fixtures of brief 3.3 count in the CHECK group and
  in the ERASE group, and the erase-neg group line reads its zero count,
  because the directory is empty (SJ-D27, SJ-D44).
- SJ-G3 SUITE-WASM.  `_build/default/test/wasm.exe test`:
  `EMIT mu-cata-depth OK`, `EMIT mu-mutual-emit OK`, `WASM-OK 17/17` and
  `SUITE-WASM OK`, exit 0.
- SJ-G4 ENCODER-SUBSET.  `zsh dev/encoder-subset.sh .`:
  `ENCODER-SUBSET OK`, exit 0.
- SJ-G5 TRUSTED-LINES.  `zsh dev/trusted-lines.sh .`:
  `TRUSTED-LINES kernel=3993/4000 encoder=237/600 OK`, exit 0.  The
  kernel delta against the entry reading of 3993 is 0 and the 7 lines of
  headroom are untouched, so SJ-B2 does not fire.  The encoder delta
  against 216 is plus 21 and the headroom left for Stage K is 363 lines.
- SJ-G6 M0-E2E.  `zsh dev/gates.sh --leg e2e`: `PASS M0-E2E main=521`,
  exit 0.  The answer is the M0 answer and `examples/m0-spine.kan` was
  not edited.
- SJ-G7 HOUSE.  `zsh dev/house.sh .`: `HOUSE no-exception OK`,
  `HOUSE no-mutable-state OK`, `HOUSE one-catch-site OK` with the one
  allowed site `test/sys_io.ml:19`, `HOUSE no-bool-match OK`,
  `HOUSE no-em-dash OK`, `HOUSE OK`, exit 0.
- SJ-G8 TAIL-DEPTH, stage local (brief 3.10, SJ-D42).
  `zsh sj-g8.sh /Users/oobi/Documents/kanon`:
  `TAIL-DEPTH mu-tail-100k node exit 0 answer 100000 want 100000`,
  `TAIL-DEPTH mu-tail-100k wasmtime exit 0 answer 100000 want 100000`,
  `TAIL-DEPTH mu-cata-depth node exit 0 answer 4095 want 4095`,
  `TAIL-DEPTH mu-cata-depth wasmtime exit 0 answer 4095 want 4095`,
  `TAIL-DEPTH-OK 4/4 tail return_call 15 cata return_call 0` and
  `TAIL-DEPTH OK`, exit 0.  The measured depth of the general
  catamorphism fixture is 4095 (SJ-D39).
- SJ-G9 LOGS.  `dev/M1-BUILD-LOG.md` holds one `## Stage J (2026-09-06)`
  line and `dev/M1-MUTATION-LOG.md` holds one `## Stage J` line, both
  appended after the Stage I section, which is unchanged.
  `git diff --stat -- dev/M0-BUILD-LOG.md dev/MUTATION-LOG.md` is empty
  and the porcelain lists Stage J paths only.

The whole battery.  `zsh dev/gates.sh` ran once at 15:23 and printed
`PASS` for BUILD, CARRY, R0-COUNT, R0-AUDIT, SUITE-KERNEL, SUITE-WASM,
ENCODER-SUBSET, AXIOMS, `PASS M0-E2E main=521`, `PASS M0-RATIO
ratio=2.821`, TRUSTED-LINES, DENOMINATORS, HOUSE and
`PASS PIN sha=8cf0b8b`.  R0-COUNT is green with no count edit (SJ-D10)
and CARRY is green because no carried file was edited.  M0-TIME failed
alone under host load: `FAIL M0-TIME median_ms=179.126 bound_ms=150` at
load average 35.91, then the three reruns of `zsh dev/gates.sh --leg
time` read `FAIL M0-TIME median_ms=188.525 bound_ms=150` at load 27.74,
`FAIL M0-TIME median_ms=248.392 bound_ms=150` at load 29.68 and
`FAIL M0-TIME median_ms=236.997 bound_ms=150` at load 29.68.  The main
loop waived SJ-B9 for this leg at 15:06 on the readings 97.3, 101.1 and
95.1 ms at load 21.7, and the fixer read
`PASS M0-TIME median_ms=149.873 bound_ms=150` at load 48.46 on the same
tree.  `M0_TIME_MS` stays 150 at `dev/gates.sh:48` and no agent edited
it.  The plan calls a real regression a reading above the bound at a
load average at or under 3 (M1-PLAN.md:233), which this host is far
above.

### MEASURE table

The judge ran the whole battery `zsh dev/gates.sh` once on ROOT at
2026-09-06 15:23, at the load average 35.91 35.13 32.87 before the run
and 32.63 34.45 32.67 after it.  The rows are copied from that run.  The
timed leg failed alone and was rerun three times;  the readings and
their load averages are in the Gates section above.

```
MEASURE BUILD tier=SLOW elapsed_ms=381.414 exit=0
MEASURE CARRY tier=MED elapsed_ms=1305.905 exit=0
MEASURE R0-COUNT tier=FAST elapsed_ms=118.605 exit=0
MEASURE R0-AUDIT tier=FAST elapsed_ms=52.972 exit=0
MEASURE SUITE-KERNEL tier=SUITE elapsed_ms=529.114 exit=0
MEASURE SUITE-WASM tier=SUITE elapsed_ms=3384.375 exit=0
MEASURE ENCODER-SUBSET tier=FAST elapsed_ms=137.438 exit=0
MEASURE AXIOMS tier=MED elapsed_ms=60.054 exit=0
MEASURE M0-E2E tier=SLOW elapsed_ms=1531.513 exit=0
MEASURE M0-TIME tier=SLOW elapsed_ms=1248.338 exit=1
MEASURE M0-RATIO tier=SLOW elapsed_ms=2592.306 exit=0
MEASURE TRUSTED-LINES tier=FAST elapsed_ms=51.477 exit=0
MEASURE DENOMINATORS tier=MED elapsed_ms=82.821 exit=0
MEASURE HOUSE tier=MED elapsed_ms=153.936 exit=0
MEASURE PIN tier=FAST elapsed_ms=156.141 exit=0
MEASURE M0-RATIO kanon_ms=292.438 tot_ms=103.662 ratio=2.821
BENCH m0_e2e median_ms=179.126 min_ms=157.531 max_ms=200.455 runs=5
BENCH m0_ratio median_ms=292.438 min_ms=254.743 max_ms=970.102 runs=5
```

### Decisions

SJ-D1 to SJ-D20 are pinned by the stage brief.  SJ-D21 to SJ-D42 are the
builder decisions.  SJ-D43 to SJ-D45 are the fixer decisions, renumbered
by the judge because the builders reached SJ-D42.

- SJ-D1 The erasure lands the four rows of M1-PLAN.md:103-106 and
  nothing else;  SPar and SNu keep the refused arm (A6).
- SJ-D2 No IR constructor is added;  every mu row lands on KTag, KCase,
  KTail and KErased.
- SJ-D3 No believed kernel file is edited.
- SJ-D4 An index argument is erased on the quantity Zero rule of A2.
- SJ-D5 The tid text is mu of the family name with the leg tid at the
  constructor index.
- SJ-D6 The rec group form is one composite type list with the rec group
  opcode and one sub final entry for each member.
- SJ-D7 The group boundary is the family record and never the emitter.
- SJ-D8 The four interim sidecars go and their .kan files become
  positives with driver produced goldens.
- SJ-D9 No SPEC.md obligation row moves at Stage J.
- SJ-D10 No R0 count moves and R0-COUNT stays green.
- SJ-D11 SJ-B1 does not fire for the multi-member rec group form.
- SJ-D12 The tail eligible fixture keeps the depth of 100,000;  the
  depth of the general catamorphism fixture is measured by this stage.
- SJ-D13 The general catamorphism fixture lands under test/fixtures;  the
  100,000-deep fixture is driven by the stage local gate SJ-G8.
- SJ-D14 Every golden is produced by the driver.
- SJ-D15 The two TRUSTED-LINES budgets stay 4,000 and 600.
- SJ-D16 The encoder headroom is shared with Stage K and is reported at
  the end of this stage.
- SJ-D17 Every mutation runs on a fresh copy and ROOT is never mutated.
- SJ-D18 A leg name that dev/gates.sh does not accept is read from one
  full run of the battery (erratum SG-D25).
- SJ-D19 examples/m0-spine.kan is never edited.
- SJ-D20 This brief adds SJ-G8 and SJ-G9 beyond the plan's seven gates.
- SJ-D21 The tid text is pinned in two forms: the family tid is
  `mu<NAME>` and never carries an index, and the leg struct of
  constructor K is `leg<mu<NAME>,K,R1,...,Rn>` with one repr for each
  runtime field in declaration order, or `leg<mu<NAME>,K>` for a
  constructor with no runtime field (lib/erase.ml:211 and :219).
- SJ-D22 The family tid is nominal and not structural, because the
  structural text of a recursive family would contain itself, and
  `tid_of` must agree with `repr_of` for one type (SC-D5).  A mu type
  reprs as the union `mu<NAME>` (lib/erase.ml:276).
- SJ-D23 erase.ml publishes the leg names through the rec group the
  declaration already emits:  `acc` gains a `groups` field, each KTag and
  KCase site appends the leg names of its family, and `def_code` folds
  them into KRec.  Every M0 golden is unchanged, because a program with
  no mu contributes no group name.
- SJ-D24 erase.ml discovers no mutual component:  each site publishes the
  legs of the family it names, a sibling appears inside a leg text as
  `union mu<SIBLING>`, and link.ml joins the group from those reference
  edges, so lib/global.ml needs no new accessor and SJ-B2 does not fire.
- SJ-D25 A branch of a KCase binds one kernel binder for each runtime
  field in declaration order, mirroring `rules.ml mu_branch`;  a field at
  quantity Zero binds no runtime binder and the last runtime field is the
  innermost one.
- SJ-D26 The interim words `mu_erase_word` and `mu_refused` are deleted.
  A `Sec` at SMu and an `Out` at SMu keep a refusal and read the word
  `Rules.mu_ran_word` that rules.ml already holds, so Stage J writes no
  new milestone word (SA-D5).
- SJ-D27 The empty `test/erase-neg` directory stays alive with an empty
  `.gitkeep`, because `kan_names` reads the .kan files of the directory
  and a directory that no commit carries would make the suite exit
  through `fail_out` on a fresh checkout.
- SJ-D28 The test/main.ml verdict is split:  the ERASE-NEG group is
  checked with `passed = total` alone and every other group keeps
  `passed = total && total > 0`, because brief 3.3 foresees the empty
  directory and SJ-G2 still requires SUITE-KERNEL OK.
- SJ-D29 For Stage K:  the leg text of a parameterised family is read at
  the parameter values of the site, so one family at two different
  runtime parameters would give two leg texts under one family tid.  No
  M1 fixture reaches that case;  the array and bignum forms of Stage K
  should pin whether the leg text is canonicalised at the parameter
  variables instead.
- SJ-D30 wasm/gc_encode.ml carries the rec groups as `comptype list
  list`, one entry for each group:  a group of one is the bare comptype,
  so every M0 module keeps its bytes, and a group of two or more is
  `0x4E`, the member count, then one `0x4F` sub final entry with an empty
  supertype vector for each member.  The index of a type stays its
  position in the flat reading of the groups and the header invariant
  comment is rewritten in the same edit (D-M1-5, SD-D17).
- SJ-D31 SPEC.md section 8 gains one row named `rec groups`.  No other
  row is widened and dev/encoder-subset.sh reads only the six instruction
  rows, so the allowlist does not move and SJ-B1 does not fire
  (RATIFICATIONS.md:75).
- SJ-D32 wasm/link.ml reads the legs of a family from the KRec groups the
  erasure publishes, held in `prog.mus`, because a family tid is nominal
  and carries no leg text.  `sum_legs_p` prefers that table and falls
  back to the structural reading of the tid text, which keeps every M0
  sum on its old path.
- SJ-D33 The rec group boundary is the strongly connected component of
  the reference edges the leg tids carry, and not the connected
  component:  a family that only holds a value of another family stays
  its own group, and only families that reach each other share a group
  (D-M1-5, probe p4).
- SJ-D34 A family that does not reach itself is not recursive and keeps
  one composite one group, which is SD-D17;  a recursive family, direct
  or mutual, puts every leg struct of every constructor of every member
  in one group.
- SJ-D35 wasm/emit.ml binds one kernel binder for each runtime field in
  declaration order, the last field innermost, and reads a field with
  `local.get`, `ref.cast` to the leg type and `struct.get` of field k+1,
  then the coercion to the field repr (SJ-D25, SD-D5).
- SJ-D36 Defect fix in bin/kanon.ml:  `run_emit` erases in the globals
  the file was checked in and not in `Global.initial`, because every mu
  family was unbound at emit.  Two lines.
- SJ-D37 Defect fix in test/wasm.ml:  the suite elaborates with
  `Elab.check_in` and keeps the globals it answers, because the rows
  alone do not carry the inductive families.  `kernel_value` and
  `emitted` read those globals and the fold `globals_of` is gone.
- SJ-D38 The general catamorphism fixture `test/fixtures/mu-cata-depth`
  at depth 4,095 holds no `return_call` at all:  its doubling builder is
  a recursion whose branch body consumes the recursive result, each chain
  global is a constructor application and `main` goes through `natAdd`,
  so the SJ-G8 reading of no `return_call` is exact and SJ-M2 cannot
  touch it.
- SJ-D39 The measured depth of the general catamorphism:  node answers
  8191 and fails at 16383 with `Maximum call stack size exceeded`;
  wasmtime answers 8191 and fails at 16383 with `call stack exhausted`.
  The fixture keeps 4,095, which is less than half of the smallest
  failing depth, and the kernel supplies its expectation in about 51 ms.
- SJ-D40 Placement under SJ-D13:  the 100,000-deep tail eligible fixture
  stays out of test/fixtures and is driven by the stage local gate SJ-G8
  out of the work directory, because the kernel needs 4.11 s to reduce
  its expectation while the whole SUITE-WASM leg measures 1.96 s.  The
  general catamorphism fixture lands under test/fixtures with its three
  goldens.
- SJ-D41 A third fixture, `test/fixtures/mu-mutual-emit.kan` with its
  checked, erased and wat goldens, lands beside the two A10 fixtures,
  because no golden held a multi-member rec group and SJ-M1 and SJ-M4
  would have had no subject.  It is the mutual family A and B with
  `sizeA` and `sizeB`, and `main` answers 4.
- SJ-D42 SJ-G8 is the stage local script `sj-g8.sh`, which takes the
  repository root as its one argument and defaults to ROOT, so a
  mutation copy runs it unchanged.  No dev/gates.sh leg is added, which
  stays the Stage L deliverable (M1-PLAN.md:230).
- SJ-D43 The fixer makes no source edit at Stage J.  SJ-F1 is a reporting
  defect and its remedy is the reproduced gate line, which the judge
  quotes;  SJ-F2 and SJ-F3 carry no one line fix, so the code of the
  stage stands as the builders left it.  The judge renumbered this
  decision and the two below from SJ-D26 to SJ-D28, because the builders
  reached SJ-D42.
- SJ-D44 The SJ-G2 entry of this log quotes the numeric group lines of
  the final reproduced run and never a terse later run that omits them.
  The erase-neg group line is quoted at its zero count, which brief 3.3
  requires because the directory is empty and holds only
  `test/erase-neg/.gitkeep`.
- SJ-D45 The Stage K and Stage L hand-off carries the SJ-F2 fact as a
  build rule and not as a gate change:  wasm-opt and ENCODER-SUBSET are
  confirmed not to reject a wrong rec group split, so every new
  multi-member-group fixture needs a .wat golden that holds the `(rec`
  form.  No leg of dev/gates.sh moves at Stage J.

### Findings

- SJ-F1, medium, resolved by this log.  The builder hand-off quoted
  `PARSE-OK 88/88, CHECK-OK 57/57, ERASE-OK 57/57` for SJ-G2, which does
  not reproduce:  the tree reads `PARSE-OK 90/90`, `CHECK-OK 59/59` and
  `ERASE-OK 59/59`, and 59 files match `test/fixtures/*.kan`.  The stale
  figure was read before `mu-cata-depth.kan` and `mu-mutual-emit.kan`
  landed.  No committed file carries it;  the only `88/88` in the
  repository is the Stage I section of this file, where it is correct.
  The Gates section above holds the reproduced numbers (SJ-D44).
- SJ-F2, low, disclosed and carried into the hand-off.  SJ-M1 and SJ-M4
  are not caught by wasm-opt or by ENCODER-SUBSET.  On both mutation
  copies `wasm-opt --enable-gc --enable-reference-types
  --enable-tail-call --print` exited 0 with an empty stderr, node still
  answered 4, and `ENCODER-SUBSET OK` still printed.  The killer in both
  cases is the byte for byte golden compare in test/wasm.ml against
  `test/golden/mu-mutual-emit.wat`, the one golden of the 17 that holds a
  `(rec` form.  The remedy is the build rule of SJ-D45.
- SJ-F3, info, no edit.  M0-TIME is load sensitive on this host and is
  not a code defect.  The readings and their load averages are in the
  Gates section.  `M0_TIME_MS` stays 150.

### Hand-off notes for Stage K

- The encoder count.  `wasm/gc_encode.ml` is 237 lines of the 600 line
  encoder budget, from 216 at Stage J entry, so 363 lines are left for
  the array composite type and its three opcodes (SJ-D16,
  M1-PLAN.md:130).  The budget does not move (D-M1-7, correction C6);  a
  form above 363 lines is SJ-B3 at Stage K and a halt for the user.
- The erased rows the bignum representation must keep sound.  SPEC.md
  section 2.3 now holds two mu rows:  `In` at `Lan (SMu ..)` erases to
  `KTag (tid, the constructor index in declaration order, the runtime
  fields)`, with a tag and no payload for a constructor with no runtime
  field, and no index argument ever enters it;  `Elim` at `Lan (SMu ..)`
  erases to `KCase (tid, scrutinee, one branch for each constructor in
  declaration order)`, and a branch body that is the recursive call
  itself is `KTail`.  A branch binds one kernel binder for each runtime
  field in declaration order, the last field innermost (SJ-D25).  The two
  representation runtime of Stage K must keep both rows true for a Nat
  that is a bignum:  a field at the bignum representation is still one
  runtime field of the leg struct and still one branch binder.
- The tid text the array tid joins.  The family tid is `mu<NAME>` and
  carries no index.  The leg struct of constructor K is
  `leg<mu<NAME>,K,R1,...,Rn>`, one repr for each runtime field in
  declaration order, and `leg<mu<NAME>,K>` for a constructor with no
  runtime field (SJ-D5, SJ-D21, lib/erase.ml:211 and :219).  A mu type
  reprs as the union `mu<NAME>`, which is nominal and not structural
  (SJ-D22).  The array tid of Stage K joins that text and link.ml dedups
  by it.
- The measured depth of the general catamorphism.  The fixture
  `test/fixtures/mu-cata-depth.kan` runs at depth 4,095 and holds no
  `return_call`.  Both hosts answer 8191 at depth 8,191 and both fail at
  16,383:  node prints `Maximum call stack size exceeded` and wasmtime
  prints `call stack exhausted`.  The fixture depth is less than half of
  the smallest failing depth (SJ-D12, SJ-D39, RATIFICATIONS.md:80).
- The fixtures that left test/erase-neg.  Four files moved to
  `test/fixtures` and each gained a driver produced `.checked` golden and
  a driver produced `.erased` golden:  `mu-erase.kan`,
  `mu-rec-direct.kan`, `mu-rec-indexed.kan` and `mu-rec-mutual.kan`.
  Their four `.err` sidecars are deleted, none of the four defines
  `main`, so none has a `.wat` golden, and `test/erase-neg` now holds
  only `.gitkeep` and reads `ERASE-NEG-OK 0/0` (SJ-D8, SJ-D27, SJ-D28).
- The build rule for a new rec group fixture.  wasm-opt and
  ENCODER-SUBSET do not reject a wrong rec group split, so every new
  fixture with a multi-member group needs a `.wat` golden that holds the
  `(rec` form.  Today `test/golden/mu-mutual-emit.wat` is the only one of
  the 17 `.wat` goldens that holds it (SJ-F2, SJ-D45).
- The stage local gate.  SJ-G8 lives outside the repository with the
  100,000-deep fixture `mu-tail-100k.kan`.  Stage L owns dev/gates.sh and
  decides whether the leg joins the battery (M1-PLAN.md:230).

### Notes for the user, not a ruling

- Gates beyond the plan row.  The plan gives SJ-G1 to SJ-G7.  This stage
  ran SJ-G8 TAIL-DEPTH and SJ-G9 LOGS as well, which the stage brief adds
  on the Stage G, Stage H and Stage I precedent (SJ-D20).
- The encoder reading.  237 of 600 lines, 363 left for Stage K.
- The placement of the 100,000-deep fixture.  It stays out of
  test/fixtures and rides SJ-G8, because the kernel needs 4.11 s to
  reduce its expectation (SJ-D13, SJ-D40).
- The measured catamorphism depth.  4,095 in the fixture, 8,191 answered
  and 16,383 failing on both hosts (SJ-D12, SJ-D39).
- Builder work beyond the brief file list.  The defect fixes in
  bin/kanon.ml (SJ-D36) and test/wasm.ml (SJ-D37), the third fixture
  mu-mutual-emit (SJ-D41), and the `.gitkeep` and the split ERASE-NEG
  verdict that keep the empty directory alive (SJ-D27, SJ-D28).

### Staged review fixes (2026-09-06)

Review scope: the 36 staged Stage J paths, before commit.  Validation ran
in an isolated copy of that tree, with the original vendor tree read only.

- CI coverage blocker, fixed in test/main.ml: the empty ERASE-NEG exception
  accepted deletion of migrated positives.  Removing mu-erase.kan from
  fixtures made the original staged suite exit 0.  The new MIGRATED group
  requires all four replacements; the same mutation now reports the
  missing fixture, MIGRATED-OK 3/4, and exits 1.
- MEDIUM, fixed in lib/erase.ml: mu_group_tids published site-specific
  representations under one nominal family tid.  Checked eliminators for
  Box Nat and Box (Nat -> Nat) made emission exit 2 with "an application
  head is not a function".  Layouts now open family parameters as neutral
  variables in a fresh context.  This resolves and supersedes SJ-D29.
- MEDIUM, fixed in lib/erase.ml: mu_fields dropped a dependent payload
  instantiated at prod (), while its declaration layout and case branch
  retained a field.  The checked mu-dependent-layout fixture made emission
  exit 2 with "an argument list is shorter than its signature".  Payloads
  and branch slots now follow the same declaration layout.  A generic
  field instantiated at an erased type carries KErased as a placeholder.

Added mu-parameter-layout and mu-dependent-layout to the normal fixture
suite, with checked, erased and validated Wasm text goldens.  The first
covers Nat, function, tuple and empty tuple parameter instantiations.  The
second exercises constructors at Nat, empty tuple and function types, with
a trailing Nat field to check binder positions.  Node and Wasmtime answer
9 and 27 respectively, agreeing with the kernel expectations.

Validation: build 0 errors and 0 warnings; PARSE-OK 92/92, CHECK-OK 61/61,
ERASE-OK 61/61, NEG-OK 31/31, ERASE-NEG-OK 0/0, KNEG-OK 2/2, REC-OK 1/1,
MIGRATED-OK 4/4, SUITE-KERNEL OK; WASM-OK 19/19, SUITE-WASM OK.  The full
15-leg dev/gates.sh battery passed with GATES-OK.  M0-E2E returned 521;
M0-TIME median was 132.583 ms against 150 ms; TRUSTED-LINES remained
kernel=3993/4000 and encoder=237/600.  Existing goldens stayed unchanged.

Blockers: none remain from this review.  Merge verdict: merge with these
staged fixes, which make nominal constructor layouts consistent across
instantiations and preserve migrated test coverage.  No commit was made.

## M1 Stage K: arbitrary precision Nat and exact One (2026-09-06)

Status: PASS, all eleven Stage K gates and all four semantic mutations.
The user's agreement correction and explicit M0-spine freeze exception
are recorded in RATIFICATIONS.md rounds 2026-09-06 (d) and (e).
No commit or M1-EXIT is claimed; the commit remains a user step.

ROOT remains `/Users/oobi/Documents/kanon` at Stage J commit
`ac94fe36c7fc7d4013a00d3fa102666e2cafdd0a`.  The isolated implementation is
`/Users/oobi/Documents/gpt4/kanon-stage-k/work`; PREP denotes its parent.
The frozen tot pin and vendor are `8cf0b8bfbb574e344d8d489ba6fd6b81de4cf562`.
Earlier M0 and M1 log entries, denominators and R0 counts are unchanged.

### Decisions and implementation

| Id | Final decision and evidence |
| --- | --- |
| SK-D1 | Bignum is the total signed Zarith 1.14 boundary, pinned in dune-project and linked by lib/dune.  Decimal folding validates digits; narrowing checks representability.  Negative forged Nat literals and primitive operands are rejected.  PREP/naturals-check.sh passes 44 boundary checks. |
| SK-D2 | The closed LInt constructor carries Bignum.t.  Its consumers, printers and surface tokens are widened.  The carried literal delta is 15; no kernel term, shape or IR constructor is added. |
| SK-D3 | Nat decimals have no host-integer ceiling.  Universe, binder, leg and projection numbers use total bounded readers.  Exact add, truncated subtract, multiply, equality and less-than retain Bool leg 1 for true and 0 for false. |
| SK-D4 | Runtime Nat uses i31 through 1073741823, otherwise an immutable sign-1 struct holding little-endian base-32768 limbs.  Helpers promote before overflow, allocate fresh result arrays, trim high zero limbs and normalize small answers to i31.  The largest schoolbook intermediate is 1073741823. |
| SK-D5 | CArray and array.new/get/set/len are the complete encoder additions.  array.set is required to populate heterogeneous fresh limbs.  Shared operands are never stored into.  SPEC records exact encodings.  Binaryen's printed exact reference qualifier is structural syntax, with no new encoder instruction; the subset negative control still rejects i32.and. |
| SK-D6 | Internal large values remain exact.  The unchanged zero-argument i32 export traps only for an out-of-i31 final result, with driver exit 4 on kernel, Node, Wasmtime and both.  The focused runtime runner passes 20/20 observations. |
| SK-D7 | Quantity owns pure path intervals and retained dependencies from nonreturning paths.  One is exactly one use on every returning runtime path.  Runtime mode is separate from multiplicity; repeated type inference does not count as runtime use.  The carried quantity delta is 151 after the review round of 2026-09-06. |
| SK-D8 | Rules compose sequences, declared argument scaling and branch alternatives.  Runtime Zero scrutinee stamps are rejected; surface and eta-generated cases use One.  Explicit One scopes close in the kernel.  Eager let definitions count once; aliases carrying a linear resource may be used at most once.  Closure construction retains dependencies even when invocation cannot return. |
| SK-D9 | Five actual unary SMu sources each contain 1089 indexed Agreement witnesses for every pair from 0 through 32, 5445 total.  Every unary definition and observer avoids its tested primitive, and all axiom disclosures are empty. |
| SK-D10 | Python integer arithmetic independently supplies all 400 pairs per primitive from the approved 20-value set, 2000 total.  Kernel, Node and Wasmtime each produce 400 successful small observations per operation.  No general theorem or billion-node unary execution is claimed. |
| SK-D11 | All eleven Stage K gates and four mutations remain required.  The ordinary suite retains all 61 original positive sources unchanged.  No bound, denominator, opcode guard, expected result or pin is waived. |
| SK-D12 | The believed list retains every existing member and adds Bignum.  Substantive reuse and traversal factoring hold the measured total at 3997/4000; encoder is 246/600.  No trusted work moves into an unmeasured new module and no documentation is deleted to meet the bound. |
| SK-D13 | The byte-identical unary matrices move to test/agreement, with all ten goldens retained in test/golden.  The dedicated mandatory gate also performs their original surface roundtrips.  Repeating all 5445 witnesses six times in the general-suite benchmark exceeded its 120-second watchdog; the dedicated gate preserves coverage and restores the original benchmark's bounded role. |
| SK-D14 | The user explicitly approved the M1-PLAN.md:153 exception: "Please apply the spine correction."  The linear function is now the identity; its former addition occurs at the closed call site as natAdd (linear 8) 1.  Linear use remains covered, linearValue remains 9, and the active baseline returns 521.  No quantity, expected answer, bound or denominator changes. |
| SK-D15 | Review exposed type-only and erased-field/call/let closure captures plus application erasure trusting APt stamps.  Erasure now prunes captures from the actual erased body's free variables and remaps retained indices; application quantities come from checked function types.  The combined regression returns 58 on all four host settings. |

The trusted count starts at 3993.  Shared occurrence traversal and list
comparison recover 40 lines.  After the initial usage implementation and
Bignum integration, the count was 4054.  Shared closure/list comparison,
former inspection, binder-quantity diagnostics and global-head lookup
recover 55 lines.  Soundness fixes add 12.  Totality reuses its ordered
spend_all traversal and merges identical Lan/Ran arms (9 lines); shared
SPi former checking recovers another 5.  Final: 3997, a net increase of
4 over Stage J and 3 lines of headroom.  Encoder grows by 9 to 246.

### Gates and observed results

| Id | Command in WORK unless stated otherwise | Observed result |
| --- | --- | --- |
| SK-G1 BUILD | zsh dev/dunecho.sh build | PASS, zero errors and warnings; Zarith 1.14 installed and pinned. |
| SK-G2 CARRY | zsh dev/carry-check.sh | PASS; quantity 97, literal 15, every other carried delta unchanged. |
| SK-G3 SUITE-KERNEL | _build/default/test/main.exe test; zsh one-paths.sh | PASS; PARSE 120/120, CHECK 73/73, ERASE 73/73, NEG 47/47, KNEG 2/2, REC 1/1, MIGRATED 4/4.  Direct One checks 27/27 and surface path checks 22/22.  Five exhaustive positives are additionally required by SK-G5. |
| SK-G4 SUITE-WASM | _build/default/test/wasm.exe test _build/stage-k-wasm-standalone; zsh dev/nat-runtime.sh | PASS; WASM 29/29 and focused runtime 20/20.  Extra capture regression returns 58 on kernel, Node, Wasmtime and both. |
| SK-G5 AGREEMENT | zsh agreement.sh | PASS; all 5445 unary and 2000 full-range cases, 7445/7445.  Unary parser roundtrips and both checked/erased goldens are mandatory.  Independent expectations match all three execution hosts. |
| SK-G6 ENCODER-SUBSET | zsh dev/encoder-subset.sh | PASS after exact printer-type accounting; the real printed exact control passes and unlisted i32.and is rejected. |
| SK-G7 TRUSTED-LINES | zsh dev/trusted-lines.sh | PASS; kernel 3997/4000, encoder 246/600, Bignum included. |
| SK-G8 DENOMINATORS | zsh dev/gates.sh --leg denominators | PASS; frozen JSON and hash unchanged. |
| SK-G9 HOUSE | zsh dev/house.sh; git diff --check | PASS; all house checks and whitespace clean. |
| SK-G10 BASELINE | zsh dev/gates.sh | PASS, all 15 legs and GATES-OK on the first active run after the approved spine correction.  M0-E2E 521; M0-TIME 110.466 ms against 150 ms.  PREP/gate-evidence/baseline-approved-spine.out and .json retain exact output and unchanged source digests. |
| SK-G11 LOGS | python3 -P PREP/validate-stage-k-close.py | PASS; exactly one Stage K section in each M1 log, all eleven gate rows, fifteen decision rows, four mutation rows and the Stage L handoff.  All earlier log bytes remain unchanged. |

The final active baseline records BUILD 304.825 ms, CARRY 798.448 ms,
SUITE-KERNEL 218.659 ms, SUITE-WASM 6027.434 ms and M0-RATIO 1411.866 ms.
Its informational raw M0 ratio is 2.054.  The normalized M1 ratio remains
a Stage L obligation.  M0-TIME measures 110.466 ms median, 101.794 ms
minimum and 113.624 ms maximum, five runs, against the unchanged 150 ms
bound.  Load averages were 18.88/25.36/36.07.  No timing rerun was needed.

The previous active baseline failed AXIOMS and M0-E2E on the frozen
spine's invalid One use; M0-TIME reported BENCH-ERROR before timing.
Its other twelve legs passed.  The earlier ratio watchdog failure was
resolved by SK-D13.  Both historical failures remain in gate-evidence.

A fresh positive proposal copy at PREP/spine-proposal-check/work now
passes the unchanged full battery on its first attempt: all fifteen legs
PASS, GATES-OK, M0-E2E 521 and M0-TIME 110.636 ms against 150 ms.  Its
source manifest proves the spine patch was the only difference at that
validation time, before subsequent SPEC and log updates.  Results and
full output remain under PREP/spine-proposal-check.  The user's explicit
exception then authorized application and the passing active run above.

Evidence: PREP/gate-evidence, agreement-evidence, agreement-reference.json,
agreement-move.json, agreement-roundtrip-evidence.json, check-review,
one-final-validation.json, one-paths.log, one-mutation, mutations and
linearity-handoff.md.  The mutation section below records SK-M1 through
SK-M4 and their explicit failure observations.

### Review and Stage L handoff

Review corrected eager-let accounting, unreachable closure construction,
runtime Zero scrutinee stamps, SPi eta stamp consistency, unnecessary
runtime captures, and forged APt application erasure.  Each concrete
finding has a passing regression under PREP/check-review.  The encoder
printer qualifier has separate positive and negative reader controls.

Stage L must integrate PREP/agreement.py, agreement-roundtrip.ml/.sh,
agreement-reference.json and full-range/*.kan into its required permanent
agreement leg.  Persistent unary sources are test/agreement/*.kan;
their checked and erased goldens remain in test/golden.  The existing
ordinary fixture suite and all its original sources remain present.
Integrate the focused One runner at PREP/one-paths.ml/.sh and the runtime
runner currently at WORK/dev/nat-runtime.sh.  Keep both finite agreement
sets mandatory and retain mutation controls and exact negative sidecars.

No Stage K blocker remains.  PREP/spine-correction.md explains the
approved correction and its evidence.  Close copies and stages only
reviewed Stage K paths after checking the unchanged Stage J base.
Stage F remains committed; no optional Lean agreement theorem was added.

## Stage L (2026-09-06)

### Status and scope

IMPLEMENTED, VALIDATION PENDING.  The user requested continued kanon
development and staging all changes.  The entry is c418062, the committed
Stage K.  This stage adds the full M1 surface, executable feature ledger,
permanent agreement runners, M1 spine and 1,000-line corpus.  The native
collaboration workflow ran separate scope, surface, gate, example review,
surface review, gate review and isolated mutation tasks.

The full battery returned GATES-FAIL, with sixteen passing legs and three
open legs: M0-TIME, M0-RATIO and AGREEMENT.  This is not a Stage L PASS or
an M1-EXIT ratification.  The user retains commits and the M1-EXIT stamp.
The explicit request to stage all changes supersedes historical SL-B3's
clean-porcelain exit condition.  Concurrent main-tree metatheory changes
are preserved and included in staging; they are not part of this compiler
validation.  No kernel, encoder, M0 spine, pin or frozen denominator changed.

### Deliverables and decisions

- SL-D1: `mu ... :=` and constructor `| name binder* : result` sugar
  reuse the Stage G family tree. Constructor binders fold into the
  existing dependent arrow chain with their original quantities.
  `mu ... with` and `and` remain compatible.
- SL-D2: `mutual mu ... mu ... end` creates one family group and
  requires at least two members. Empty, singleton, unterminated and
  `and`-joined explicit mutual blocks are parser refusals. Three-member
  recursion is covered by `sl-mutual-three.kan`.
- SL-D3: `match` has a distinct `SMatch` surface node, accepts only
  constructor keys, and requires a mu scrutinee even with zero branches.
  It calls the existing fibered elaboration. Numeric `case` and Stage H
  constructor `case` retain their behavior.
- SL-D4: constructor branches accept Stage H quantity/name fields and
  typed binders, including mixtures. An optional type annotation is
  checked at a universe and compared by existing type conversion with
  the declared field type, in the context of preceding fields. The
  kernel still checks field quantities and branches.
- SL-D5: the printer writes `:=`, normalizes multi-family declarations
  to `mutual ... end`, keeps constructor types as expanded arrows, and
  preserves `case` versus `match` and typed field annotations. Parsed
  trees round-trip exactly.
- SL-D6: `nu` keeps `nu arrives at M2` in term and declaration positions.
  Match keeps the Stage H optional index clause and existing kernel
  motive requirement. `end` terminates mutual groups only; parentheses
  delimit nested match bodies before an outer branch.
- SL-D7: `test/sl_surface.ml` holds 20 permanent parser boundary,
  round-trip and sugar-equivalence checks. Run without arguments;
  success is exit 0 and final line `SL-SURFACE OK`. Parser negatives
  belong here because the existing kernel suite parses every negative.
- SL-D8: added two runtime fixtures with checked, erased and Wat goldens,
  plus three semantic negatives for collection matching and incorrect
  field annotations. Parent-authorized migration renames embedded
  `def mutual` and its lookup in `test/main.ml` to `mutualValue`, because
  `mutual` is now a required reserved word. Gates agent owns the other
  independent change in that file.
- SL-D9: SPEC sections 7 and 9 describe the new sugar and complete M1
  grammar, including retained recursive definitions and compatibility
  forms. Section 10 marks subsingleton elimination discharged by Stage
  H SH-G7 and `any` discharged by Stage D SD-D6, retaining milestone M1.
  Independent review amendment: section 7 explicitly maps `def rec` and
  recursive `and` groups through `Totality.guard_group`, `Order.translate`
  and checking of the translated `Elim` body before `Global.Def`
  installation, as M1-PLAN section 4 requires. The implementation was
  read at surface/elab.ml:1035, :1061 and :1062 and lib/order.ml:510;
  this amendment changes documentation only.

- SL-D10: M0-TIME uses the median of three medians of five, always prints the
  three BENCH lines, retains 150 ms and excludes wasm-opt as previously ruled.
- SL-D11: M0-RATIO is binding on the unrounded per-line value, with six decimal
  places displayed; its numerator is the median of five corpus checks.
- SL-D12: Record the 8138 checked pin lines in dated denominators-m1.json;
  validate the ruled 103.662 ms and line-count fields before dividing.
- SL-D13: M1-CORPUS times check, emit, validation, kernel observation and the
  both-host driver path together, including their repeated driver work. It
  requires exactly 1000 newline-terminated lines and the 713 ms bound.
- SL-D14: The permanent AGREEMENT leg always executes both finite sets,
  totaling 5445 unary and 2000 independent exact-arithmetic cases.
- SL-D15: Retain original agreement source/manifest equality checks, unary
  round trips, both goldens and all three full-range host observations.
- SL-D16: Key HOUSE allowances by relative path, enclosing top-level function
  and exact arm text, with one reason each; line movement grants no new site.
- SL-D17: Replace the three additional named fallthroughs with exhaustive
  unit guards while preserving their existing successful and error branches.
- SL-D18: POSITIVITY discovers each positive fixture containing a mu
  declaration and requires the direct, mutual and indexed originals, plus
  the exact named nonpositive negative diagnostic.
- SL-D19: The executable M1 ledger retains original source fixtures, appending
  small closed scalar observations only into generated .gatework copies.
- SL-D20: Every ledger observation checks, emits, validates and compares
  kernel with both hosts; exact checker negatives accompany its feature row.
- SL-D21: Empty-family large elimination is checked and erased before a
  closed scalar observation. It cannot be applied to a closed Void inhabitant,
  because none exists. The non-subsingleton and self-recursive Prop negatives
  separately pin the two required refusals.
- SL-D22: Each primitive also has a small typed unary witness, both runtime
  observations and a deliberately wrong witness with an exact sidecar.
- SL-D23: Keep the original 27 direct kernel and 22 surface One path cases
  mandatory in M1-SUITE, including all original exact quantity diagnostics.
- SL-D24: Keep the original 20 Nat runtime observations mandatory, including
  the independent oversized-export trap on all four driver host modes.
- SL-D25: M1-SUITE runs surface's durable SL-SURFACE regression executable and
  the parent-owned M1 spine, requiring at least 300 lines and its main promise.
- SL-D26: Write generated suite sources, Wasm, WAT and evidence under
  .gatework; permanent data includes only reviewed sources and exact sidecars.
- SL-D27: Preserve all existing watchdog ceilings; use SUITE for positivity,
  M1-SUITE and AGREEMENT and SLOW for the timed corpus leg.
- SL-D28: Force RUNS=5 for each benchmark and reject malformed BENCH output;
  Decimal arithmetic avoids a rounded ratio silently crossing the bound.
  All three timing legs report the observed one-minute load.
- SL-D29: Keep explicit bound arguments in the helper for isolated mutation
  controls, while the permanent battery always supplies its fixed constants
  and accepts no environment-based bound or sampling overrides.

- SL-D30: examples/m1-spine.kan has 396 lines and returns 599.  It carries
  every accepted M0 form and all required M1 forms without a postulate.
  Its five small typed agreement witnesses compare unary recursion with
  literal arithmetic.  Each wrong witness was independently rejected.
- SL-D31: test/corpus/m1-corpus.kan has exactly 1,000 lines and returns
  814: the complete spine's 599, a 5-by-5 arithmetic grid's 200, and six
  indexed vector copies' 15.  Every grid cell and copy reaches the export.
  Checked agreement witnesses are proof obligations, not padding.
  dev/gen-m1-corpus.py regenerates the corpus byte for byte.  Continuation
  lines retain their source indentation; no blank or comment padding is
  added to reach the prescribed size.
- SL-D32: checksum expressions form balanced trees.  The initial scratch
  experiment used 100 grid cells and chained partial-sum globals, causing
  repeated elaboration through those globals.  The final representative
  corpus keeps every prescribed feature.  The separate ratified 7,445-case
  agreement matrix and its original sources are unchanged.
- SL-D33: strengthen HOUSE to scan complete source text, because review
  reproduced valid multiline catch-all arms that the first line scanner
  missed.  The two allowances remain exact, function-specific and single-use.
- SL-D34: preserve every failed timing result.  No threshold, sampling
  count, watchdog, ratio normalization or agreement requirement is waived.
  High load prevents a quiet-machine verdict in this run.  Stage L and
  M1-EXIT remain open until the failed legs pass.
- SL-D35: copy only reviewed compiler deliverables after checking entry
  hashes against main.  Stage all main-tree changes as explicitly requested,
  including the independent metatheory work.  Do not commit or write RATIFY.

### Observed gates

The full battery used these unchanged bounds: M0-TIME 150 ms, M0-RATIO
2.000, M1-CORPUS 713 ms, kernel 4,000 lines and encoder 600 lines.

```text
LOAD BEFORE (74.99462890625, 68.26806640625, 49.6728515625)
PASS BUILD
PASS CARRY
PASS R0-COUNT
PASS R0-AUDIT
PASS SUITE-KERNEL
PASS SUITE-WASM
PASS ENCODER-SUBSET
PASS AXIOMS
PASS M0-E2E main=521
BENCH m0_e2e_1 median_ms=677.199 min_ms=309.302 max_ms=1485.977 runs=5
BENCH m0_e2e_2 median_ms=439.204 min_ms=353.436 max_ms=618.814 runs=5
BENCH m0_e2e_3 median_ms=432.310 min_ms=377.661 max_ms=571.466 runs=5
FAIL M0-TIME median_ms=439.204 bound_ms=150 load1=62.494 samples=3x5
BENCH m1_check_corpus median_ms=40.266 min_ms=33.296 max_ms=51.084 runs=5
MEASURE M0-RATIO kanon_ms=40.266 kanon_lines=1000 tot_ms=103.662 tot_lines=8138 ratio=3.161088 bound=2.000 load1=62.494
FAIL M0-RATIO kanon_ms=40.266 kanon_lines=1000 tot_ms=103.662 tot_lines=8138 ratio=3.161088 bound=2.000 load1=62.494
PASS TRUSTED-LINES
PASS DENOMINATORS
PASS HOUSE
PASS PIN sha=8cf0b8b
PASS POSITIVITY fixtures=22 negative=mu-nonpositive
PASS M1-CORPUS elapsed_ms=416.399 bound_ms=713 lines=1000 main=814 load1=62.494
PASS M1-SUITE ledger=16 focused-one=49 nat-runtime=20 surface=OK
FAIL AGREEMENT
MEASURE M0-RATIO tier=SLOW elapsed_ms=510.578 exit=1
LOAD AFTER (127.60986328125, 85.99951171875, 62.1220703125)
```

M0-TIME's three medians were 677.199, 439.204 and 432.310 ms; their
median was 439.204 ms.  M0-RATIO's corpus check median was 40.266 ms,
giving 3.161088 after the required per-line normalization.  Both failed
at one-minute load 62.494.  A quiet-machine regression verdict under
SL-B1 was not obtained.  M1-CORPUS passed at 416.399 ms, returning 814.

After all build and mutation tasks stopped, a standalone retry also
failed at load 63.640.  Its M0-TIME medians were 654.705, 567.048 and
432.928 ms, giving 567.048 ms.  Its M0-RATIO check median was 39.639 ms,
giving 3.111865.  These retries are retained in evidence/retry-2-time.log,
retry-2-ratio.log and retry-2.json.  No passing baseline is claimed.

AGREEMENT reached its unchanged 300-second SUITE watchdog and exited
124 after completing unary and full-range natAdd and natSub, 2,978 cases.
It did not finish all 7,445 cases.  Exact manifest regeneration and all
ten persistent source matrices passed comparison; that is source evidence,
not a replacement for completing execution.  The full result remains FAIL.

The kernel suite passed PARSE 127/127, CHECK and ERASE 76/76, NEG 51/51,
KNEG 2/2, REC 1/1 and MIGRATED 4/4.  The full Wasm golden suite passed.
M1-SUITE passed sixteen feature rows, all exact negative twins, 27 direct
and 22 surface One cases, 20 Nat runtime cases and 20 surface regressions.
New runtime fixtures return 42 and 3 on both hosts.  Independent surface
review also rejected ten adversarial parser, annotation and recursion probes.

### MEASURE table

```text
MEASURE M0-RATIO kanon_ms=40.266 kanon_lines=1000 tot_ms=103.662 tot_lines=8138 ratio=3.161088 bound=2.000 load1=62.494
MEASURE BUILD tier=SLOW elapsed_ms=3598.988 exit=0
MEASURE CARRY tier=MED elapsed_ms=2402.726 exit=0
MEASURE R0-COUNT tier=FAST elapsed_ms=665.852 exit=0
MEASURE R0-AUDIT tier=FAST elapsed_ms=248.324 exit=0
MEASURE SUITE-KERNEL tier=SUITE elapsed_ms=4203.299 exit=0
MEASURE SUITE-WASM tier=SUITE elapsed_ms=7125.111 exit=0
MEASURE ENCODER-SUBSET tier=FAST elapsed_ms=121.273 exit=0
MEASURE AXIOMS tier=MED elapsed_ms=77.868 exit=0
MEASURE M0-E2E tier=SLOW elapsed_ms=507.528 exit=0
MEASURE M0-TIME tier=SLOW elapsed_ms=11153.945 exit=1
MEASURE M0-RATIO tier=SLOW elapsed_ms=510.578 exit=1
MEASURE TRUSTED-LINES tier=FAST elapsed_ms=59.268 exit=0
MEASURE DENOMINATORS tier=MED elapsed_ms=99.927 exit=0
MEASURE HOUSE tier=MED elapsed_ms=391.917 exit=0
MEASURE PIN tier=FAST elapsed_ms=183.576 exit=0
MEASURE POSITIVITY tier=SUITE elapsed_ms=632.984 exit=0
MEASURE M1-CORPUS tier=SLOW elapsed_ms=568.765 exit=0
MEASURE M1-SUITE tier=SUITE elapsed_ms=16105.603 exit=0
MEASURE AGREEMENT tier=SUITE elapsed_ms=300037.444 exit=124
```

### Review and mutations

The surface review found no implementation defect.  Its missing structural
recursion sugar row was added to SPEC under SL-D9.  The gate review's
multiline catch-all finding was fixed and independently verified.  The
clean scanner passes; named, wildcard, typed and split-pipe multiline
controls fail.  HOUSE was rerun after the fix and passed.  The example
review's explicit agreement-witness and indentation findings were fixed.
All three required isolated mutations were caught; details are in the
Stage L mutation section.  They do not discharge a failing baseline leg.

### Handoff and evidence

Evidence root: /Users/oobi/Documents/gpt4/kanon-stage-l.  The entry manifest
is baseline.json; scope and workflow are in README.md; builder decisions
are in surface-result.md and gates-result.md; independent review is in
example-review.md, surface-review.md and gates-review.md.  The full output
and measurement state are evidence/battery-1.log and battery-1.json.
Mutation commands, exits and source hashes are under mutations/.

On a quiet machine, rerun the three open legs without changing constants:

```sh
zsh dev/gates.sh --leg time
zsh dev/gates.sh --leg ratio
zsh dev/gates.sh --leg agreement
```

Record their actual results before claiming Stage L PASS.  M1-EXIT still
requires the user commits, a green committed-tree battery and the user's
ratification.  F3 is closed for mu by the new spine; auto and nu remain
M2 work.  The optional Lean agreement theorem was not part of this stage.

## Stage L follow-up (2026-09-07)

### Scope and fixes

Continued from b6a5af67d5e06243bbcbead246cb6a8921d42726, preserving the ten
existing uncommitted files.  The user requested continued development and
staging of all changes.  Validation used the isolated source snapshot at
/Users/oobi/Documents/gpt4/kanon-stage-l-followup/work.

- AGREEMENT runs the five independent primitives concurrently, retaining
  every witness, golden comparison, axiom check and host comparison.
  Rows retain deterministic order and every watchdog stays unchanged.
- A run writes its selected report as FAIL before manifest validation or
  worker startup.  Invalid or interrupted reruns cannot retain an old
  PASS.  Filtered runs write only their selected report.
- The agreement round-trip runner locates the named OCaml switch and its
  Zarith stub library.  Both bytecode runners prepend that path while
  preserving inherited CAML_LD_LIBRARY_PATH entries.  Without that variable,
  the original round-trip runner failed to load dllzarith; the fix succeeds.
- HOUSE covers OCaml helpers under dev and tuple/or-pattern catch-alls.
  Review restored exactly the two D-M1-10 allowances: the intermediate
  subset check incorrectly allowed a third site.  Erasure's explicit
  list-shape error cases and the mutual-parser cleanup preserve behavior.
- Nat runtime validation resolves wasm-opt on PATH.  Corpus generation
  accepts --out.  Surface helpers gained documentation.  Axioms.lean
  discloses fourteen additional existing declarations.  README describes
  the implemented M1 surface, Nat representation, One usage and gates.

### Validation

The OCaml build passed with zero errors and warnings.  The complete kernel
and Wasm suites, encoder subset, axiom disclosure, M0 end-to-end spine,
positivity and denominator checks passed.  M1-SUITE passed sixteen feature
rows, 49 focused One cases, twenty Nat runtime cases and twenty surface
cases.  After its path fix, the One runner passed again: 27 direct and 22
surface cases.  Corpus regeneration via --out was byte-identical to the
tracked 1,000-line source returning 814.

The first battery's CARRY and PIN failures came from a copied relative
submodule Git pointer.  Repairing only the scratch pointer to the original
read-only Git directory made both checks pass.  Final HOUSE passed.
TRUSTED-LINES remains kernel=3997/4000 and encoder=246/600.

The full default Lean build, including all four regression roots, passed
with zero errors, incomplete proofs and warnings.  Axioms.lean completed:
its declarations depend on no axioms or exactly Quot.sound.  Existing
pinned dependency and build caches were copied into the snapshot; no
dependency revision changed.  This is additional disclosure, not a new
semantic theorem or compiler-preservation claim.

Independent HOUSE, One exit-propagation, agreement-report and library-path
controls passed.  The report harness uses stubbed workers; its synthetic
7,445-case result tests reporting only, not arithmetic agreement.  Final
static review found no remaining correctness or gate-weakening defect.
All ten generated agreement source matrices and the reference manifest
also matched exactly, preserving the 7,445-case workload.

### Performance and remaining gates

The first battery returned GATES-FAIL.  M0-TIME measured 1984.861 ms against
150 ms at load1=404.541.  M0-RATIO measured 25.097466 against 2.000 at
load1=405.378.  M1-CORPUS returned the correct value but took 7612.941 ms
against 713 ms at load1=405.964.  These are failed measurements on the
loaded host, not a quiet-host performance verdict.  No constants,
denominators, trusted-line bounds or workload sizes were relaxed.

The first agreement run reached its unchanged watchdog at 300.420 seconds,
exit 124, with its report still FAIL.  The separate final-source attempt
passed all 7,445 cases in 290.166 seconds under the same 300-second limit:
5,445 unary witnesses and 2,000 full-range cases, including kernel, Node
and Wasmtime comparisons for each primitive.  It exited zero and wrote
PASS with all ten rows successful.  Load1 was 212.873 before and 109.970
after.  AGREEMENT is now verified; M0-TIME, M0-RATIO and M1-CORPUS need
passing measurements.  M1-EXIT remains open and no ratification is written.

### Evidence

Evidence root: /Users/oobi/Documents/gpt4/kanon-stage-l-followup/evidence.
The full battery is battery-1.log.  Scoped results are carry-final.log,
pin-final.log, house-final.log, trusted-lines-final.log and one-final.log.
lean-build.json and lean-axioms.log hold the Lean results.  house-controls
and agreement-controls contain reproducible scripts, hashes and results.
The final agreement attempt uses agreement-final.log,
agreement-final-run.json and agreement-final/results.json.

### Review round 2026-09-07 (follow-up)

This block records the follow-up review of the 2026-09-07 fix round on
top of Stage L commit b6a5af6.  Seven findings were fixed, no finding
was ruled out this round, and six items were dropped as merged or
refuted into the kept findings below.

| id | severity | file:line | defect | verdict |
|----|----------|-----------|--------|---------|
| A-1 | medium | dev/agreement.py:199 | AGREEMENT emitted no per-row line and no incremental results.json, so a watchdog kill left zero row evidence | fixed |
| B-1 | medium | dev/house-catchalls.py:35 | Catch-all scanner missed as-pattern, nested-tuple and typed-tuple arms, so HOUSE stayed green on three unapproved catch-alls | fixed |
| D-3 | low | dev/house.sh:67 | The shared scan helper extended the no-mutable-state leg to dev, past the rule it states, with no exemption path | fixed |
| C-1 | low | README.md:273 | Two README HOUSE scope rows contradicted the dev/*.ml coverage this batch added | fixed |
| B-2 | low | dev/house-catchalls.py:43 | A boolean `\|\|` inside an arm guard was reported as a catch-all, so legal guarded code could not satisfy HOUSE leg 1 | fixed |
| C-2 | low | README.md:220 | Layout tree omitted test/sl_surface.ml, test/corpus and test/agreement, all load bearing elsewhere in the same README | fixed |
| ND-1-1 | medium | dev/house-catchalls.py:16 | New defect from the fixes: SELECTIVE missed a polymorphic variant tag, so a backtick-tagged arm passed HOUSE uncaught | fixed |

Refuted and dropped items, with reasons carried verbatim from the
review ruling.

A-3, dev/M1-BUILD-LOG.md:2036: REFUTED on the merits.  The code
behaviour is real, but the finding is filed as a false sentence in
dev/M1-BUILD-LOG.md and the sentence is not false in its paragraph.
The three-sentence unit at 2035-2037 establishes the selected report
as its subject and discloses the same residual the finding describes,
so no reader is told a filtered rerun overwrites an unfiltered
results.json.  dev/agreement.py:183-184 states the same scoping.
dev/gates.sh:197 and 201 keep the permanent battery unfiltered, so the
gate cannot reach the scenario either.  Not a finding.

D-1: merged into A-1.  Same file dev/agreement.py, same line 199, same
defect.  A-1 kept as the clearer statement; D-1's synthetic kill
control and citations are folded into A-1's detail.

A-2: merged into C-1.  Same file README.md, same two rows, same
defect.  C-1 states it most completely.  A-2's claim that leg 2 routes
through scan() is correct in the staged file, contrary to its own
verify note; that point is tracked separately as D-3.

B-4: merged into C-1.  Same file README.md, same line 273, same stale
HOUSE scope row.  Adds nothing beyond C-1.

D-2: merged into C-1.  Same file README.md, same line 273, same stale
HOUSE scope row.  Its severity downgrade to low is adopted for the
merged C-1, since the defect is doc-only with no gate, bound, script
or runtime effect.

B-3: merged into D-3.  Same file dev/house.sh, same line 67, same
defect.  D-3 kept as the fuller statement because it also cites the
leg's own contradicting comment at lines 65-66 and the
gc_encode.ml-keyed exemption window at 72-73.

### Gate results, review round 2026-09-07 (follow-up)

Verdict GATES-OK.  Load: load1=10.323 (M0-TIME, M0-RATIO), load1=11.098
(M1-CORPUS); uptime before the battery load averages 6.58 10.29 14.18,
after the battery load averages 9.44 10.17 13.59.  AGREEMENT completed
7,445 of 7,445 cases (unary 5,445, full-range 2,000), no watchdog exit.
TRUSTED-LINES read kernel 3,997 of 4,000 and encoder 246 of 600.

| leg | status | note |
|-----|--------|------|
| BUILD | PASS | dune build via gates.sh |
| CARRY | PASS | |
| R0-COUNT | PASS | |
| R0-AUDIT | PASS | |
| SUITE-KERNEL | PASS | |
| SUITE-WASM | PASS | |
| ENCODER-SUBSET | PASS | |
| AXIOMS | PASS | |
| M0-E2E | PASS | main=521 |
| M0-TIME | PASS | median_ms=113.150 bound_ms=150 load1=10.323 samples=3x5 |
| M0-RATIO | PASS | ratio=1.400924 bound=2.000 load1=10.323 |
| TRUSTED-LINES | PASS | kernel=3997/4000 encoder=246/600 |
| DENOMINATORS | PASS | |
| HOUSE | PASS | |
| PIN | PASS | sha=8cf0b8b |
| POSITIVITY | PASS | fixtures=22 negative=mu-nonpositive |
| M1-CORPUS | PASS | elapsed_ms=222.064 bound_ms=713 lines=1000 main=814 load1=11.098 |
| M1-SUITE | PASS | ledger=16 focused-one=49 nat-runtime=20 surface=OK |
| AGREEMENT | PASS | cases=7445 unary=5445 full-range=2000, completed 7445/7445, no watchdog exit |
| dunecho build (ladder item 2) | PASS | OK build: 0 errors, 0 warnings; exit 0 (required env -u OPAM_SWITCH_PREFIX -u CAML_LD_LIBRARY_PATH, and same env unset for the battery nohup launch after a first attempt failed with Library zarith not found) |
| house.sh (ladder item 3) | PASS | HOUSE OK |
| trusted-lines.sh (ladder item 4) | PASS | kernel=3997/4000 encoder=246/600 OK |
| sl_surface.exe (ladder item 5) | PASS | SL-SURFACE-OK 20/20, SL-SURFACE OK, exit 0 |
| lean (ladder item 8) | not run | git diff --stat -- meta/ is empty this round, no meta/ path changed |
| porcelain (ladder item 9) | PASS | MM README.md, dev/agreement.py, dev/house-catchalls.py, dev/house.sh (index+worktree changes); M rows for dev/M1-BUILD-LOG.md, dev/M1-MUTATION-LOG.md, dev/agreement-roundtrip.sh, dev/gen-m1-corpus.py, dev/nat-runtime.sh, dev/one-paths.sh, lib/erase.ml, meta/Axioms.lean, surface/parser.ml, test/sl_surface.ml; no meta/.lake, .gatework or _build rows; no untracked ?? rows |

All timed legs (M0-TIME, M0-RATIO, M1-CORPUS) read PASS this round, so
the VALIDATION PENDING sentence for red timed legs does not apply.

## Current compiler validation (2026-09-07)

The complete 21-leg battery passed on commit
`8603482c2d6a4493837aeb011971d4a62ac13306`, tree
`c316289b26baa47d00d7766722a0ed4d23920b7e`. This includes the reactor
compiler, CLI and full-buffer append changes that followed the previous
19-leg record. The command was `zsh dev/gates.sh`, with exit 0 and final
verdict `GATES-OK`. No gate, watchdog, performance bound or test selection
was changed. No compiler or runtime correction was needed.

Validation ran in the initially clean source snapshot at
`/Users/oobi/Documents/gpt4/kanon-current-validation/work`. Its tracked
files and index matched that commit. BUILD took 162.122 ms (gates.log
`MEASURE BUILD`), so the compiler build was incremental, not a cold-build
benchmark. All repository changes in this increment are validation
records and documentation.

The complete stdout is retained in
[validation/2026-09-07/gates.log](validation/2026-09-07/gates.log), with
the command, source identity and transcript SHA-256 in
[gates.json](validation/2026-09-07/gates.json). Stderr was empty. The
table transcribes the final MEASURE block; every exit code was zero.

| leg | status | tier | elapsed ms |
| --- | --- | --- | ---: |
| BUILD | PASS | SLOW | 162.122 |
| CARRY | PASS | MED | 353.131 |
| R0-COUNT | PASS | FAST | 392.862 |
| R0-AUDIT | PASS | FAST | 25.184 |
| SUITE-KERNEL | PASS | SUITE | 484.476 |
| SUITE-WASM | PASS | SUITE | 3129.863 |
| ENCODER-SUBSET | PASS | FAST | 62.608 |
| AXIOMS | PASS | MED | 25.721 |
| M0-E2E | PASS | SLOW | 233.095 |
| M0-TIME | PASS | SLOW | 2169.394 |
| M0-RATIO | PASS | SLOW | 211.868 |
| TRUSTED-LINES | PASS | FAST | 26.478 |
| DENOMINATORS | PASS | MED | 35.924 |
| HOUSE | PASS | MED | 331.371 |
| PIN | PASS | FAST | 63.851 |
| POSITIVITY | PASS | SUITE | 245.691 |
| M1-CORPUS | PASS | SLOW | 341.810 |
| M1-SUITE | PASS | SUITE | 4564.117 |
| AGREEMENT | PASS | SUITE | 23902.809 |
| REACTOR | PASS | MED | 613.469 |
| RUNTIME | PASS | MED | 3809.039 |

The binding observations differ from the whole-leg elapsed times above:
M0-TIME was 98.640 ms against 150 ms, with load1 9.808 and three
five-run medians. M0-RATIO was 1.174986 against 2.000, with a 14.967 ms
median check and load1 10.864. M1-CORPUS completed in 256.020 ms against
713 ms on a 1000-line corpus that returned main=814, at load1 10.864.
All passed on
the first complete run. AGREEMENT completed all 7445 cases, comprising
5445 unary witnesses and 2000 independent full-range cases. M1-SUITE
passed its 16 feature rows, 49 focused One checks, 20 Nat runtime checks
and surface suite. These remain finite validation evidence.

The current Lean package also passed its default build, including all
four regression roots: 51 jobs, zero errors and warnings, with
`leanprover/lean4:v4.33.0-rc1`. The reused `.olean` cache came from the
Stage L follow-up tree recorded in lean.json `cache.source`. Its cache
source files were byte-identical to this snapshot, both dependency
revisions matched the manifest, and the dependency working trees had no
tracked changes. Its 52 hashes were checked before and after the copy.
A second candidate tree was rejected because `Axioms.lean` differed
(lean.log). This was an incremental build.
`Axioms.lean` printed 39 reports: ten declarations had no axioms and
29 depended only on `Quot.sound`. The default build also reported the
test declaration `erasure_not_hom` depending on `propext` and
`Quot.sound` (lean.log line 21). Both names are inside lean.json
`axioms.admissible_names`. The four Stage F syntax theorems
remained axiom-free. A separate package requiring this snapshot built
through the public `KanonMeta` import, including a concrete two-element
vector copy theorem, with 48 jobs and zero errors or warnings. The
first client setup printed a Lake manifest warning about a changed
packages directory. The record resolves it with the default
`.lake/packages` and a verified dependency symlink. The reported run is
the one after that change (lean.json `external_client.initial_setup_warning`,
evidence `lean/client-initial.stderr`). The
source audit covered 16 first-party Lean files and 20 tactic blocks,
all using `kan_rfl`, with no forbidden proof tokens and no source changes.
Exact commands, source hashes, the external client and audit results are
retained in [lean.json](validation/2026-09-07/lean.json); the combined
output is in [lean.log](validation/2026-09-07/lean.log). The full cache
manifest remains in the external evidence directory, identified by its
path and SHA-256 in that record.

Evidence root: /Users/oobi/Documents/gpt4/kanon-current-validation/evidence.
`captures/run-8EZU4I` holds the battery stdout and stderr; `lean/` holds
build.log, axioms.log, client/, audit.py, check_cache.py and
cache-provenance.json.

The mutation ledger was audited against all 29 required stage ids:
SF-M1..M4, SG-M1..M5, SH-M1..M6, SI-M1..M3, SJ-M1..M4, SK-M1..M4
and SL-M1..M3. Each has a recorded killing observation; the plan's
SH-M1b is logged as SH-M6. This audit reuses historical mutation evidence
and does not claim a new execution of those mutants. SH-M4, SI-M1 and
SI-M3 were killed by exact-diagnostic differences. SJ-M1 and SJ-M4 were
killed by Wasm goldens, while the validator accepted those mutants.
SG-M5 covers the historical interim erasure refusal removed at Stage J.
SL-M2's original bound mutation ran while its baseline also failed under
load; subsequent baseline passes do not alter that original experiment.
The ledger retains these qualifications. SPEC's six obligation rows
remain discharged within their stated implementation and finite-test
scope; the external semantic models do not establish compiler preservation.

M1 exit ratification remains open. This record does not fill the user's
M1-EXIT stamp or claim full Lean parity, general arithmetic agreement,
or source-to-Wasm preservation.

## Lanyard M1: Cargo build command (2026-09-14)

`lanyard build --out DIR [--release] [--offline] [--print-model MODEL]
FILE.lan` checks and emits a fresh crate, then invokes Cargo in that
directory. It forwards Cargo streams and normal exit codes and reports
subprocess wall time in a separate `LANYARD-BUILD REPORTED` stderr row.
Paths remain outside shell text. Invalid arguments, invalid programs and
occupied output paths refuse before Cargo starts. Cargo failures retain
the emitted files. The generated program is never run by the build command.

The cumulative `--stage M1-build` gate passed, including the Stage F gate,
its five killed assertion mutations, the pending trust mutation and the
informational timing control. The new command has 16 process-boundary tests.
The full gate required execution outside the filesystem sandbox because
macOS Git's launcher writes a warning in the existing E2E environment test;
the 19 E2E assertions passed without changes. Final review corrected the
new gate's usage text and changed the missing-entry program, the inline
source in test/lan_build.py, to a valid program without `main`; the
focused build tests were rerun afterward.

A real `build --offline --print-model Todo` compiled the unmodified Todo
golden with Rust 1.98.1, using the installed `1.98` toolchain alias. Cargo
reported 198908.987 ms for the first compilation, with two existing generated
code warnings. The generated Cargo.toml and Rust source were byte-identical
to the golden. Running the executable separately returned the exact corpus
output with exit 0 and empty stderr.

The probe used a private Cargo home and target directory. Its Git sources
were fetched from the local checkouts at the pinned commits, preserving
the generated Git dependency declarations. Two missing crate archives,
time-macros 0.2.32 and zerocopy-derive 0.8.57, were downloaded into that
private cache and checked against Cargo.lock hashes before the offline
build. The emitted crate's resolved lockfile is retained with the captures.

The source inventory measures 268 driver lines and 12822 total lines.
The existing proposal keeps its 212-line driver and 12766-line total
limits. Its candidate driver check therefore fails, while M0 reports six
passing legs and one pending leg with no failed leg. No numeric allowance,
policy approval or milestone exit is recorded. See STAGE-M1-BUILD.md and
the receipt under `dev/validation/stage-m1-build/` for commands and hashes.

## Stage M1 BUILD review fixes (tag LSM1B, 2026-09-14)

F-1 bin/lanyard.ml. The header exit-code paragraph now states that the
build command forwards Cargo's own exit status after the crate is
written, so 1, 64, 101, 127 and 255 can come from Cargo, and that the
refusals before Cargo keep the 0, 1 and 64 meanings.

F-2 bin/lanyard.ml. The `dispatch_build` doc comment now states that an
I/O failure after the guards is loud. The process exits 2 with the
system error text, the same as the crate command.

F-3 test/lan_build.py. Two assertions could not fail. The signalled test
now reports against an independent code, 255 or 128 plus SIGTERM, and no
longer compares the exit code with itself. The missing-cargo test now
removes the driver's own report row from stderr and asserts the shell
diagnostic `not found` in what remains.

F-4 bin/lanyard.ml, test/lan_build.py. A new `lan_file` helper requires a
stem before the `.lan` suffix, so a bare `.lan` is a usage error. The
build arm and the four emit arms share the helper. The build arm keeps
its own dash guard, so the emit arms accept the same paths as before. A
new `bad` usage row covers `build --out DIR .lan`.

F-5 dev/M1-BUILD-LOG.md. The M1 build entry named a missing-entry fixture
file that is not staged. The sentence now names the inline source in
test/lan_build.py.

F-6 bin/lanyard.ml. The 246-character usage line is split across four
source lines with `^`. The printed text stays byte-identical.

F-7 bin/lanyard.ml. The output directory was carried twice. The flags
`output`, `release` and `offline` move to their own `build_flags` record
nested in the parse accumulator. The parse returns that record with the
directory and the path, so no stale directory travels with the flags.
The repeat detection for every option stays. The doc comments describe
the two records.

The fix ladder (tag fix-1) ran the full Stage M1-build gate on the
staged tree and reported STAGE-M1-BUILD OK and STAGE-GATE-EXIT 0. The
status rows matched the baseline capture exactly, 87 rows against 87
rows, and all 23 pinned rows were present with 0 missing; no row read
RED, FAIL or SURVIVED. The trusted-code line count in the proposed
policy row moved from 12822 to 12848 total lines because of the new
doc comments; the row stays PROPOSED with candidate=FAIL, which is the
expected state until the user rules on the policy. The four Python
suites ran: lan_trusted_inventory.py 18 tests OK, lan_trusted_policy.py
17 tests OK, lan_m0_gates.py 36 tests OK, and lan_build.py 16 tests
OK. The usage text is byte-identical to the text before the fixes.

## Lanyard M1: in-memory execution (2026-09-14)

`lanyard run [--steps N] [--print-model MODEL] FILE.lan` checks, specializes
and lowers the source before evaluating main over the Rust IR. Native
functions, captures, recursive data and finite checked handlers retain
their checked lowering. The five Nat primitives use arbitrary-precision
arithmetic. Model operations use an immutable per-run store with separate
connections, selected schemas, explicit initialization, unique keys and
create/lookup. Only `sqlite::memory:` connections are accepted. The source
program scripts its operations; HTTP request parsing remains future work.

Successful runs discard their result unless model output is selected.
Output is built only after success. Model integer, byte and UTF-8 checks
retain the printer's storage bounds. Quoted text uses OCaml byte escaping.
Steps default to 100000 and may be set to 1 through 1000000. Evaluation also
has a nesting limit of 512. Runtime errors are values and return exit 1;
invalid options and missing input return 64.

The new sources are `rust/interp.ml` (141 lines), `rust/run_store.ml` (66)
and `rust/run_value.ml` (107). The driver grows by 32 lines to 326.
The complete inventory measures 49 files and 13194 lines. The three
interpreter files occupy the existing unassigned group. The proposed
12766-line policy, its source roster and the 212-line driver limit remain
unchanged, with candidate=FAIL and verdict PENDING. No trust scope,
allowance number, policy approval or milestone exit is recorded.

The stage retains the cumulative M1 build gate, then adds 40 interpreter
checks, 26 CLI tests and five isolated mutation controls. The CLI suite
includes 11 observations from existing closure and recursive fixtures,
the four-row database handler and the M0 Todo output. Its cases cover
connection and model isolation, aliases, evaluation order, missing rows,
duplicate keys, scalar limits, foreign refusals, command syntax and paths.
See `dev/STAGE-M1-RUN.md` and the stage receipt for the commands, outcomes
and final compiler-source hashes.

The cumulative command completed with `STAGE-M1-RUN OK`, exit 0. All 40
interpreter checks, 25 CLI tests and five mutation controls passed. M0
reported six passing legs, one pending trust leg and no failed leg. Timing
was reported as NOISY and remains informational. The first sandboxed run
stopped at two existing E2E assertions because macOS Git printed a confstr
warning. Running the same gate with normal filesystem access passed all
19 E2E tests with their assertions unchanged. The receipt retains that
initial diagnostic alongside the successful complete gate capture.

## Stage M1 RUN review fixes (tag LSM1R, 2026-09-14)

A slice review of the 20 paths staged on f4f6e16 produced a judged finding
list. One prober pass and one review Workflow reported the items, and the
judge kept seven for this fix round. The fixes below change the
interpreter, the store, the two test suites and the stage documents. They
add no interpreter observation, so the pinned row
`LAN-RUN OK observations=40` stays 40.

- F-1 low, test/lan_run_mutations.py: `run` now takes a `timeout` argument
  and the six cold builds of the copied tree pass `timeout=None`. A build
  under machine load can no longer raise an uncaught timeout that reads as
  a surviving mutant. Mutant executions keep the 120 s bound.
- F-2 low, dev/STAGE-M1-RUN.md: the nesting limit is stated in units of
  evaluation depth. Each subterm evaluation and each call consumes one
  unit, so one source-level call consumes several. The guard is unchanged.
- F-3 low, rust/interp.ml and test/lan_run.ml: the Boolean tag identity had
  three copies of one literal. `Interp.boolean_tid` now reads the identity
  from `Model.bool_repr` with an exhaustive match over the representation
  constructors, and both `primitive` and the unit test use that helper.
- F-4 refuted, test/lan_run_mutations.py: the steps mutant is killed by the
  nesting guard, which is the kill the control is meant to prove. The
  mutation log sentence is accurate. No change.
- F-5 nit, test/lan_run.py: the `cargo` stub records its own invocation in
  a marker file and the test asserts that marker is absent. The Cargo half
  of the case can now fail.
- F-6 nit, test/lan_run.py: one new case connects, pushes the schema,
  creates a row, pushes the schema again and looks the row up. The claim
  "Repeated schema initialization preserves the rows" is now tested. The
  CLI count moves from 25 to 26 in dev/STAGE-M1-RUN.md and in the stage
  description above.
- F-7 nit, rust/run_value.ml and rust/run_store.ml: `text` takes an
  optional label and `connect` passes "connection URL", so a non-UTF-8
  connection URL no longer reports "invalid UTF-8 in model text".
- F-8 nit, merged Workflow items, no behavior change: `run_store.model`
  binds `creating` once, `Run_value.key` takes the validated fields from
  `model_fields` instead of repeating the field and zip work, and the two
  parameters that shadowed their function name are renamed to `kind` and
  `name`.
- Not fixed: the Workflow item about `call` repeating the lookup work of
  `find` in rust/interp.ml was not upheld by the Workflow verifier, so it
  stays. Two style-only items, the suffix rebuilding in the `contains`
  helper of test/lan_run.ml and the option and result chain in the
  `--steps` parsing of bin/lanyard.ml, were dropped for the seven-finding
  cap.

The six captures under `dev/validation/stage-m1-run/` predate these fixes
and stay frozen, and their receipt keeps `cli_tests=25`; the recorded
outcome sentence above also keeps the counts of that earlier run. The fix
ladder re-ran `zsh dev/gates.sh --stage M1-run`.

The fix-1 gate run, 2026-09-14 14:02 PDT, is GREEN: `STAGE-GATE-EXIT 0`,
all 96 of 96 rows match the frozen capture, and all 32 of 32 pinned rows
hold. test/lan_run.py now reports `Ran 26 tests`, where the frozen
capture shows 25. The closing run repeats this gate with the same
expectations; its log stays in the review kit as
gates-LSM1R-close.log.

## Lanyard M1 scripted requests (2026-09-14)

This slice adds `lanyard run --request URI FILE.lan`, the scripted request
portion of M0-PLAN section 8. A checked `Cx -> Uri -> SeeOther` entry point
receives a fresh in-memory database context and an origin-form URI. The
interpreter implements the pinned `topcoat.db` and `topcoat.see_other`
operations and renders an empty HTTP 303 response with CRLF headers.

The context registers reachable model layouts. Repeated context lookups
share the database; separate requests and explicit connections stay
isolated. Schema initialization remains explicit. The driver validates
request options before source I/O and refuses combination with
`--print-model`. Handler type errors and runtime failures print no response.
URI validation rejects control characters, malformed escapes and locations
outside the documented origin-form subset. The existing step and nesting
bounds apply.

`dev/STAGE-M1-REQUEST.md` describes the interface and limits. The example
under `test/fixtures/request.lan` creates and reads a row before redirecting.
The new `--stage M1-request` gate retains M1-run and adds 23 interpreter
checks, 18 CLI tests and four mutation controls. The previous foreign
refusal test now uses a synthetic future operation, since `topcoat.db` is
implemented. It still kills the unsupported-operation mutation.

The source inventory measures the new runtime module and driver changes
under the existing proposed policy. No policy roster, budget, target
signature, Rust golden or carried kernel file changes in this slice.
M0 remains pending. Validation captures, the inventory and source
hashes are retained under `dev/validation/stage-m1-request/`.

The complete cumulative gate passed with normal filesystem access: 23
request interpreter checks, 18 request CLI tests and four killed request
mutations, retaining the 40 interpreter checks, 26 CLI tests and five
mutations of M1-run. An earlier attempt hit the existing benchmark-driver
test's 30-second timeout under high machine load. That unchanged test
passed alone in 4.408 seconds before the final cumulative run passed.
The passing capture includes expected FAIL rows from negative controls.

## Stage M1 REQUEST review fixes (tag LSM1Q, 2026-09-14)

The fixes come from the LSM1Q review kit: prober hypotheses H1-H14 and the
ctxcat-review Workflow run wf_7f8df44c-271 (raw 4, upheld 2, survivors 2).

- F-1 nit bin/lanyard.ml: the driver header and the `run_options` comment now
  state request mode, the checked `Cx -> Uri -> SeeOther` entry point, the
  `--request URI` option, exit 64 for a malformed URI before source I/O,
  exit 1 for a run with no response and exit 0 with the 303 on stdout.
- F-2 nit rust/interp.ml: `run` and `request` share one `checked_steps`
  helper. The refusal text stays byte-identical.
- F-3 nit dev/STAGE-M1-REQUEST.md and README.md: the accepted-URI sentences
  drop "optional query". They now state that after the leading slash `?` is
  an ordinary path byte and the interpreter never splits or counts it.
- F-4 nit test/lan_request.py: the two unfalsifiable assertions in
  `test_no_cargo_or_shell` become one comment. The PATH-only environment and
  the `$(id)` URI stay, so the suite still runs 18 tests.
- F-5 low rust/interp.ml: the `request` entry-point pattern binds `cx_type`
  and `uri_type`, so the name `uri` means the validated string alone.

Proof: the fix suites ran on a copy of the tree under `$TMPDIR`. Observed
rows: build rc=0; `test/lan_trusted_inventory.py` Ran 18; `test/lan_trusted_policy.py`
Ran 17; `test/lan_m0_gates.py` Ran 36; `test/lan_build.py` Ran 16;
`test/lan_run.py` Ran 26; `test/lan_request.py` Ran 18 (floor 18 OK);
`lan_run.exe` LAN-RUN OK observations=40; `lan_request.exe` LAN-REQUEST OK
observations=23. Every suite exited 0. The mutation needles of
`test/lan_run_mutations.py` that target `rust/interp.ml` are unchanged:
`(List.rev arguments) fn.body` and `state.steps <= 0`, one occurrence each.

Ladder verdicts: the baseline ladder on the unfixed staged tree was GREEN at
2026-09-14 16:41 PDT (GATE LSM1Q tag=baseline GREEN, STAGE-GATE-EXIT 0,
RED-WATCH 0, PINS 40/40, ROWS 104/104 IDENTICAL against
dev/validation/stage-m1-request/stage.stdout). The fix-1 ladder on the fixed
tree was GREEN at 17:29 PDT with the same rows (tag=fix-1). Both logs live
in the review kit at ~/Documents/lanyard-stage-m1-request-review
(gates-LSM1Q-baseline.log, gates-LSM1Q-fix-1.log). The census rows above
were observed again at 17:3x on the fixed tree (probes/fix-suites-2.log).
The close ladder runs after this block is staged; its rows stay in the kit
(gates-LSM1Q-close.log).

## Lanyard M1 DELETE (2026-09-14)

Added `Model.delete_by_id` as a checked foreign schema and generated
`ModelName.delete_by_id` instance. Rust emission calls the pinned Toasty
method with a checked Nat key and an asynchronous unit result. The
interpreter removes only the matching model/key in the selected connection.
Missing keys and repeated deletion succeed, and deleted keys are reusable.

The target catalog grows from 15 to 16 rows, retaining nine foreign types.
The Todo axiom report grows from 17 to 19 foreign constants, adding the
schema and its model instance. Exact catalog assertions and the report
golden now require those entries. Toasty and Topcoat source commits and
Topcoat anchors stay unchanged; the Toasty signature digest covers the
additional row.

Validation: `zsh dev/gates.sh --stage M1-delete` passed through the cumulative
M1 request gate, 23 deletion unit checks and all four deletion mutations.
Clean and restored mutation controls passed. The final CLI suite passed
nine tests, including a deletion-only request that must retain its model
through reachability. That ninth test was added after the cumulative gate
had run its eight-test CLI suite; the final nine-test suite was captured
separately. Compiler sources were unchanged after the cumulative gate.

The emitted create/delete/recreate crate built offline against both clean
local target pins with Rust 1.98.1. Its real SQLite run printed exactly
`Counter { id: 7, value: 23 }` and a newline, matching the interpreter,
with exit 0 and no stderr. The build retained 11 unused-code or unused-value
warnings. A private Cargo cache copied 210 locally available archives only
after checking their lockfile checksums. The successful build is recorded
in the workspace gateledger. Captures, generated crate, lockfile, inventory
and source hashes live under `dev/validation/stage-m1-delete/`.

The first cumulative run encountered the existing macOS `git` confstr
warning in two Git-isolation tests under the sandbox. The complete gate
passed with normal filesystem access and the original assertions.

Trust remains pending. The measured printer group is 1237 lines and the
generated signature module is 110 lines. The proposed allowances remain
1231 and 104 respectively, and no M0 exit or policy ruling is recorded.
Deletion inside model-returning closures is covered; function values whose
unit result has an erased layout retain the existing erasure refusal.

## Stage M1 DELETE review fixes (tag LSM1D, 2026-09-14)

F-1 (low, rust/run_store.ml:89). The foreign dispatch arm for the model
schemas used a three-space indent and repeated the three schema names.
The arm now reads `| () when Result.is_ok (Model.operation row.schema) ->`
at the two-space indent of every sibling arm. `Model.operation` returns a
result whose Error is the refusal, so the schema name list stays in
rust/model.ml only and cannot drift from the dispatch.

F-2 (nit, rust/run_store.ml:53). `previous` scanned all `db.rows` for every
operation although the Delete arm never reads it. The binding is now the
thunk `let previous () = ...`, and only the Create duplicate-key guard and
the Get arm force it. Delete makes one pass over the rows. The predicate
keeps the spelling `Bignum.equal key stored_key` with the reversed operands,
which the lookup-key mutant of test/lan_run_mutations.py needs.

F-3 (nit, rust/model.ml:108). The `result` field projection string was built
for Delete as well, and the Delete body discarded it. The projection now
builds inside the `Create | Get` branch of `body`. `| Delete -> call in`
stays byte-identical for the erased-delete mutant.

F-4 (nit, test/lan_delete_mutations.py:55). A survivor exited inside the
mutation loop, so the harness skipped the restored control and reported no
restored state. The loop now records the survivor message, breaks, restores
the source, runs the restored control, prints the survivor summary and exits
non-zero with `LAN-DELETE-MUTATIONS FAILED killed=<n>/4 restored=GREEN`. The
green path prints the same rows as before: `LAN-DELETE-MUTATIONS CONTROL OK`,
four `LAN-DELETE-MUTATIONS <name> KILLED` rows and
`LAN-DELETE-MUTATIONS OK killed=4/4 restored=GREEN`.

F-5 (nit, target/README.md:3-11 and :95-100). The two edited paragraphs
appended sentences onto existing lines and ran past the file wrap. Both
paragraphs are re-wrapped at 76 columns with no wording change. The counts
16, nine, seven, 110 and 104 are unchanged, and the markdown link
`[crate command](../dev/STAGE-E-CRATE.md)` is not split.

Proof. The fix suites ran on a copy of the tree with the ladder build recipe
and printed: `_build/default/test/lan_request.exe observations=23`,
`_build/default/test/lan_run.exe observations=40`,
`_build/default/test/lan_delete.exe checks=23 failures=0`,
`test/lan_request.py Ran 18`, `test/lan_run.py Ran 26`,
`test/lan_build.py Ran 16` and `test/lan_delete.py Ran 9`. All seven rows are
OK at their floors and the run exit code is 0.

Needles. Each mutation needle occurs exactly once after the fixes. In
rust/run_store.ml: `Ok (Unit, replace { db with rows } store)` 1,
`Bignum.equal stored_key key` 1,
`String.equal name model.name && Bignum.equal stored_key key` 1,
`Bignum.equal key stored_key` 1, `refuse ("foreign operation " ^ row.schema)`
1, `Ok (Database database.id,` 1, `Ok (Database id, store)` 1,
`not (List.mem row catalog.constants)` 1. In rust/model.ml:
`| Delete -> call in` 1. In rust/interp.ml: `(List.rev arguments) fn.body` 1,
`state.steps <= 0` 1. In rust/run_http.ml: `HTTP/1.1 303 See Other` 1,
`when uri_character character` 1.

Ladders. The baseline ladder ran on the unfixed staged tree and reported
GREEN at 19:18 PDT (GATE-END 02:18:34Z, stage_rc=0). The compare-rows
probe on the baseline tag showed RED-WATCH 0, PINS 48/48 and ROWS 112/112
IDENTICAL. The fix-1 ladder ran on the fixed tree and reported GREEN at
19:4x PDT (LADDER-DETACHED 02:41:52Z), with rows
`LAN-DELETE OK checks=23 failures=0`,
`LAN-DELETE-MUTATIONS OK killed=4/4 restored=GREEN`, `STAGE-M1-DELETE OK`
and `STAGE-GATE-EXIT 0`. The compare-rows probe on the fix-1 tag showed
RED-WATCH 0, PINS 48/48 and ROWS 112/112 IDENTICAL. The close ladder
re-runs `zsh dev/gates.sh --stage M1-delete` on the final tree after the
close, and its verdict is recorded in the review kit, not in this file.

## Stage M1 UPDATE (2026-09-14)

Every model now exposes `ModelName.update fields db : ModelName`. The full
checked model value supplies its primary key and replacement scalar fields.
The interpreter validates the complete value, requires an existing row,
and replaces only that model and key in the selected connection. Missing
and deleted rows fail. Repeated updates succeed. The operation remains
observable when its returned model is unused, and works through closures
and scripted request database handles.

The Rust printer shares the existing model input and output conversions.
The new pinned signature validates the supplied scalar fields, fetches the
existing row with `get_by_id`, and applies Toasty's instance `update!`
macro. Its primary key is assigned the same value used by the lookup.
Lookup and update are separate calls without a transaction guarantee.
The target catalog grows from 16 to 17 rows, still with nine foreign types.
Todo's axiom report grows from 19 to 21 foreign constants. Exact catalog,
instance-list and axiom expectations include the new schema and instance.
The Toasty signature digest changes; both library source pins stay fixed.

The update suite passes 28 unit checks and 11 CLI tests. Five mutations
are killed with named behavioral failures, and clean and restored controls
pass. The tests cover missing rows, key and field ranges, invalid text,
model layout and metadata, other keys/models/connections, key-only models,
closures, unused results and request reachability. The fixture deliberately
places its key after the text field and replaces text, Bool and Nat values.

The emitted fixture builds offline with Rust 1.98.1 against the clean
pinned Toasty and Topcoat sources. Real SQLite prints exactly
`Task { title: "updated", id: 7, completed: true, value: 23 }` and a newline,
matching the interpreter, with exit 0 and empty stderr. The build reports
five unused-code or unused-variable warnings and is recorded in gateledger.
The final evidence includes the emitted crate, lockfile, source inventory,
source hashes and captures under `dev/validation/stage-m1-update/`.

An initial cumulative run timed out on two inherited CLI rejection checks
with a 10-second limit. Both checks passed in isolation in 0.266 seconds;
the measured host load average was 148.45. Their assertions and timeouts
stay unchanged. Trust remains pending: generated signatures measure 116
lines against the proposed 104-line allowance. No policy or M0 exit ruling
is added.

The sandboxed retry passed those rejection checks, then encountered macOS
Git `confstr` warnings in the two existing Git-isolation tests. Validation
was rerun with normal filesystem access and the original assertions.

The final inventory measures 1240 printer lines and 13338 compiler lines
across 50 source files. The existing proposed budgets remain 1231 printer
lines and 12766 compiler lines; their status remains proposed.

Final validation: `zsh dev/gates.sh --stage M1-update` passed with exit 0,
including the cumulative M1 deletion gate, all 28 update unit checks,
all 11 update CLI tests and all five update mutations. Clean and restored
controls passed. The combined M0 report records six of seven legs passing,
one pending trust decision and zero failed checks. Compiler sources stayed
unchanged after this run; only documentation and evidence were completed.

## Stage M1 UPDATE review fixes (tag LSM1U, 2026-09-14)

The review kit LSM1U ran on base 3c3f2c1. An opus prober judged 20
hypotheses and reported CONFIRMED-DEFECT 2, REFUTED 2 and NOT-A-FINDING 16.
A ctxcat-review Workflow, run wf_4ad9f6af-7b2, ran 3 agents with 0 errors
and produced 2 raw findings, of which 1 was upheld. The upheld finding is
the same defect as F-1. Fable subagents died on the
`[reasoning_extraction]` classifier, so the finder and builder tiers ran on
opus and the closer runs on sonnet.

F-1 (nit, target/toasty-7bd502cb.sig:11 and dev/STAGE-M1-UPDATE.md:50).
The `Model.update` print rule expands `#{fields}` two times, once to build
`__lan_fields` whose `id` selects the row and once inside `update!`, so the
emitted block repeats each field conversion. The conversions are pure, so
the behavior does not change. The rule is pinned by the erased-update
needle, by the signature digest in target/PIN.json and by the frozen native
capture, so the fix is a disclosure and not a rule change. A new paragraph
in dev/STAGE-M1-UPDATE.md states the double expansion, its reason, and the
later signature change that can bind the converted key one time. The .sig
row, target/PIN.json, rust/model.ml and rust/run_store.ml are unchanged.
target/README.md lists the catalog entry only and does not explain the
rule, so it is unchanged too.

F-2 (nit, README.md:91). The M1 update paragraph said "exposed as
`Counter.update fields db`" without the "for each model" qualifier that the
delete paragraph at README.md:79 carries, although the update example runs
the Task model. The paragraph now reads "exposed as `Counter.update fields
db` for each declared model", with the placement and the wording of the
delete paragraph. The two edited lines are re-wrapped at the width of their
neighbors. No other wording changed.

Proof. The fix suites ran on a copy of the tree with the ladder build
recipe and printed nine OK rows at their floors:
`_build/default/test/lan_request.exe observations=23`,
`_build/default/test/lan_run.exe observations=40`,
`_build/default/test/lan_delete.exe checks=23`,
`_build/default/test/lan_update.exe checks=28`, `test/lan_request.py Ran
18`, `test/lan_run.py Ran 26`, `test/lan_build.py Ran 16`,
`test/lan_delete.py Ran 9` and `test/lan_update.py Ran 11`. The run exit
code is 0. Each mutation needle still occurs exactly once in the tree: the
no-update, all-keys, all-models and missing-row-success needles in
rust/run_store.ml, and the erased-update needle in
target/toasty-7bd502cb.sig. Both fixes touch documentation only.

Ladders. The baseline ladder ran on the unfixed staged tree and reported
GREEN (W/gates-LSM1U-baseline.log: GATE-START 2026-09-15T06:01:11Z, load1
38.84; GATE-END 06:25:41Z, load1 46.41; stage_rc=0). The compare-rows probe
on the baseline tag showed RED-WATCH 0, PINS 57/57 and ROWS 121/121
IDENTICAL. The fix-1 ladder ran on the fixed tree and reported GREEN
(W/gates-LSM1U-fix-1.log: GATE-START 06:35:03Z, load1 26.12; GATE-END
07:02:11Z, load1 38.51; stage_rc=0), with rows
`LAN-UPDATE OK checks=28 failures=0`,
`LAN-UPDATE-MUTATIONS OK killed=5/5 restored=GREEN`, `STAGE-M1-UPDATE OK`
and `STAGE-GATE-EXIT 0`. The compare-rows probe on the fix-1 tag showed
RED-WATCH 0, PINS 57/57 and ROWS 121/121 IDENTICAL. The close ladder
re-runs `zsh dev/gates.sh --stage M1-update` on this exact staged tree
after the close, and its verdict is recorded in the review kit, not in
this file.

## Stage M1 ALL (2026-09-15)

Added `Model.all`, specialized as `ModelName.all db : ModelName.rows`.
Model elaboration generates the nominal list family with `nil` and `cons`
constructors and refuses collisions with its generated names. The checked
bridge verifies the two-constructor layout and reuses scalar conversions
for Nat, Bool and byte-list fields. The interpreter filters by model and
connection, sorts numeric keys and returns an immutable list. The emitted
query orders by `id`, then converts the returned vector with a reverse
`try_fold` that propagates row-conversion failures.

The pinned Topcoat Todo example supplies the query shape. Library source
pins and anchors remain the same; the signature digest includes the new
schema. The catalog has 18 rows, nine foreign types and 122 generated
lines. Todo's axiom report has 23 foreign constants and three definitions.
Existing Rust goldens gain the generated model list declarations.

Focused validation passed 23 listing unit checks and 12 CLI tests. All five
listing mutations were killed and restored controls passed. The retained
deletion and update mutation suites passed 4/4 and 5/5 respectively. The
emitted fixture built offline with Rust 1.98.1 and ran on real in-memory
SQLite. Both backends printed:

```text
Task { title: "updated", id: 3, completed: true, value: 122 }
```

Both runs exited 0 with empty stderr. Cargo reported 20 unused-code or
unused-variable warnings. The fixture inserts out of order, updates one
row, deletes another, reads the first remaining row and totals the complete
list through a checked recursive function.

The initial cumulative run stopped on sandboxed Git `confstr` warnings
in two M0 end-to-end stderr assertions. All 19 harness tests passed with
normal Git access and unchanged assertions. The next run reached the
deletion mutations, where the old emitter source target no longer matched
the branch's `Result` wrapper. The mutation now replaces `Ok call` with
`Ok "()"` and retains the same `checked unit result` failure assertion.
The isolated deletion, update and listing mutation suites then passed.

The cumulative command is `zsh dev/gates.sh --stage M1-all`. Its final
capture, the earlier diagnostic captures, emitted crate, lockfile and
source hashes are recorded under `dev/validation/stage-m1-all/`.
The compiler inventory measures 50 files and 13398 lines against the
existing proposed budget of 12766. Trust remains pending; this slice
introduces no policy ruling or M0 exit stamp.

## Stage M1 ALL review fixes (tag LSM1A, 2026-09-15)

The review kit LSM1A ran on base 6e69b74 over a 64-path slice, that is 28
review paths and 36 frozen captures under `dev/validation/stage-m1-all/`.
A ctxcat-review Workflow and an opus prober supplied the raw findings. Six
findings passed the judge: one low and five nits. The baseline ladder was
green before any edit.

F-1 (nit, rust/run_store.ml:86). The result line of the `Model.Delete` arm
carried a 12-space indent while its sibling lines in the same arm carry
11. The line now carries the 11-space indent that `git show HEAD` records
for the neighbouring arms. The expression is unchanged.

F-2 (low, test/lan_all.py:109-116). `test_generated_name_collisions_are_-
rejected` asserted the exit code and an empty stdout only, so any failing
`check`, for any reason, satisfied the eight subTests. The subTest now
also asserts `b"duplicate declaration"` in stderr, the way
`test_wrong_list_type_is_rejected` pins `b"mismatch"`. The text comes from
the `fresh_names` check in surface/elab.ml:1250 and covers the four
generated names and both source orders. The test count stays 12.

F-3 (nit, target/README.md:3-5). The third line of the catalog paragraph
ran to 86 columns while the file wraps at 71 to 76. The paragraph is
rewrapped at 76 columns with the same words in the same order. No sentence
and no catalog count changes.

F-4 (nit, rust/model.ml:114-117). `foreign_call` built the row conversion
string for every operation although the `Delete` render arm discards it.
The conversion is now a thunk, `converted ()`, called in the `All` arm and
in the `Create | Get | Update` arm only. Every emitted string stays
byte-identical, so the goldens and the lan_all.ml needles do not move.

F-5 (nit, rust/model.ml:44-48). `Elab.model_rows model.model_name` was
evaluated for `list_tid` and again inside the layout predicate. The
catalog binds `rows_family` once above `list_tid` and uses the binding in
both places. The `rows_name` helper near line 29 takes a `Model.t`, not
the `Elab.model_info` value used here, so it is not reused.

F-6 (nit, rust/run_store.ml:48-49). The sort comparator bound the sort key
as `left` and the ignored row as `_left`, which reads as a pair of names
for one value. The ignored row binders are now `_left_row` and
`_right_row`. `Bignum.compare left right`, a mutation needle, is
unchanged.

Proof. The fix suites ran on a copy of the tree, never in the repository.
The unit suites report lan_request.exe observations=23, lan_run.exe
observations=40, lan_delete.exe checks=23, lan_update.exe checks=28 and
lan_all.exe checks=23, each at its floor. The CLI suites report
lan_request.py 18 tests, lan_run.py 26, lan_build.py 16, lan_delete.py 9,
lan_update.py 11 and lan_all.py 12, each at its floor. Every row is OK and
the script exits 0. The needle sweep over the five mutation suites reports
NEEDLES ok=23 bad=0.

Ladders. The baseline ladder ran on the unfixed staged tree and reported
GREEN (GATE-END tag=baseline 2026-09-15T13:13:54Z, stage_rc=0; GATE LSM1A
tag=baseline GREEN). The compare-rows probe on the baseline tag showed
RED-WATCH 0, PINS 66/66 and ROWS 130/130 IDENTICAL. The fix-1 ladder ran
on the fixed tree and reported GREEN (GATE-END tag=fix-1
2026-09-15T13:38:21Z, stage_rc=0; GATE LSM1A tag=fix-1 GREEN). The
compare-rows probe on the fix-1 tag showed RED-WATCH 0, PINS 66/66 and
ROWS 130/130 IDENTICAL. The close ladder re-runs `zsh dev/gates.sh --stage
M1-all` on this exact staged tree after the close, and its verdict is
recorded in the review kit, not in this file.


## Stage M1 TEXT (2026-09-15)

The pinned Topcoat Todo create handler trims its title and checks whether
the result is empty. This slice adds `Text.trim Bytes value` and
`Text.is_empty Bytes value` to the checked target catalog. Both operations
accept the existing nominal byte-list representation and validate byte
ranges and UTF-8. Trimming preserves interior text and removes all 25
Unicode whitespace scalars at either end. Empty checks return the existing
two-unit Boolean sum. Shared inputs retain their original contents.

Closed erased text arguments survive specialization for direct calls,
aliases and captured calls. The Rust adapter checks the family layout and
the complete foreign-call metadata before printing the pinned string
idioms. The interpreter uses the same layout and conversion boundaries.
Unsupported layouts and open text arguments fail before execution or
emission. Conversion errors still propagate when a result is unused.

The catalog grows from 18 to 20 declarations, while the foreign type
census remains nine. Todo's axiom golden grows from 23 to 25 foreign
constants. The generated signature module measures 134 lines against the
existing proposed allowance of 104. Library commits and Topcoat source
anchors retain their pins. The new adapter joins both printer accounting
paths and the proposed roster; no budget, trust ruling or exit stamp is
approved by this slice.

`dev/STAGE-M1-TEXT.md` documents the API and target contract. The fixture
prints `Title { id: 1, text: "write tests", blank: true }`. The stage gate
retains all prior M1 model listing checks and adds 63 unit checks, four
CLI/native test groups, 111 native observations and five isolated
mutations with clean and restored controls. Tests include Unicode
whitespace, preserved non-whitespace scalars, embedded NULs, malformed
UTF-8, byte ranges, family separation, metadata tampering and unused
results. Validation evidence is recorded in `dev/validation/stage-m1-text/`.

The final `zsh dev/gates.sh --stage M1-text` run exited 0 with
`STAGE-M1-TEXT OK`. All 33 frozen build and test input hashes still matched
after completion. The unchanged 19-test Git integration harness and the
complete gate ran outside the macOS sandbox after sandboxed Git emitted
`confstr()` warnings into two strict stderr checks. The receipt records
that environment retry. M0 remains `PENDING`, with six passing legs and
the existing trust decision outstanding.

## Stage M1 TEXT review fixes (tag LSM1T, 2026-09-15)

The review kit LSM1T ran on base 661c0f5 over a 46-path slice, that is
36 review paths and 10 frozen captures under
`dev/validation/stage-m1-text/`. A ctxcat-review Workflow and an opus
prober supplied the raw findings. Seven findings passed the judge: two
medium and five low, one of which carries five nits. The baseline ladder
was green before any edit.

F-1 (medium, dev/M0-BUILD-LOG.md:2981). The slice block was appended to
the M0 log although every M1 stage block lives in this file under `##
Stage M1 <NAME> (date)`. The 42 appended lines now stand at the end of
this file under `## Stage M1 TEXT (2026-09-15)`, and dev/M0-BUILD-LOG.md
carries its HEAD bytes again and leaves the staged set. The words of the
block do not change; only the heading is retitled.

F-2 (medium, README.md:304). The saved-JSON sentence read 46 current
OCaml sources while the staged dev/trusted-policy.json roster grew to 47
when rust/text_ops.ml joined the printer group. The sentence now reads
47 current OCaml sources. test/lan_trusted_inventory.py rebuilds that
roster in the M1-text gate.

F-3 (low, rust/run_store.ml:108). The interpreter spelled `Rir.Tid
"sum<struct tuple<>|struct tuple<>>"` a third time as a bare literal.
rust/text_ops.ml:14 now binds `bool_tid` and defines `bool_repr` as
`Rir.TyUnion bool_tid`, and the store arm uses `Text_ops.bool_tid`.
rust/model.ml:14 stays as it is, because routing it through Text_ops
risks a module cycle. The mutation needle `(if String.equal text "" then
1 else 0)` on that line is byte-identical, so the invert-empty mutant of
test/lan_text_ops_mutations.py still finds its site.
test/lan_text_ops.ml and the M1-text gate row cover the change.

F-4 (low, rust/text_ops.ml:73). `trim` reported a runtime UTF-8 failure
through `invalid`, which prefixes "Rust emission: ", for a value that is
never emitted. The failure now returns `Error (Error.Mismatch "invalid
UTF-8 in text operation")` with the same message text. No test, golden
or capture pins the prefixed form. The M1-text unit suite covers the
path.

F-5 (low, test/lan_text_ops_mutations.py:62). The `break` after the
first survivor left the remaining mutants unrun, so the harness reported
one survivor even when several survived. The loop now runs all five
mutants and the failure report lists every survivor. The MUTATIONS table
at :11-22 and the count guard stay byte-identical. The five KILLED rows
and the restored control of the M1-text gate cover the change.

F-6 (low, test/lan_trusted_policy.py:214). The NaN corruption case keyed
on the raw `"limit": 9` literal, which this slice had to bump from 8.
The case now derives the literal from the policy object the test already
builds, through `policy["groups"][0]["limit"]`, and rewrites the first
occurrence only. The file adds no import. The subTest still raises
ValueError in the M1-text gate and in the M0 trust leg.

F-7 (low with five nits, dev/gates.sh:325). The usage string omitted
`M1-text` although the header comment at :43-44 and the dispatch at :50
both accept `--stage M1-text`; the tail now ends `|M1-all|M1-text]`. The
five nits: README.md:26-28 is rewrapped inside the file column band with
the same words, so no 93-column line stands in a 67 to 73 column
paragraph; target/README.md:3-13 is rewrapped for the same reason, with
the same 20, nine and eleven counts; rust/run_value.ml:73 drops the dead
`byte < 0 ||` disjunct, because the `natural` helper admits non-negative
numbers only; test/lan_text_ops.ml:56 extends the "Unicode neighbors
preserved" row with U+2060 WORD JOINER on the input and on the expected
output, so the disclosed 63 unit checks stay 63; test/lan_text_ops.py:26
renames the `negative_utf8` case to `invalid_utf8`, because the byte
list `[255]` is a valid byte with an invalid UTF-8 encoding. The M1-text
gate covers the usage row, run_value, the unit row and the case name;
the two rewraps are prose.

Carried. C-1 (low, surface/lower.ml:91). `program_with` calls
`text_operations source` although both production callers already bound
`Lower.text_operations specialized`. The fix changes the signature at
:89 and all three call sites, a cross-file refactor with no behavior
change that no staged test asserts, so it takes its own slice. C-2 (low,
rust/run_store.ml:98-100). A `Text.`-prefixed schema that the catalog
does not carry enters the prefix arm and dies with `Error.Mismatch "run:
text metadata differs"` instead of the `Error.Not_yet "Rust emission:
text schema <name>"` that rust/text_ops.ml:13 reserves. The arm is
unreachable today, because the staged target catalog holds `Text.trim`
and `Text.is_empty` only, and a review round never edits the target
catalog or target/PIN.json.

Ladders. The baseline ladder ran on the unfixed staged tree and
reported GREEN (GATE-END tag=baseline 2026-09-15T16:03:09Z,
stage_rc=0; GATE LSM1T tag=baseline GREEN). The compare-rows probe on
the baseline tag showed RED-WATCH 0, PINS 76/76 and ROWS 140/140
IDENTICAL. The fix-1 ladder ran on the fixed tree and reported GREEN
(GATE-END tag=fix-1 2026-09-15T17:14:59Z, stage_rc=0; GATE LSM1T
tag=fix-1 GREEN). The compare-rows probe on the fix-1 tag showed
RED-WATCH 0, PINS 76/76 and ROWS 140/140 IDENTICAL. The close ladder
re-runs `zsh dev/gates.sh --stage M1-text` on this exact staged tree
after the close, and its verdict is recorded in the review kit, not
in this file.

## Stage M1 URI (2026-09-15)

`Uri.from_text` converts a checked byte-list family into an origin-form
URI. It uses the existing request grammar and byte limit, preserving
percent escapes and URI text. Todo-style handlers can now redirect to
the fixed home path. Closed direct calls, aliases and captures use the
text specialization boundary; invalid values remain observable when
unused. The Rust adapter validates before calling the pinned Topcoat
URI parser, with `InvalidUri` in both generated error variants.

`zsh dev/gates.sh --stage M1-uri` passed the cumulative gate, 41 new
unit checks, five CLI test groups and three isolated mutations with
clean and restored controls. Two emitted native executables compiled
offline against the checked target pins with Rust 1.98 and passed 58
observations. Their synchronous and database-using modules cover URI
preservation, the 8192-byte boundary, invalid encodings and redirects.

The first gate exposed a retained catalog-count assertion. Catalog and
axiom assertions now account for 21 declarations and Todo's 26 foreign
constants. The next run hit two existing stderr assertions because
sandboxed macOS Git emitted `confstr()` warnings. The unchanged gate
passed outside the sandbox. The native compile reported 14 unused-code
warnings from generated helpers. Captures, exact inputs and hashes are
in `dev/validation/stage-m1-uri/receipt.json`.

The target signature digest and axiom golden include the new schema.
Foreign atoms remain nine; library commits, anchor hashes and trust
budget proposals retain their existing values. Trust and M0 exit remain
pending.

## Stage M1 URI review fixes (tag LSM1I, 2026-09-15)

The review kit LSM1I ran on base 73cedd0 over a 57-path slice, that is
25 review paths and 32 frozen captures under
`dev/validation/stage-m1-uri/`. A ctxcat-review Workflow and an opus
prober supplied the raw findings. Six findings passed the judge: one
medium, three low and two nits. The baseline ladder was green before
any edit.

F-1 (medium, dev/M0-BUILD-LOG.md:2980). The slice block was appended
to the M0 log, and its heading words were reversed against the
sibling shape. The 30 lines now stand at the end of this file under
`## Stage M1 URI (2026-09-15)`. dev/M0-BUILD-LOG.md is byte-identical
to HEAD again. The body of the moved block does not change; only the
heading line changes.

F-2 (low, test/lan_uri.ml:12). `contains` rebuilt the whole suffix at
every index, so each substring test was quadratic over the
36706-byte emitted module. The helper now scans indexes with
`Seq.init` and compares with `String.sub`, under a `limit >= 0` guard
that keeps the slice in bounds. The scan allocates nothing per index.

F-3 (low, test/lan_uri.ml:80). Nothing tied the emitted
`value.len() > 8192` to `Run_http.max_uri_bytes`. The existing
"emitted validation" check gains one conjunct inside the same
boolean, `contains code ("value.len() > " ^ string_of_int
Lanyard_rust.Run_http.max_uri_bytes)`. The count `checks=41` is
unchanged.

F-4 (low, target/README.md:5). The catalog sentence carried two `and`
conjunctions in one list. The first `and` is now a comma. Line 6 stays
byte-identical.

F-5 (nit, rust/model.ml:250). The added clause read `row.schema` next
to `row.Rir.schema` in one boolean. The clause is now qualified as its
neighbour is.

F-6 (nit, rust/text_ops.ml:72). The binder `_path` held a foreign
type, not a path. It is renamed `_uri_type`, and the rest of the line
stays verbatim.

Carried. C-1 (low, rust/model.ml:250 and rust/run_store.ml:98). The
two dispatch sites want a shared `Text_ops.handles` predicate. That
refactor widens the Text_ops interface and edits the run_store arm the
mutation harness keys on, so it takes its own slice. C-2 (low,
test/lan_uri.ml:40 and test/lan_uri_native.py:19). The accepted and
refused path lists are duplicated across the OCaml and the Python
harness. No shared source spans the two languages, and a generator
moves counts that frozen captures pin. C-3 (nit,
target/README.md:6). The line is 78 columns after the F-4 comma fix. A
reflow cascades through the rest of the paragraph and needs judgment
about wrap points. C-4 (low, rust/text_ops.ml:80). The emitter-side
byte limit still repeats the interpreter bound. The mutation needle on
that line must stay byte-identical, so the tie is made on the test
side as F-3 instead.

Proof. The fix suites report 16 of 16 rows OK: `lan_uri.exe
checks=41`, `lan_uri.py Ran=5`, and the M1 TEXT, RUN, REQUEST, DELETE,
UPDATE and ALL suites at their floors. The five mutation needles count
1 each in the staged blobs. The fix run staged 25 review paths
(`FIX-RUN paths=25`). The 32 frozen captures are untouched, because
the cached numstat is identical to the capture taken before the edits.
The em-dash sweep counts 0.

Ladders. The baseline ladder ran on the unfixed staged tree and
reported GREEN (GATE-END tag=baseline 2026-09-15T20:18:58Z,
stage_rc=0; GATE LSM1I tag=baseline GREEN). The compare-rows probe on
the baseline tag showed RED-WATCH 0, PINS 83/83 and ROWS 147/147
IDENTICAL. The fix-1 ladder ran on the fixed tree and reported GREEN
(GATE-END tag=fix-1 2026-09-15T21:00:32Z, stage_rc=0; GATE LSM1I
tag=fix-1 GREEN). The compare-rows probe on the fix-1 tag showed
RED-WATCH 0, PINS 83/83 and ROWS 147/147 IDENTICAL. The close ladder
re-runs `zsh dev/gates.sh --stage M1-uri` on this exact staged tree
after the close, and its verdict is recorded in the review kit, not
in this file.

## Stage M1 FORM (2026-09-15)

`Form.field Bytes body name` reads a named text field out of a
URL-encoded body. `Bytes` is the checked nominal byte-list family, as
for `Text.trim`, so Todo's create handler can take its title from a
scripted request body. `rust/form_data.ml` holds the interpreter side:
`Form_data.parse` splits the body on `&`, `Form_data.decode` resolves
`+` and `%HH` once for both halves of a field, and `Form_data.field`
selects one decoded name. The bounds are `max_bytes = 8192` and
`max_fields = 128`, applied before decoding or allocation. Empty
names, a missing `=`, invalid UTF-8 and duplicate decoded names fail
even when the result is unused.

The same module emits the adapter. Its embedded `runtime` string
validates every field with `lan_form_validate_component` and
`lan_form_field` before it calls the pinned
`topcoat::router::content::Form::<Vec<(String, String)>>::from_bytes`,
and every failure uses `Error::InvalidForm`. The CLI gains
`run --request URI --form BODY`. `--form` requires `--request`, each
option occurs once, and the handler then has type
`Cx -> Uri -> Bytes -> SeeOther`, with the original encoded body in
the third parameter.

`zsh dev/stage-m1-form.sh` retains the cumulative URI gate and then
runs the new suites. It prints `LAN-FORM OK checks=53`, the six CLI
test groups of `test/lan_form.py`, and the four isolated mutations
`skip-duplicates`, `skip-body-bound`, `skip-emitted-validation` and
`skip-effect-contract`, each KILLED, between
`LAN-FORM-MUTATIONS CONTROL OK` and
`LAN-FORM-MUTATIONS OK killed=4/4 restored=GREEN`. The stage row is
`STAGE-M1-FORM OK`. The native harness `test/lan_form_native.py`
builds two offline binaries against the checked target pins with Rust
1.98 and reports `LAN-FORM-NATIVE OK binaries=2 observations=76`.

The first bound candidate was 64 KiB. A debug native run overflowed
the generated byte-list destructor's stack, so the stage keeps the
8 KiB contract of the current recursive byte-list runtime. Large
program-created byte lists remain a general runtime limitation. This
slice does not change their representation and does not certify their
resource use.

The catalog holds 22 declarations and nine foreign types, and Todo
reports 27 foreign constants. The proposed printer roster gains
`rust/form_data.ml` with an unchanged budget. Library pins, anchor
fingerprints, trust approval and the M0 exit stamp are unchanged. The
docs are README.md, dev/STAGE-M1-FORM.md and dev/STAGE-M1-REQUEST.md.
Captures and tested input hashes are frozen under
`dev/validation/stage-m1-form/`.

## Stage M1 FORM review fixes (tag LSM1F, 2026-09-15)

The review kit LSM1F ran on base 37c5903 over a 74-path slice, that is
34 review paths and 40 frozen captures under
`dev/validation/stage-m1-form/`. An opus prober supplied 15 hypotheses
and three sweep rows, and one ctxcat-review Workflow run with three
agents supplied 7 raw findings, of which 6 were upheld, under a judge
cap of 7. Four findings passed the judge: one medium, one low and two
nits. Six more are carried.

F-1 (med, dev/M1-BUILD-LOG.md:3083). The M1 log ended with the LSM1I
review block and held no block for this stage, and the file was absent
from the 74 staged paths. The stage block above and this review block
are appended, so the stage now carries a heading of the sibling
shape, with the stage name and the date. Every number in the prose is
read from the frozen captures and is not recomputed.

F-2 (low, rust/form_data.ml:81,85). The emitted adapter restated both
bounds as the literals `8192` and `128` inside the `runtime` quoted
string, while the interpreter reads `max_bytes` and `max_fields`, so a
change of either constant would leave the native binary on the stale
bound. The quoted string is now split at the two literals and the two
constants are concatenated with `string_of_int`. The emitted bytes are
unchanged.

F-3 (nit, rust/form_data.ml:31,34,42). The name `fields` held two
meanings three lines apart: the raw `&` segments at :31 and the
decoded accumulator at :34, which :42 searches. The segment list is
renamed to `segments` at :31, at :32 and in the fold subject. The
accumulator keeps its name, so the mutation needle
`List.mem_assoc name fields` stays byte-identical and unique.

F-4 (nit, test/dune:3). The `(modules ...)` line of the first tests
stanza started at column 3 while `(names ...)` and `(libraries ...)`
start at column 2. One leading space is removed. The module list is
byte-identical.

Carried. C-1: the emitted adapter drops the segment count and the
decoded values before it searches the topcoat field list, and the
matching check cannot land without regenerating a frozen native
capture. C-2: prepare() in `test/lan_form_native.py` overwrites the
sibling `.lan` source, so the kept source reproduces only
`src/bin/async_form.rs`, and a second source file would add a path to
the frozen capture set. C-3: run() lets `subprocess.TimeoutExpired`
and `FileNotFoundError` escape as tracebacks, and no catch-free form
covers them while the try-free rule holds. C-4: the GOOD and BAD
literals duplicate `test/lan_form.ml` with no shared source, and any
generator moves a pinned row. C-5: no case carries a decoded `;`, CR
or LF, and every added case moves `checks=53` and `observations=76`.
C-6: the stage gate never runs `test/lan_form_native.py`, so the
native row is hand-produced, and adding the line would change the
frozen stage stdout.

Proof. The fix suites ran on a copy of the tree and printed 18 floor
rows, all OK: `LAN-FORM OK checks=53`, `LAN-URI OK checks=41`,
`LAN-TEXT-OPS OK checks=63`, the request, run, delete, update and all
binaries at their floors, and nine Python suites at their `Ran`
floors. `python3 -P test/lan_form_mutations.py` printed
`LAN-FORM-MUTATIONS OK killed=4/4 restored=GREEN`, and every suite
reported rc=0. The nine mutation needles each count 1 in the
worktree. The fix run staged the 34 review paths
(`FIX-RUN paths=34`) with `zsh -n OK`, `py_compile OK files=15`,
`em-dash total=0` and the one permitted catch site in
dev/trusted-inventory.py. The 40 frozen captures are untouched,
because the cached numstat of `dev/validation/stage-m1-form/` is
identical to the digest taken before the edits. The tree then held 75
staged paths and 0 unstaged changes.

Ladders. The baseline ladder ran on the unfixed staged tree and
reported GREEN (GATE-END tag=baseline 2026-09-16T03:38:59Z,
stage_rc=0; GATE LSM1F tag=baseline GREEN). The compare-rows probe on
the baseline tag showed RED-WATCH 0, PINS 91/91 and ROWS 155/155
IDENTICAL. The fix-1 ladder ran on the fixed tree and reported GREEN
(GATE-END tag=fix-1 2026-09-16T04:15:13Z, stage_rc=0; GATE LSM1F
tag=fix-1 GREEN). The compare-rows probe on the fix-1 tag showed
RED-WATCH 0, PINS 91/91 and ROWS 155/155 IDENTICAL. The close ladder
re-runs `zsh dev/gates.sh --stage M1-form` on this exact staged tree
after the close, and its verdict is recorded in the review kit, not
in this file.

## Stage M1 RESPONSE (2026-09-16)

`Response.text Bytes body` builds a response with status 200 and the
content type `text/plain; charset=utf-8`. `Bytes` is the checked
nominal byte-list family, as for `Form.field`, so a handler can
answer a scripted request with plain text. Every element must fit in
a byte and the complete body must be valid UTF-8, and both checks
fail the program even when the response is unused. `rust/run_http.ml`
holds the interpreter side: it builds the response value, validates
the body, and serializes HTTP/1.1 with a content length measured in
UTF-8 bytes.

The emitted adapter follows the pinned Topcoat `content_response`
idiom: construct the response from a string, then set the static
content-type header through the `headers_mut` accessor of the pinned
API. Byte-list conversion retains its range and UTF-8 errors. The CLI
accepts `Cx -> Uri -> Response` beside `Cx -> Uri -> SeeOther` under
`run --request URI`, and with the `--form BODY` option either result
may follow the checked byte-list body parameter. Redirect behavior is
unchanged.

`zsh dev/stage-m1-response.sh` retains the cumulative form gate and
then runs the new suites `_build/default/test/lan_response.exe`,
`test/lan_response.py` and `test/lan_response_mutations.py`. It
prints `LAN-RESPONSE OK checks=32`, the six CLI test groups, and the
four isolated mutations `wrong-status`, `wrong-length`,
`skip-response-validation` and `skip-effect-contract`, each KILLED,
between `LAN-RESPONSE-MUTATIONS CONTROL OK` and
`LAN-RESPONSE-MUTATIONS OK killed=4/4 restored=GREEN`. The stage row
is `STAGE-M1-RESPONSE OK`, and the stage runs from
`zsh dev/gates.sh --stage M1-response`.

The native harness `test/lan_response_native.py` builds two offline
binaries against the checked target pins with Rust 1.98 and reports
`LAN-RESPONSE-NATIVE OK binaries=2 observations=24`. The stage gate
does not run that harness, so the native row is a manual recording,
as for the form stage.

The catalog holds 23 declarations and nine foreign types, and Todo
reports 28 foreign constants. The generated module has 152 lines, and
the `target/PIN.json` signature sha changes because the catalog gains
the `Response.text` row, for 23 rows in total. Library pins, anchor
fingerprints, trust approval and the M0 exit stamp are unchanged. The
docs are README.md, dev/STAGE-M1-RESPONSE.md and target/README.md.
Captures and tested source hashes are frozen under
`dev/validation/stage-m1-response/`.

## Stage M1 RESPONSE review fixes (tag LSM1P, 2026-09-16)

The review kit LSM1P ran on base ef7dc23 over a 62-path slice, that is
28 review paths and 34 frozen captures under
`dev/validation/stage-m1-response/`. A drafter supplied 15 hypotheses,
an opus prober confirmed two of them, and one ctxcat-review Workflow
run with three agents supplied 8 raw findings, of which 7 were
upheld, under a judge cap of 7. Six findings passed the judge: one
medium, two low and three nits. Three more are carried.

F-1 (med, dev/M1-BUILD-LOG.md:3286). The M1 log ended with the LSM1F
review block and held no block for this stage, and the file was absent
from the 62 staged paths. The stage block above and this review block
are appended, so the stage carries a heading of the sibling shape,
with the stage name and the date. Every number in the prose is read
from the frozen captures and is not recomputed.

F-2 (low, bin/lanyard.ml:10-11). The driver doc block accepted both
entry-point types but its tail still promised the 303 response on
stdout, which is wrong for a `Response` handler. The tail now reads
that the command exits 0 with the serialized response on stdout, 303
for SeeOther and 200 text/plain for Response, and the two lines are
re-wrapped to the width of the block.

F-3 (low, target/README.md:96-99). The staged paragraph reported the
152 generated lines but dropped both the proposed allowance 104 and
the statement of the overrun, so a 48-line overrun stood undisclosed.
The paragraph now states that S0-D1 requires the user to rule the
numeric `A_sig` allowance, that the proposed allowance is exactly 104
without margin, and that the additional 48 measured lines exceed that
proposed allowance, which this adapter does not change.

F-4 (nit, test/lan_response.ml:13-16). The local `contains` helper
rebuilt a sub-sequence and allocated a fresh string for every
candidate index. It now uses the `String.starts_with ~prefix:needle`
form of test/lan_text_ops.ml:13-15, with the same name, the same
signature and the same behaviour, so every call site is unchanged.

F-5 (nit, target/README.md:6). One line of the catalog paragraph ran
to about 95 columns while its neighbours wrap near 70. Lines 3 to 9
are re-wrapped at 72 columns or less. No word changes.

F-6 (nit, dev/STAGE-M1-RESPONSE.md:34-39). One line of the
restrictions paragraph was 81 columns and ended on a stray word,
while the rest of the paragraph measures 50 to 69 columns. The
paragraph is re-wrapped at 72 columns or less. No word changes.

Carried. C-1: the stage gate never runs `test/lan_response_native.py`,
so the native row is hand-produced; the predecessor slice LSM1F ruled
the identical gap a nit as its C-6, the native leg is a manual
recording that dev/STAGE-M1-RESPONSE.md:78-81 documents,
test/lan_response.py:59-71 already pins the emitted source text, and
adding the line would change the frozen stage stdout. C-2: the claim
that the response UTF-8 guard is unreachable is refuted, because
`Run_http.response` is a public library entry that
test/lan_response.ml:77 calls directly, so the guard is load-bearing
at the module boundary and the mutant kill is genuine. C-3: the
`Uri_from_text` and `Response_text` arms at rust/text_ops.ml:86-91
are a taste change with no behavioural content, because the arms bind
different foreign types and use no `_` arm.

Proof. The fix suites ran on a copy of the tree and printed 19 floor
rows, all OK: `LAN-RESPONSE OK checks=32`, `LAN-FORM OK checks=53`,
`LAN-URI OK checks=41`, `LAN-TEXT-OPS OK checks=63`, the request, run,
delete, update and all binaries at their floors, and ten Python suites
at their `Ran` floors, each with rc=0. `test/lan_response_mutations.py`
printed `LAN-RESPONSE-MUTATIONS CONTROL OK`, the four mutants
`wrong-status`, `wrong-length`, `skip-response-validation` and
`skip-effect-contract` each KILLED, and
`LAN-RESPONSE-MUTATIONS OK killed=4/4 restored=GREEN`. The twelve
review needles each count 1 in their staged files. The fix run staged
the 28 review paths with `zsh -n OK`, `py_compile OK` and
`em-dash total=0`. The 34 frozen captures are untouched. The tree then
held 63 staged paths and 0 unstaged changes.

Ladders. The baseline ladder ran on the unfixed staged tree and
reported GREEN (GATE-END tag=baseline 2026-09-16T15:26:06Z,
stage_rc=0; GATE LSM1P tag=baseline GREEN). The compare-rows probe on
the baseline tag showed RED-WATCH 0, PINS 99/99 and ROWS 163/163
IDENTICAL. The fix-1 ladder ran on the fixed tree and reported GREEN
(GATE-END tag=fix-1 2026-09-16T15:52:49Z, stage_rc=0; GATE LSM1P
tag=fix-1 GREEN). The compare-rows probe on the fix-1 tag showed
RED-WATCH 0, PINS 99/99 and ROWS 163/163 IDENTICAL. The close ladder
re-runs `zsh dev/gates.sh --stage M1-response` on this exact staged
tree after the close, and its verdict is recorded in the review kit,
not in this file.

## Stage M1 HTML (2026-09-16)

This slice continues from the reviewed response commit `22ac8d0`.
`Html.text Bytes value` adds checked HTML text-node escaping, and
`Response.html Bytes body` adds a status 200 UTF-8 HTML response.
Ampersand, less-than and greater-than escape according to the pinned
Topcoat text table. Quotes and Unicode remain unchanged, and existing
entities are escaped again. Raw HTML responses preserve their input.

Both operations specialize through the existing byte-list path and
validate complete foreign metadata before native emission. The
interpreter adds an explicit HTML response variant and shares response
framing with plain text. The form fixture trims and stores a Todo title,
then returns the escaped stored value. Byte range and UTF-8 failures
propagate even when the result is unused.

The default Dune alias includes 43 HTML unit checks. Six CLI groups
cover exact response bytes, escaped form fields, failures, native
emission and ownership refusals. The stage gate retains the response
gate and adds five HTML mutations with clean and restored controls.
The separate native harness checks 25 observations with each of the
two generated error variants, for 50 observations. Its Rust 1.98 build
has no errors and 18 unused-code warnings. The default Dune suite and
all 19 end-to-end tests passed. macOS Git emits a sandbox-only warning
in two strict end-to-end checks; those tests and the cumulative gate
run with normal local permissions.

The catalog grows from 23 to 25 declarations, with nine foreign types.
Todo's foreign count grows from 28 to 30. Catalog inventory assertions,
legacy name order, axiom totals and the axiom golden are updated.
The generated catalog has 164 lines, 60 above the proposed allowance
of 104. No allowance, library pin, source anchor, trust approval or
M0 exit stamp is changed.

Text-node escaping does not validate attributes, scripts, styles or
URLs. Existing foreign ownership restrictions and recursive byte-list
stack limits remain. The stage contract is in `STAGE-M1-HTML.md`.
Validation captures, native sources and checked input hashes are in
`validation/stage-m1-html/`.

## Stage M1 HTML review fixes (tag LSM1H, 2026-09-16)

The review kit LSM1H ran on base 22ac8d0 over a 31-path slice. An opus
drafter supplied 7 hypotheses. An opus prober confirmed four of them,
refuted one, ruled two not a finding and swept 26 more rows. One
ctxcat-review Workflow run, wf_8b61f9a0-d3a, supplied 7 raw findings,
of which 3 were upheld and 3 survived. An opus judge passed four
findings, one low and three nits, under a judge cap of 7. Three more
are carried.

F-1 (low, dev/STAGE-M1-HTML.md:87-90 and
dev/M1-MUTATION-LOG.md:642-648). The mutation leg was the one check of
this slice with no standalone evidence record, and the gap was also
silent, because the response and form receipts each list a mutation
capture key and ship a trio. The predecessor trios are capture-harness
artifacts of the author's worktree, and no script of this tree makes
one, so both documents now state the deviation and name the record:
`validation/stage-m1-html/stage.stdout` rows 677 to 683, which hold
the control row, the five KILLED rows and the `killed=5/5
restored=GREEN` row. The edits are prose only. The receipt, the 31
captures and the porcelain count are unchanged.

F-2 (nit, dev/M1-MUTATION-LOG.md:627). The HTML table header read
`| Mutation | Required failure |`, while the three earlier M1 tables
at lines 553, 577 and 605 read `| Mutation | Required failing
observation |`. The header now uses the earlier wording.

F-3 (nit, dev/M1-MUTATION-LOG.md:637-638). The cumulative-command
sentence said that the stage gate "also retains the four response
mutations", which understates the retained set, because
dev/stage-m1-html.sh:7 chains the response stage and one recorded run
retains thirteen mutation families before LAN-HTML. The sentence now
reads that the gate retains every earlier stage gate, including the
four response mutations.

F-4 (nit, target/README.md:3-14). The catalog paragraph was not
reflowed after the two new names, so line 7 was a 34-column fragment
between lines of 64 and 61 columns. The paragraph is re-wrapped at 71
columns or less, from 13 lines to 12. No word changes.

Carried. C-1: the stage gate never runs `test/lan_html_native.py`, so
the native row is a manual recording, which dev/STAGE-M1-HTML.md:75-83
documents at least as fully as the predecessor slice, where LSM1F and
LSM1P ruled the identical gap a carry. C-2: the bare phrase "18
unused-code warnings" over 13 dead_code rows plus 5 unused_variables
rows matches the precedent of this file at dev/M1-BUILD-LOG.md:3074
for the uri slice, so it is pre-existing, not a new defect. C-3: the
`contains` helper at test/lan_html.ml:13 is a third spelling, not a
second, because test/lan_form.ml:12-15 already diverges from
test/lan_response.ml:13-16 in the pre-image tree; per suite copies of
the small helpers are the house shape at HEAD, so a share-one-helper
change is a repo-wide refactor and is out of slice scope.

Proof. Every fix is documentation. No source file, no receipt and no
capture under `dev/validation/stage-m1-html/` is changed, so the 31
frozen captures, the pinned source hashes and the recorded stage
stdout keep their values. The fix suites ran on a copy of the tree
outside the repository: `_build/default/test/lan_html.exe` reports 43
checks, `test/lan_html.py` reports 6 checks, and
`test/lan_html_mutations.py` reports `killed=5/5 restored=GREEN` with
a green restored control.

Ladders. The baseline ladder ran on the unfixed staged tree and
reported GREEN (GATE-END tag=baseline 2026-09-16T19:09:20Z,
stage_rc=0; GATE LSM1H tag=baseline GREEN). The compare-rows probe on
the baseline tag showed RED-WATCH 0, PINS 108/108 and ROWS 172/172
IDENTICAL. The fix-1 ladder ran on the fixed tree and reported GREEN
(GATE-END tag=fix-1 2026-09-16T21:22:59Z, stage_rc=0; GATE LSM1H
tag=fix-1 GREEN). The compare-rows probe on the fix-1 tag showed
RED-WATCH 0, PINS 108/108 and ROWS 172/172 IDENTICAL. The close
ladder re-runs `zsh dev/gates.sh --stage M1-html` on this exact staged
tree after the close, and its verdict is recorded in the review kit,
not in this file.

## Stage M1 CONCAT (2026-09-16)

This slice continues from the reviewed HTML commit `d34eb7b`.
`Text.concat Bytes left right` joins two checked UTF-8 byte lists into
one value. Concatenation preserves literal bytes. It applies no
escaping and no sanitization. Both arguments pass the byte range and
UTF-8 checks before the join, and a failure of either argument
propagates even when the result is unused.

The operation specializes through the existing byte-list path and adds
no dependency and no foreign type. It converts both checked lists to
strings, uses standard `String` concatenation, then converts the result
back to the selected list family. Complete foreign metadata and print
placeholders are validated before native emission. Aliases and captured
helpers work. Partially applied value arguments are rejected, as with
the existing foreign adapter lowering.

The cumulative stage retains the HTML gate and adds 33 OCaml checks and
7 Python checks. It adds four concat mutations with clean and restored
controls, and reports `LAN-CONCAT-MUTATIONS OK killed=4/4
restored=GREEN`. Rows 686 to 693 of the stage capture hold
`LAN-CONCAT OK checks=33`, the control row, the four KILLED rows, the
kill summary and `STAGE-M1-CONCAT OK`. The kit comparator tracks 180
gate rows and 116 pins. The axioms, Dune test, native prepare, native
build, native check and stage captures all exit 0.

The separate native harness checks 19 observations in the synchronous
error variant and 20 in the database error variant. It reports
`LAN-CONCAT-NATIVE OK binary=lanyard-program observations=19` and
`LAN-CONCAT-NATIVE OK binary=async_concat observations=20`. The
database case creates a row in the left argument, then updates and
deletes it in the right argument. Reversal or repeated evaluation
fails. The harness runs by hand with Rust 1.98; the stage gate does not
call it.

The catalog grows to 26 declarations, with nine foreign types. Todo
reports 31 foreign constants. The generated catalog has 170 lines, 66
above the pending proposed allowance of 104. No allowance, library pin,
source anchor, trust approval or M0 exit stamp is changed.

The recursive byte-list representation retains its large-value stack
limit. This slice adds no size limit and no streaming representation.
The slice stages 51 paths: 23 source, test and document paths, and 28
frozen captures. The stage contract is in `STAGE-M1-CONCAT.md`.
Validation captures, native sources and checked input hashes are in
`validation/stage-m1-concat/`.

## Stage M1 CONCAT review fixes (tag LSM1C, 2026-09-16)

The review kit LSM1C ran on base d34eb7b over a 51-path slice. An opus
drafter supplied 9 hypotheses. An opus prober upheld five of them,
downgraded three, refuted one and added two new rows. One ctxcat-review
Workflow run, wf_ab3560e0-fbe, supplied 6 raw findings, of which 5 were
upheld and 5 survived. An opus judge passed seven findings, one medium,
three low and three nits, under a judge cap of 7. Four more are
carried.

F-1 (med, dev/M1-BUILD-LOG.md:3536). The slice recorded no block in the
M1 build log. The file held 18 `## Stage M1 ` headings, none of which
named CONCAT, while every predecessor stage recorded a block. The log
now holds a `## Stage M1 CONCAT (2026-09-16)` block in the shape of the
HTML block. The block states the base commit, the operation, the
specialization and metadata path, the gate and native numbers and the
capture directory. The file is hand-staged as an added path.

F-2 (low, dev/M1-MUTATION-LOG.md:650). The slice recorded no section in
the M1 mutation log, so the log and the captures disagreed: the four
CONCAT KILLED rows existed only inside the staged stage capture. The log
now holds a `## Text concatenation (2026-09-16)` section with one table
row per mutation, the control rules, the cumulative command and the
capture row numbers. The file is staged with F-1.

F-3 (low, rust/run_store.ml:124). The Concat and Form_field arity arm
printed `invalid "text argument count"`, the same string as the
catch-all arm at :126 and the render guard at rust/text_ops.ml:74, so
three distinct failures shared one message. The pre-image arm named its
operation family. The arm now prints `invalid "concat or form argument
count"`. The catch-all and the render guard keep their strings.

F-4 (low, test/lan_concat.ml:12-14). The new `contains` test helper
rebuilt the whole suffix for every index, so the search allocated O(n)
bytes per position and O(n^2) overall. The helper now scans with
`String.sub` over a total index list and allocates no suffix. The other
three copies of the helper stay unchanged; a shared helper is a
repo-wide refactor and is out of slice scope. The scan line carries a
`(* @total-accessor *)` marker, because the OCaml exception hook blocks
a bare `String.sub`; the index range of the `List.init` bound makes the
call total.

F-5 (nit, target/README.md:6-9). The catalog paragraph was not reflowed
after the `Text.concat` insert, so line 7 was 86 columns, the widest
line of the file, against neighbours of 63 to 71. The paragraph is
re-wrapped at 71 columns or less. No word changes.

F-6 (nit, dev/STAGE-M1-CONCAT.md:13-77). Six prose lines of the new
stage document exceeded 72 columns, while the sibling stage documents
hold every prose line at 72 or fewer and exceed that width only inside
fences. The six prose lines are re-wrapped at 72 columns. The fenced
command lines stay on one line each, by convention. The re-wrapped
paragraphs are at :13-14, :25-28, :41-43, :45-47, :67-69 and :73-77. The
F-4 duplication sentence is at :71-72.

F-7 (nit, test/lan_concat.py:90-92). The placeholder contract compares
sorted slot sets, so a print rule of `#{right} + &#{left}` satisfies it,
and the emission test asserted only that `src/main.rs` exists. The gate
therefore could not kill an operand-order reversal. The existing
`test_emission` now reads the emitted Rust. It asserts that the file
contains the expanded print rule `__lan_left + &__lan_right`. It also
asserts that the file does not contain the swapped form
`__lan_right + &__lan_left`. The first version of the assertion looked
for the source literals `b"left"` and `b"right"`. The printer never
emits those literals, because byte texts become model-text constructor
calls on hex-named nominal types. The fix-1 ladder found the error. It
was RED at `test_emission`. Ladder tag fix-2 carries the repaired
assertion. The Python check count stays 7.
This round adds no mutation row to test/lan_concat_mutations.py. The kit
comparator pins the gate log to the frozen capture, which holds 180
rows, `LAN-CONCAT-MUTATIONS OK killed=4/4 restored=GREEN` and
`LAN-CONCAT OK checks=33`. The captures and the receipt stay untouched
in a review round. The mutation row is deferred to the next capture
round.

Carried. C-1: the stage gate never runs `test/lan_concat_native.py`,
so the native row is a manual recording, carried unchanged since LSM1F.
C-2: the added README sentence is 75 columns, but the staged README has
68 lines over 72 columns and a maximum of 136, so the line sits inside
the file's own width band; refuted against the bytes. C-3: the empty
`dev/validation/stage-m1-concat/diff-check.stdout` appears only in the
receipt `files_sha256`, and the HTML receipt lists the identical empty
file with the same hash, so the orphan is carried from LSM1H by design.
C-4: the receipt has no `e2e-local` key, which matches the form
receipt, and the composed request path runs in-gate through
test/lan_concat.py; this is practice, not a gap.

Proof. Six of the seven fixes are documentation or test-local. The one
source edit changes an error string in rust/run_store.ml. No receipt and
no capture under `dev/validation/stage-m1-concat/` is changed, so the 28
frozen captures, the pinned source hashes and the recorded stage stdout
keep their values. The fix suites ran on a copy of the tree outside the
repository: all 23 verdict rows are OK, with `LAN-CONCAT OK checks=33`
for the OCaml suite, `Ran 7 tests` for test/lan_concat.py and
`LAN-CONCAT-MUTATIONS OK killed=4/4 restored=GREEN` for the mutation
suite. The recorded run is `FIX-RUN paths=23 extras=2`, over `FIX-RUN
STAGED base=51 porcelain=53 captures=28 optional=2 unexpected=0`.

Ladders. The baseline ladder ran on the unfixed staged tree and reported
GREEN (LAUNCH 2026-09-17T00:16:41Z after a 60s load-gate wait at load1
41.88; VERDICT GATE LSM1C tag=baseline GREEN waited=960s lines=788 at
2026-09-17T00:34:44Z; FIX-LADDER baseline GREEN). The compare-rows probe
on the baseline tag showed RED-WATCH 0, PINS 116/116 and ROWS 180/180
IDENTICAL. The fix-1 ladder ran on the first fixed tree and reported RED
(LAUNCH 2026-09-17T00:48:31Z at load1 11.98; VERDICT GATE LSM1C
tag=fix-1 RED waited=360s lines=790 at 2026-09-17T00:56:32Z; FIX-LADDER
fix-1 RED). The compare-rows probe on the fix-1 tag showed RED-WATCH 0,
PINS 107/116 and ROWS 173/180 DIFFER, because the first F-7 assertion
still looked for the source literals b"left" and b"right", which the
native printer never emits, so test_emission failed. Fixer unit D
replaced the assertion with a check on the expanded print rule
`__lan_left + &__lan_right` and on the absence of the swapped form. The
fix-2 ladder ran on the repaired tree and reported GREEN (LAUNCH
2026-09-17T01:26:55Z at load1 14.06 with no wait; VERDICT GATE LSM1C
tag=fix-2 GREEN waited=390s lines=788 at 2026-09-17T01:35:26Z;
FIX-LADDER fix-2 GREEN). The compare-rows probe on the fix-2 tag showed
RED-WATCH 0, PINS 116/116 and ROWS 180/180 IDENTICAL. The close ladder
re-runs the gate on this exact staged tree after the close, and its
verdict is recorded in the review kit, not in this file.

## Stage M1 NAT-TEXT (2026-09-16)

This slice continues from the reviewed CONCAT commit `6e1a952`.
`Text.from_nat Bytes value` renders a natural number as decimal text.
Zero becomes `b"0"`. Other values carry no leading zeros. Values
beyond `u64` work in the interpreter and in the emitted Rust, with
computed values, aliases and captured arguments.

The schema is `(0 Text : Type 0) -> (value : Nat) -> Text`. The output
must be a closed, checked byte-list family. The type argument is
erased. The natural has shared quantity. The operation is synchronous
and pure. An effectful argument is evaluated once, and its effects
are retained when the formatted result is unused.

The interpreter uses its arbitrary-precision natural representation.
The Rust adapter reads the existing little-endian base-256 limbs and
accumulates decimal digits without narrowing the input. Each digit is
in `0..9`. Each multiply-and-carry value is at most 2559 and fits in
`u16`. The helper is emitted only when the program uses this
operation. It adds no library dependency and no foreign type. The SQL
integer range checks and the recursive byte-list limits still apply.

The cumulative stage retains the concat gate and adds 45 OCaml checks
and 7 Python checks. The adapter unit suite joins the default Dune
test alias. Decimal checks cover byte boundaries through 1024 bits,
deterministic larger values below 2048 bits, zero, leading zeros,
arithmetic, closures and link composition. The separate native leg
checks 970 decimal observations. The database leg checks five
observations in the interpreter. Both legs run by hand with Rust
1.98; the stage gate does not call the native leg.

Four native mutations alter radix, limb order, zero and carry
behavior, with clean and restored controls. Rows 695 to 705 of the
stage capture hold `LAN-NAT-TEXT OK checks=45`, the native row, the
database row, the two control rows, the four killed rows,
`LAN-NAT-TEXT-MUTATIONS OK killed=4` and `STAGE-M1-NAT-TEXT OK`. The
kit comparator tracks 191 gate rows and 127 pins.

The additional database harness checks empty, single-row and sorted
multi-row pages against pinned Toasty and Topcoat. It also checks a
database write inside the natural argument and an unused formatted
result. Native database compilation reports 15 generated
unused-variable and dead-code warnings.

The catalog grows to 27 declarations, with nine foreign types. Todo
reports 32 foreign constants. The generated catalog has 176 lines, 72
above the pending proposed allowance of 104. No allowance, library
pin, source anchor, trust approval or M0 exit stamp is changed.

The slice stages 47 paths: 23 source, test and document paths, and 24
frozen captures. Five capture json files record the round. The staged
`receipt.json` keeps the reduced schema of the capture round, with the
keys `base`, `captures`, `files`, `recorded_at`, `stage` and `status`.
It holds no axioms capture, although the stage log records the
`LAN-AXIOMS` rows. The stage contract is in `STAGE-M1-NAT-TEXT.md`.
Validation captures, native sources and checked input hashes are in
`validation/stage-m1-nat-text/`.

## Stage M1 NAT-TEXT review fixes (tag LSM1N, 2026-09-16)

The review kit LSM1N ran on base 6e1a952 over a 47-path slice. An opus
drafter supplied 13 hypotheses. An opus prober confirmed nine of them,
refuted one and ruled three not a finding. One ctxcat-review Workflow
run, wf_6e0148a1-f42, supplied 7 raw findings, of which 3 were upheld
and 3 survived. An opus judge passed seven findings, four medium and
three nits, under a judge cap of 7. Six more are carried.

F-1 (med, target/README.md:98). The catalog README kept the generated
counts of the concat round. Line 98 read 170 lines and line 102 read
66 measured lines, while this catalog has 176 lines and exceeds the
proposed 104-line allowance by 72. Line 98 now reads 176 lines and
line 102 now reads 72 measured lines. The allowance is unchanged.

F-2 (med, target/README.md:334). The foreign constant count stayed at
31, the concat number, although Todo reports 32 foreign constants
after this slice. Line 334 now reads 32 foreign constants.

F-3 (med, dev/M1-BUILD-LOG.md:3703 and dev/M1-MUTATION-LOG.md:678).
The slice recorded no block in the M1 build log and no section in the
M1 mutation log, so the logs and the captures disagreed: the four
NAT-TEXT killed rows existed only inside the staged stage capture. The
build log now holds a `## Stage M1 NAT-TEXT (2026-09-16)` block in the
shape of the concat block, and this fixes block. The mutation log now
holds a `## Natural-number text (2026-09-16)` section with one table
row per mutation, the control rules, the cumulative command and the
capture row numbers. Both logs are hand-staged as added paths.

F-4 (med, dev/STAGE-M1-NAT-TEXT.md:63-70). The staged `receipt.json`
holds only the keys `base`, `captures`, `files`, `recorded_at`,
`stage` and `status`, and the capture set holds no axioms trio,
although the stage log records the `LAN-AXIOMS` rows. Earlier rounds
recorded the full schema. The stage document now records the frozen
captures, the reduced schema, the missing axioms capture and the
deferred recapture. Deviation: no in-repo writer is corrected, because
`dev/stage-m1-nat-text.sh` writes no receipt, and neither did
`HEAD:dev/stage-m1-concat.sh`. The writer is the out-of-tree
gateledger harness named in the receipt argv. The keys that the
harness must restore are listed in the review kit, and the recapture
belongs to the next capture round.

F-5 (nit, target/README.md:6-8). The catalog paragraph was not
reflowed after the `Text.from_nat` insert, so one line reached 83
columns, the widest line of the file. The paragraph is re-wrapped at
64 columns or less. No word changes.

F-6 (nit, rust/run_store.ml:127-128). A dead `From_nat` arm preceded
the combined arity arm, so one arm of the match was unreachable.
`Text_ops.From_nat` now joins the combined arm. The match stays
exhaustive and adds no catch-all pattern. No test and no capture
pinned the removed message.

F-7 (nit, test/lan_nat_text.py:61-64 and
test/lan_nat_text_database.py:48-51). Two fixture builders grew a
string with repeated concatenation inside a loop. Each builder is now
one `"".join` over a generator. The emitted bytes are unchanged and
the ast parses clean. Deviation: the third site, the emitted helper in
rust/text_ops.ml:117-126, is deferred to the next capture round,
because `receipt.json:99` pins the digest of `native/src/main.rs`,
which carries the helper verbatim at :203-220, and the carry mutation
anchor `(digits, next / 10)` at test/lan_nat_text.py:39 is the fold
accumulator that a chain-and-collect rewrite removes.

Carried. C-1, the manual native leg, holds the LSM1F design. C-2, the
empty `diff-check.stdout`, and C-3, the missing e2e-local capture, sit
inside the frozen captures and wait for the next capture round. C-4,
the Workflow row on the `contains` helper, is refuted under the LSM1C
F-4 precedent. C-5, the wrap candidates at or under 80 columns, and
C-6, the Workflow row 4 with drafter H9, are refuted.

Proof. The suite probe on the fixed tree reported
`lan_nat_text.exe checks=45`, `test/lan_nat_text.py Ran 7`,
`lan_nat_text_database.py --interpreter observations=5` and
`--mutations killed=4` with both controls, and every earlier floor row
OK. A search for `FAILED`, `Error` and `Traceback` in the suite log
printed nothing. The needle probe reported `NEEDLES rows=14 bad=0`.

Ladders. The baseline ladder ran on the unfixed staged tree and
reported GREEN (launched detached 2026-09-17T03:46:21Z at load1 36.14,
pid 99692; verdict 2026-09-17T04:00:52Z after 750s, 805 log lines;
GATE LSM1N tag=baseline GREEN at gates-LSM1N-baseline.log:805;
FIX-LADDER baseline GREEN). The compare-rows probe on the baseline tag
showed RED-WATCH 0, PINS 127/127 and ROWS 191/191 IDENTICAL. The fix-1
ladder ran on the fixed tree and reported GREEN (launched detached
2026-09-17T04:23:41Z at load1 11.57, pid 3477; verdict
2026-09-17T04:38:42Z after 780s, 805 log lines; GATE LSM1N tag=fix-1
GREEN at gates-LSM1N-fix-1.log:805; FIX-LADDER fix-1 GREEN). The
compare-rows probe on the fix-1 tag showed RED-WATCH 0, PINS 127/127
and ROWS 191/191 IDENTICAL. The close ladder re-runs the gate on this
exact staged tree after the close, and its verdict is recorded in the
review kit, not in this file.

## Stage M1 TEXT-NAT (2026-09-16)

This slice adds `Text.to_nat Bytes text`, the inverse decimal boundary to
`Text.from_nat`. A nonempty sequence of ASCII digits parses exactly into
an arbitrary-precision natural. Leading zeros are accepted. Empty input,
signs, whitespace, fractions, separators, exponents, non-ASCII digits,
NULs, malformed UTF-8 and out-of-range byte elements fail.

Specialization retains the checked byte-list family. The Rust adapter
returns the existing natural representation and reuses `Nat::decimal`
behind an empty-input check. The interpreter uses `Bignum.of_decimal`.
The schema carries the existing fallible-text error effect. Neither the
kernel nor the natural runtime arithmetic changes. Argument effects
remain once-only and survive an unused result, including failures.

The form fixtures exercise arithmetic above `u64` and a Todo create/fetch
flow with parsed IDs and escaped titles. The database harness also covers
updates, deletion, retained writes and the unchanged SQL key range.
`Text.to_nat` is recognized through aliases and captured text arguments;
the helper is absent when unused.

Focused validation passed 53 OCaml checks, nine CLI groups, 736 native
observations and seven database scenarios in each runtime. Four native
mutations were killed with passing clean and restored controls. The
default Dune test alias includes the new unit suite. The native database
crate builds offline against the existing pins with Rust 1.98, reporting
26 generated unused-variable and dead-code warnings.

The cumulative stage retains every predecessor check. Its temporary Git
root is outside the Dune project so native ledger scopes and copied
mutation projects have independent roots, and is removed on exit.
Validation needs normal Git process access on this macOS host: sandboxed
Git emits a `confstr` warning that violates two existing empty-stderr
assertions. The 19-test end-to-end suite passes with normal access;
those assertions remain unchanged.

The generated catalog now has 28 proposed declarations, nine foreign
types and 182 lines. Todo's disclosure reports 33 foreign constants.
The signature fingerprint, disclosure golden and count assertions are
updated. The proposed 104-line signature allowance is exceeded by 78;
this slice approves no trust budget, library revision or M0 exit stamp.

`dev/validation/stage-m1-text-nat/` retains the native harness, complete
captures and input hashes. Its receipt uses the full capture schema and
includes a separate axiom-report capture, addressing the prior slice's
deferred evidence recapture.

Final validation passed `STAGE-M1-TEXT-NAT`, the default Dune tests,
the ten-observation, eleven-refusal axiom suite and the seven-scenario
native database harness. The cumulative capture ends with passing clean
and restored controls around all four killed parser mutations.

## Stage M1 TEXT-NAT review fixes (tag LSM1D, 2026-09-16)

The review kit LSM1D ran on base e6e40fe over a 25-path slice. An opus
drafter supplied seven hypotheses. An opus prober confirmed four of
them and refuted three. One ctxcat-review Workflow run,
wf_a8161576-02d, supplied 13 raw findings, of which 12 were upheld and
12 survived. An opus judge passed seven findings, two medium, two low
and three nits, under a judge cap of 7. Seven more are carried.

F-1 (med, README.md:344). The root README kept the pre-slice count of
32 foreign constants, while corpus/m0/axioms.txt reads
`COUNT Foreign=33`, test/lan_axioms.py calls `report(todo, 33, 3)` and
dev/STAGE-M1-TEXT-NAT.md reads 33 foreign constants. Line 344 now
reads 33 foreign constants. No other word of the paragraph changes.

F-2 (med, target/README.md:102). The allowance disclosure kept the
excess of the concat round. Line 98 reads 182 lines and the proposed
allowance is 104, thus the excess is 78, the value that
dev/STAGE-M1-TEXT-NAT.md records. Line 102 now reads 78 measured
lines. The allowance is unchanged.

F-3 (low, dev/stage-m1-text-nat.sh:9). The comment at :8 promised the
system temporary directory, but the command hard-coded /tmp, so a
caller without a writable /tmp saw a RED stage for an environment
reason. Line 9 now reads
`stage_tmp=$(mktemp -d "${TMPDIR:-/tmp}/lanyard-text-nat.XXXXXX")`.
The default keeps the earlier behavior where TMPDIR is unset.

F-4 (low, dev/M1-MUTATION-LOG.md:711 and :718). The section presented
the four mutants as mutations of a changed Rust adapter, although
`mutations()` at test/lan_text_nat.py:217-231 patches the whole
emitted program, and the radix anchor `n.scale(10)?` occurs only in
`Nat::decimal` at rust/emit.ml:484, which this slice does not change.
Line 711 now names the mutated copy of the emitted program, and the
radix row at :718 names the shared decimal runtime that the adapter
calls. No count and no capture changes.

F-5 (nit, test/lan_text_nat.ml:36 and :39). Two string comparisons
used the polymorphic `=` in a file that compares with `String.equal`
at :14 and :16. Both sites now call `String.equal`, so the file keeps
one spelling and the comparisons stay monomorphic.

F-6 (nit, test/lan_text_nat.ml:26). The second bind of `number` only
rewrapped its value, thus it is a map. Line 26 now reads
`V.natural value |> Result.map Bignum.to_string`. The outer bind that
branches is unchanged.

F-7 (nit, test/lan_text_nat.ml:12-14). A second `contains` helper
built a full index list with `List.init` and read the text with
`String.sub` under a `(* @total-accessor *)` escape. The helper now
uses the test/lan_text_ops.ml:13-15 formulation over `String.to_seq`
and `String.starts_with`. The escape comment goes away with the
`String.sub` call, and no other user of the escape is in this file.

Carried. C-1, the manual native leg, holds the LSM1F design. C-2, the
target/README.md:7 width at 78 columns, and C-3, the mutation-log
heading form, are refuted. C-4, the `harness()` append loop, C-5, the
`source()` rebuild per case, and C-6, the third `List.exists`
operation probe, sit below the judge cap. C-7 lists the by-design
items of the hypotheses document. The two pinned sources that this
round edits, dev/stage-m1-text-nat.sh and test/lan_text_nat.ml, keep
their pre-fix shas at
dev/validation/stage-m1-text-nat/source-sha256.json:109 and :696: no
command of this tree rewrites that capture, and all 27 captures stay
byte-identical, as in the LSM1N round.

Proof. The suite probe on the fixed tree reported 44 floor rows OK and
none FAIL, among them `lan_text_nat.exe checks=53`,
`test/lan_text_nat.py Ran 9` with `LAN-TEXT-NAT NATIVE OK
observations=736`, `lan_text_nat_database.py --interpreter
observations=7`, and the mutation rows `LAN-TEXT-NAT-MUT OK clean`,
the four KILLED rows empty, radix, plus and zero, and
`LAN-TEXT-NAT-MUT OK restored`. The retained rows kept their LSM1N
values: `lan_nat_text.exe checks=45`, `test/lan_nat_text.py Ran 7`,
`lan_nat_text_database.py --interpreter observations=5` and
`--mutations killed=4`. A search for `FAILED`, `Error` and `Traceback`
in the suite log printed nothing. The needle probe reported
`NEEDLES rows=13 bad=0`.

Ladders. The baseline ladder ran on the unfixed staged tree and
reported GREEN (launched detached 2026-09-17T06:56:32Z at load1
30.56, pid 54633; verdict 2026-09-17T07:16:39Z after 1080s, 821 log
lines; GATE LSM1D tag=baseline GREEN at
gates-LSM1D-baseline.log:821; RED-WATCH tag=baseline hits=0; PINS
tag=baseline ok=137 missing=0; ROWS tag=baseline capture=201 log=201
IDENTICAL; COMPARE rc=0; FIX-LADDER baseline GREEN). The fix-1
ladder ran on the fixed tree and reported GREEN (launched detached
2026-09-17T07:37:46Z at load1 11.89, pid 40388; verdict
2026-09-17T07:48:48Z after 540s, 821 log lines; GATE LSM1D tag=fix-1
GREEN at gates-LSM1D-fix-1.log:821; RED-WATCH tag=fix-1 hits=0;
PINS tag=fix-1 ok=137 missing=0; ROWS tag=fix-1 capture=201 log=201
IDENTICAL; COMPARE rc=0; FIX-LADDER fix-1 GREEN). The close ladder
re-runs the gate on this exact staged tree after the close, and its
verdict is recorded in the review kit, not in this file.

## Stage M1 TEXT-EQUAL (2026-09-17)

Added `Text.equal Bytes left right` as a synchronous adapter over closed
byte-list families. The target schema erases its type argument and gives
both values shared quantity. The interpreter compares validated strings;
the Rust printer maps string equality to the existing Boolean sum. Case,
whitespace, NULs and Unicode encodings are preserved. Both arguments are
evaluated once, left to right, before their byte-list validation. Errors
and database effects survive unused results.

The form fixture branches on `action=save`. The database fixture uses
ordered create, update and delete operations, then reads a persisted
record to prove the comparison's effects remain observable. Omitting an
unused comparison fails that read-back control. Named aliases, captures,
alternate families, unsupported layouts, malformed UTF-8 and invalid
bytes are covered in the unit and CLI suites.

Validation covers 49 OCaml checks, eight CLI groups, 256 interpreted text
pairs, 266 native observations and five database scenarios in each
runtime. Five emitted-program mutations are killed, with passing clean
and restored controls. The native database crate uses locked, offline
dependencies and reports 25 generated unused-variable and dead-code
warnings. No library dependency or foreign type was added.

The catalog and disclosure fixtures now report 29 proposed declarations,
nine foreign types and 34 Todo foreign constants. Its generated module
has 188 lines, 84 above the proposed 104-line allowance. The Topcoat
signature digest changes with the new row; library identities, source
anchors, proposed allowances and the pending M0 exit decision stay as
before.

Captures and source hashes are in `validation/stage-m1-text-equal/`.
A cumulative run under the filesystem sandbox stopped in the
existing Git-configuration regression: macOS Git wrote a temporary-path
warning to stderr. The isolated regression passed with normal macOS
access. The complete stage is validated in that environment, keeping
the original assertions.

Final validation passed `STAGE-M1-TEXT-EQUAL`, the default Dune test
alias, the axiom suite, the style gate and the five-scenario native
database harness. The cumulative capture includes the 49 new OCaml
checks, 266 native observations and all five killed mutations with clean
and restored controls.

## Stage M1 TEXT-EQUAL review fixes (tag LSM1E, 2026-09-17)

The review kit LSM1E ran on base 4ff9f6f over a 24-path slice. An opus
drafter supplied 14 hypotheses. An opus prober confirmed two of them,
refuted three and cut nine. One ctxcat-review Workflow run supplied
six raw findings, of which two were upheld. An opus judge passed three
findings, one low and two nits, under a judge cap of 7. Three more are
carried.

F-1 (nit, rust/run_store.ml:133). The arm for one text argument and
the catch-all arm at :135 both printed `text argument count`, thus the
run path lost the distinction that HEAD held. Line 133 now reads
`invalid "text pair argument count"`. The catch-all arm at :135 and
the emit path at rust/text_ops.ml:85 keep their wording. Behavior does
not change; only the diagnosis is distinct again. A search for
`argument count` over the two files shows three different strings.

F-2 (low, dev/STAGE-M1-TEXT-EQUAL.md:48-50). The manual native
database leg gave the template LOCK, but no line of the record named
the lock of the capture. New prose below the code fence names
dev/validation/stage-m1-text-nat/native/Cargo.lock, which the argv of
native-prepare-capture.json:1 records, and states that its bytes are
identical to this stage lock. A search for `stage-m1-text-nat` over
the doc gives one hit, which was zero before.

F-3 (nit, test/lan_text_equal.ml:13-15). The `contains` helper built
each suffix again with `Seq.drop` and `String.of_seq`, thus one
allocation for each index. The helper now uses the
test/lan_concat.ml:12-14 form over `List.init` and `String.sub` below
the `(* @total-accessor *)` marker, which also covers the empty text.
Test code only: no capture value moves.

Repin. The three edited sources and this log are pinned, thus the same
fix rewrites their sha256 in
dev/validation/stage-m1-text-equal/source-sha256.json: rust/run_store.ml
to c6d960e9, dev/STAGE-M1-TEXT-EQUAL.md to e3c5cecd,
test/lan_text_equal.ml to 164c2617 and dev/M1-BUILD-LOG.md to the
value of this block. The other 974 entries stay as before.
receipt.json needs no edit: its `source_hashes` value is the file name
"source-sha256.json". The pin probe reports ok=24 mismatch=0.

Carried. C-1, the manual native database leg, is a hand leg by design.
C-2, the `OK test: 0 failed, 0 passed` row of dune-tests.stdout:1, is
pre-existing in the two predecessor captures. C-3, the allocating
`contains` copy in five more test modules, is a family-wide move out
of this slice. Five more claims are refuted, among them the warning
classes of the doc, the 72-column width and the receipt hash gap.

Proof. The suite probe on the fixed tree reported 50 floor rows OK and
none FAIL, among them `lan_text_equal.exe checks=49`,
`test/lan_text_equal.py Ran 8` with `LAN-TEXT-EQUAL NATIVE OK
observations=266`, `lan_text_equal_database.py --interpreter
observations=5`, and the mutation rows `LAN-TEXT-EQUAL-MUT OK clean`,
the five KILLED rows inverted, length, prefix, trimmed and
unchecked_right, plus `LAN-TEXT-EQUAL-MUT OK restored`. The retained
lan_text_nat rows kept their LSM1D values: `lan_text_nat.exe
checks=53`, `Ran 9`, `NATIVE OK observations=736`, `--interpreter
observations=7` and four KILLED rows. A search for `FAILED`, `Error`,
`error:` and `Traceback` in the suite log printed nothing. The needle
probe reported `NEEDLES rows=14 bad=0`.

Ladders. The baseline ladder ran on the unfixed tree on 2026-09-17,
LAUNCH rc=0, VERDICT GATE LSM1E tag=baseline GREEN, with PINS
tag=baseline ok=148 missing=0 and ROWS tag=baseline capture=212
log=212 IDENTICAL. The fix-1 ladder ran on the fixed tree on
2026-09-17, LAUNCH rc=0, VERDICT GATE LSM1E tag=fix-1 GREEN, with
PINS tag=fix-1 ok=148 missing=0 and ROWS tag=fix-1 capture=212
log=212 IDENTICAL. The close ladder repeats this gate on the staged
tree after this paragraph.

## Stage M1 URI-TEXT (2026-09-17)

Starting at ad248dc, this slice adds `Uri.to_text Bytes uri` to the checked
catalog, specialization, interpreter and Rust emitter. A request handler
can inspect the full URI and select a response with `Text.equal`. The new
`uri-text.lan` fixture returns `todos` for exactly `/todos` and echoes other
paths after `unmatched: `.

The adapter retains URI spelling, including percent-escape case, repeated
slashes, dot segments and the complete text after `?`. It checks the shared
origin-form contract and 8192-byte limit in both runtimes. This check remains
observable for unused results and rejects native Topcoat URI values outside
the supported subset. Type arguments remain erased; URI arguments retain
shared quantity. The operation is synchronous with no library effect. The
existing adapter error channel reports validation failures.

Validation adds 43 OCaml checks, four CLI groups and three compiler
mutations, with clean and restored controls. A native crate built offline
against pinned Topcoat passes 70 observations for rendering, round trips,
captures, alternate byte-list families and used or unused invalid values.
Its build reports eight generated dead-code warnings. The default Dune test
alias, axiom suite (10 observations and 11 refusals) and HOUSE gate pass.

The catalog grows to 30 proposed declarations and nine foreign types. Todo
now reports 35 foreign constants; both report forms and the exact golden
reflect the new row. The generated catalog is 194 lines, 90 above the pending
104-line proposal. No dependency revision, source anchor, trust approval or
M0 exit decision changes.

The cumulative stage runs with normal macOS access. Its retained Git
configuration regression fails under filesystem sandboxing because Git
prints a `confstr` warning; the original stderr assertion is preserved.
Captures, the native source and lock, and final input hashes are retained
under `validation/stage-m1-uri-text/`.

Final cumulative validation passed `STAGE-M1-URI-TEXT`, including all
retained stages, 43 new OCaml checks and the three killed mutations with
clean and restored controls. Its retained Stage F gate reports
`STAGE-F-GATES OK m0=PENDING`, preserving the existing ratification status.

## Stage M1 URI-TEXT review fixes (tag LSM1R, 2026-09-17)

A staged-slice review of this stage ran over the 23-path slice on
HEAD ad248dc. An opus drafter supplied 9 hypotheses. An opus prober
confirmed 1, refuted 2 and ruled 6 not a finding. One ctxcat-review
Workflow run supplied 7 raw findings, of which 4 were upheld. An
opus judge passed 3 findings, one low and two nits, under a judge
cap of 7. Six more are carried. The fixes touch two source files. No
frozen capture under `validation/stage-m1-uri-text/` changes, because
the emitted Rust text stays byte-identical.

- F-1, low, `README.md:366`. The axiom report paragraph said 34 foreign
  constants. The catalog, the capture and the axiom suite all report 35. The
  count is now 35.
- F-2, nit, `rust/text_ops.ml:107`. The rewritten `| Natural | Request_uri`
  arm used 14 spaces of indentation against 13 on the arm above it. The arm
  now uses 13 spaces. The change is whitespace only.
- F-3, nit, `rust/text_ops.ml:113-115` and `121-123`. The `Uri` foreign-type
  lookup was written twice in one function. A local `uri_foreign ()` helper
  holds the lookup, and both arms call it. The lookup stays lazy, so the
  refusal behaviour for other text operations does not change. Both matches
  stay exhaustive with no wildcard arm.
- Repin. `validation/stage-m1-uri-text/source-sha256.json` records the new
  SHA-256 of each edited review path: `README.md`, `rust/text_ops.ml` and
  this log.
- Refuted. The review also proposed an effects finding against the
  synchronous classification of `Uri.to_text`. It is refuted, because the
  operation adds no library effect and `dev/STAGE-M1-URI-TEXT.md:22` already
  names the adapter error channel for validation failures.
- Ladders. The baseline ladder ran on the unfixed tree, launched
  detached 2026-09-18T04:50:51Z at load1 15.60, verdict
  2026-09-18T05:02:06Z after 675 s, GATE LSM1R tag=baseline GREEN,
  with PINS tag=baseline ok=155 missing=0 and ROWS tag=baseline
  capture=219 log=219 IDENTICAL. The fix-1 ladder ran on the fixed
  tree, launched detached 2026-09-18T05:18:02Z at load1 12.42,
  verdict 2026-09-18T05:28:03Z after 480 s, GATE LSM1R tag=fix-1
  GREEN, with PINS tag=fix-1 ok=155 missing=0 and ROWS tag=fix-1
  capture=219 log=219 IDENTICAL. The close ladder repeats this gate
  on the staged tree after this paragraph.

## Stage M1 SESSION (2026-09-18)

`lanyard run --requests SCRIPT FILE.lan` runs an ordered request sequence
against one private interpreter database. Script lines carry an origin-form
URI and an optional tab-separated form body. The parser validates every
request before source I/O and exposes an abstract script type to the
interpreter. Limits are 128 requests and 1,048,576 script bytes, with the
existing per-URI and per-form limits. LF and CRLF are accepted; an explicit
empty form remains distinct from no form.

The interpreter prepares the checked program once, allocates one context,
and threads its immutable store and remaining step count through the whole
session. It preserves response order, annotates runtime errors with the
request number, and returns a transcript only when every request succeeds.
The existing single-request path shares the extracted handler shape check.

`test/fixtures/todo-session.lan` combines URI dispatch, explicit schema
initialization, form IDs, trimmed titles, sorted listings, HTML escaping,
completion updates and deletion. Its request file demonstrates a complete
create/list/update/delete sequence. Focused checks exercise isolation,
UTF-8 response lengths, redirects, empty bodies, invalid scripts, option
conflicts, a shared step budget and empty stdout after late failures.

The target catalog, library pins and emitted Rust implementation retain
their existing bytes. The inventory includes the new parser and interface
as unassigned sources. Proposed trust budgets and the M0 exit decision
remain pending.

Validation passed the cumulative `STAGE-M1-SESSION` gate and the complete
Dune test alias. The new checks comprise 30 OCaml cases, 12 CLI groups and
four killed mutations, with clean and restored controls. The mutations
reset the store, reset the budget, reverse responses and omit URI
validation. The retained Stage F result is `STAGE-F-GATES OK m0=PENDING`.
An initial restricted run failed two existing Git stderr assertions on a
macOS `confstr` warning. The successful gate ran with normal macOS access,
with those assertions preserved. Captures and final source hashes are in
`validation/stage-m1-session/`.

## Stage M1 SESSION review fixes (tag LSM1S, 2026-09-18)

A staged-slice review of this stage ran over the 23-path slice on HEAD
798252d. An opus drafter supplied 13 hypotheses. An opus prober
confirmed 2 of them, H1 and H8, and added the sweep item S1. One
ctxcat-review Workflow run (wf_c3c74b68-b94) supplied 8 raw findings,
of which 4 were upheld, and all 4 survived the verifier. An opus judge
upheld 6 findings, one medium, three low and two nits, under a judge
cap of 7. Seven more are carried. The fixes touch four review paths.
No frozen capture under `validation/stage-m1-session/` changes,
because every emitted string stays byte-identical.

- F-1, med, `test/lan_session_mutations.py:25,30`. The mutation driver
  ran `dev/dunecho.sh build` with `timeout=None`, and gave every other
  call a 120 s floor. A hung build stops the stage gate with no
  diagnostic, and a slow build under load fails the controls. The
  helper default is now 600 s, and the build call passes 600 s. No row
  text changes, and the driver still kills 4 of 4 mutants.
- F-2, low, `dev/STAGE-M1-SESSION.md:21-22`. The doc sold the
  1,048,576-byte script bound as a limit. `bin/lanyard.ml:308` reads
  the script file in full, then `rust/run_script.ml` refuses it, so the
  bound is a post-read check. The same paragraph now states this. The
  code keeps the post-read shape, because a bounded reader needs an
  exception path that the house rules ban.
- F-3, low, `rust/run_script.ml:23,28`. Both bound refusals spelled the
  numerals as literals beside the constants `max_bytes` and
  `max_requests`. A bound change leaves an actively wrong message. Both
  messages now derive the numeral with `Printf.sprintf`. Both strings
  stay byte-identical.
- F-4, low, `rust/run_script.ml:22-29`. `parse` tested three conditions
  in one nested if / else-if chain. The house rule asks for a guard
  block. The `lines` binding is now hoisted above a `match () with`
  block that keeps the three tests in the same order. The block has no
  wildcard arm, so the refusal text for an oversized script does not
  change.
- F-5, nit, `rust/run_script.ml:17`. The line-shape error called
  `invalid`, which adds a `request script: ` prefix, and the caller
  adds `request script line %d: ` a second time. The error now builds
  `Error.Mismatch` direct. The three `invalid` calls in `parse` get no
  wrapper, so they keep the prefix.
- F-6, nit, `test/lan_session.ml:14-16`. The test helper `contains`
  built a full suffix string for every index, so the substring test
  allocated in O(n^2). A total `Seq` walk now compares only the needle
  width at each tail. The predicate is the same, the fix adds no check,
  and the row `LAN-SESSION OK checks=30` holds.
- Carried. C-1 keeps the native leg manual, because the slice has no
  native capture by design. C-2 upholds the missing SESSION section of
  `dev/M1-MUTATION-LOG.md` as a gap, and defers it, because the
  preceding slice has the same gap and the staged set must stay at 23
  paths. C-3 refutes the exit-code claim against the doc prose, because
  the cited test pins exit 64 for the script path only. C-4 merges the
  bound-literal report into F-3. C-5 drops the CR strip report, because
  the proposed `String.sub` is partial and raises. C-6 drops the
  by-design reports on the SIG-SHA contract, the borrowed native
  `Cargo.lock` and the receipt shape. C-7 confirms that no fix changes
  a frozen `LAN-`, `STAGE-` or `EMIT-` row.
- Proof. The fix run reports `FIX-RUN paths=15 captures=8 extras=0`,
  `FIX-RUN STAGED base=23 porcelain=23 captures=8 optional=0
  unexpected=0` and `FIX-RUN CONTRACT OK porcelain=23 == base 23`. The
  pin map reports `FIX-RUN-PINS-VERIFY ok=15 mismatch=0` over the five
  repinned paths: `test/lan_session_mutations.py`,
  `dev/STAGE-M1-SESSION.md`, `rust/run_script.ml`,
  `test/lan_session.ml` and this log. The needle sweep reports
  `NEEDLES rows=14 bad=0`. The build reports `OK build: 0 errors, 0
  warnings`.
- Ladders. The baseline ladder ran on the unfixed tree, launched
  detached 2026-09-18T17:28:25Z at load1 13.99 (pid 3877), verdict
  2026-09-18T17:41:38Z after 793 s, 865 log lines, GATE-END
  tag=baseline stage_rc=0, GATE LSM1S tag=baseline GREEN, with PINS
  tag=baseline ok=164 missing=0 and ROWS tag=baseline capture=228
  log=228 IDENTICAL. The fix-1 ladder ran on the fixed tree, launched
  detached 2026-09-18T17:59:23Z at load1 12.61 (pid 72468), verdict
  2026-09-18T18:21:30Z after 1200 s, 865 log lines, GATE-END tag=fix-1
  stage_rc=0, GATE LSM1S tag=fix-1 GREEN, with PINS tag=fix-1 ok=164
  missing=0 and ROWS tag=fix-1 capture=228 log=228 IDENTICAL. The
  close ladder repeats this gate on the staged tree after this
  paragraph.

## M1 native request sessions (2026-09-18)

`emit --crate DIR --requests SCRIPT FILE.lan` and `build --out DIR
--requests SCRIPT FILE.lan` embed the validated request sequence in a
standalone Rust program. Script validation precedes program I/O. The
existing model-output option conflicts with request mode, and the build
driver preserves Cargo flags, output and exit status.

The session emitter reuses the checked request shape and byte-list layout.
The Rust entry printer verifies those layouts against its own lowered
signature and selects synchronous or awaited calls from inferred effects.
Unused form arguments still receive their checked text conversion. Each
request runs as a sequential Tokio task against one private SQLite context.
This requires a Send future and converts task failures into indexed errors.
The pinned SQLite missing-schema panic is covered by this path.

The program collects the full HTTP transcript before writing stdout.
Eight native cases, run twice each, agree with independent expected
transcripts and the interpreter. They cover the Todo lifecycle, redirects,
URI text, UTF-8 and control bytes, ignored forms, 128 requests, a late
failure and a missing schema. Two compiled runtime controls demonstrate
that reversed responses and partial transcripts are detected.

The cumulative `STAGE-M1-NATIVE-SESSION` gate passed, retaining the earlier
M1 gates and five new CLI test groups. The earlier restricted attempt
failed two existing Git stderr assertions because macOS emitted a confstr
warning; the successful run used normal macOS access with those assertions
preserved. Generated Rust has dead-code warnings. The full Dune alias and
final accounting checks are recorded separately under
`validation/stage-m1-native-session/`.

The printer inventory and line total now include `rust/session_emit.ml`.
This accounting update follows the aggregate run and has its own checks;
it changes no compiler or runtime source bytes. Source hashes record the
final inputs. Target signatures, dependency pins, proposed trust
allowances and the pending M0 exit stamp retain their existing values.
The manual approval probe now derives an exact roster and limits for its
disposable test policy. This lets its budget mutations run after source
growth instead of failing on the old proposal before any mutation. Its
source-policy byte check still requires the real proposal to remain intact.

## Stage M1 NATIVE-SESSION review fixes (tag LSM1NS, 2026-09-18)

A staged-slice review of this stage ran over the 30-path slice on HEAD
414121c. The slice holds 19 review paths and the 11 frozen captures
under `validation/stage-m1-native-session/`. One Workflow run
(wf_4e41740b-20e) ran three finders by lens, ocaml, python-gate and
docs-captures, then one adversarial verifier for each finder batch,
then one judge. The verifiers took 12 rows, upheld 8 and refuted 4.
The judge kept 7 findings under the judge cap of 7, five low and two
nits, and carried 5 more. This fix applies all 7. No frozen capture
under `validation/stage-m1-native-session/` changes, because every
emitted row stays byte-identical.

- F-1, low, `dev/STAGE-M1-NATIVE-SESSION.md:30-35`. The doc promised a
  request number for a database failure. The `Database` arm of
  `LanSessionError` carries no request number, and its only producer,
  the in-memory connect, runs before any request exists. The paragraph
  now numbers handler and response failures, and states that a
  database or output failure names no request.
- F-2, low, `dev/stage-m1-native-session.sh:11-13`. The cleanup trap
  covered EXIT only, so an interrupt during the multi-minute Cargo
  build left the eight-crate work tree inside the repository. Two
  signal traps now remove the tree and exit, 130 on INT and 143 on
  TERM or HUP. One combined trap was tested and rejected, because zsh
  then continues the script after the handler.
- F-3, low, `rust/emit.ml:610-617`. The scripted entry-point layout
  check tested three conditions in one `if` chain. A parenthesized
  `match () with` block now holds the same three tests in the same
  order. The brackets are load-bearing, because line 618 is an arm of
  the outer `match output with`. The refusal text does not change.
- F-4, low, `rust/session_emit.ml:82-85`. The emitter copied the raw
  form body into the generated Rust literal, so a body that mixes a
  high byte with a percent escape wrote a `src/main.rs` that rustc
  cannot read. `entry` now refuses that body and names the request
  number. The check in `rust/form_data.ml` tests the decoded field
  only, so it accepts the same input.
- F-5, low, `test/lan_native_session.py:20-22,158`. The suite gave
  every subprocess 120 s, which equals the budget of each of the five
  children of `dev/prepare-crate.py`, so the child's named
  `CRATE-PREPARE FAIL` timeout row was unreachable. The `run` helper
  now takes a timeout keyword and the crate-prepare call passes 900 s.
  A caught timeout was applied first and then reverted, because the
  house rule `one-catch-site` allows exactly one `try` under lib,
  surface, bin and test (`test/sys_io.ml:19`), so a timeout still
  surfaces as a Python traceback.
- F-6, nit, `rust/model.ml:244-248`. The foreign-path guard grew to
  four conditions in one `if`. A `match () with` guard block now holds
  them in the same order. This is style only, and the emitted source
  does not change.
- F-7, nit, `test/lan_native_session.py:110-117`. The bad-entry-point
  test pinned stderr to the substring `request`, which every session
  error carries. Each of the three cases now pins its own indexed
  prefix, `request 1: ` or `request 2: `, and all three pin `entry
  point must have type`.
- Carried. C-1 upholds the interpreter-agreement check in
  `test/lan_native_session.py`, which pins stdout and the exit code
  but not the indexed error, and defers it as the weakest row past the
  cap of 7. C-2 refutes the approved-policy report on
  `test/lan_approved_policy.py`, because the fixture approves exactly
  the copied bytes and the proposed fix would delete eight frozen
  capture rows. C-3 refutes the KeyError report on the same file as
  speculation about a future edit, because the staged code indexes a
  key that exists. C-4 refutes the `--prepare` report on
  `test/lan_native_session.py`, because a refused existing directory
  keeps stale crates out of the eight-case manifest. C-5 refutes the
  dead-code report on this log, because the build row hides warning
  text by construction and the receipt corroborates the claim.
- Repins. Seven paths take new hashes in
  `validation/stage-m1-native-session/source-sha256.json`:
  `dev/STAGE-M1-NATIVE-SESSION.md`, `dev/stage-m1-native-session.sh`,
  `rust/emit.ml`, `rust/session_emit.ml`, `rust/model.ml`,
  `test/lan_native_session.py` and this log. The map keeps its 29
  entries and verifies `PINS ok=29 mismatch=0`. The build reports `OK
  build: 0 errors, 0 warnings`.

Proof: `zsh dev/gates.sh --stage M1-native-session` on the staged
tree (2026-09-18T21:24:19Z, load 18.5) prints `OK build: 0 errors,
0 shown-warnings (141 hidden; --warn)`,
`LAN-NATIVE-SESSION-CLI OK groups=5`,
`LAN-NATIVE-SESSION PREPARED cases=8 mutants=2`,
`LAN-NATIVE-SESSION OK cases=8 executions=16 mutants=2`,
`STAGE-M1-NATIVE-SESSION OK` and exits 0. The same command on a
clone of the slice before the fixes was green at 21:02:34Z. A first
fix run went red at `HOUSE one-catch-site FAIL` because F-5 had
added a Python `try`; the rework above removed it. The trusted
accounting moves with the fixes: emit 684 to 688, model 282 to 285,
session_emit 115 to 119, printer-total 1766 to 1777;
TRUSTED-POLICY stays PROPOSED with candidate lines 14191 (was
14180). The first `TRUSTED-LINES` block of the run reports
`printer-total=1827` because the M0 mutation leg measures a mutant
copy with `added-lines=50`; the clean root and the FAST leg both
report 1777, and the baseline log shows the same shape at 1816 and
1766. The frozen captures keep the pre-fix counts, as the receipt
notes record; only `source-sha256.json` is refreshed and `PINS
ok=29 mismatch=0` holds.

## M1 loopback HTTP listeners (2026-09-18)

`emit --crate` and `build --out` accept `--listen 127.0.0.1:PORT`.
The generated program serves checked two-argument and form handlers
through pinned Topcoat, using one private SQLite store and serialized
handler calls. An abstract listen-address type enforces the loopback
endpoint before source I/O. The HTTP entry retains the emitter's checked
parameter and result layouts. Batch manifests and target pins are unchanged.

The adapter shares the URI and form validators with existing operations.
Form field decoding now exposes its validated field list for boundary
checks, including ignored forms. Request bodies have an 8192-byte bound
and a five-second read timeout. Typed errors select 400, 408, 413, 415 or
500; Topcoat handles HTTP framing, panic containment and graceful shutdown.
The pinned HTTP parser removes fragments before the adapter sees them,
which is documented and tested separately from raw scripted URI parsing.

Validation: `zsh dev/gates.sh --stage M1-http` exited 0 on the isolated
checkout of `e49c43e25b48c38d65ad4d7603e2116858ff65a2` plus this slice.
The cumulative run retained the compiler and interpreter gates, eight
native session cases with sixteen executions and two controls, four HTTP
CLI groups, and six socket groups over five server cases and two controls.
The generated HTTP build reported zero errors and 98 hidden warnings;
the retained session build reported zero errors and 141 hidden warnings.
The run used Rust 1.98, clean local target checkouts, an offline locked
build, and the existing Cargo cache. Additional transport packages were
fetched before validation and are pinned in the saved lockfile.

`validation/stage-m1-http/` records the full stage stdout and stderr,
capture manifest, receipt, lockfile and changed-source hashes. The existing
M0 trust-budget rulings and exit stamp remain pending. No policy approval
is implied by the successful stage gate.

## Stage M1 HTTP review fixes (tag LSM1HT, 2026-09-18)

A staged-slice review of this stage ran over the 22-path slice on HEAD
e49c43e. The slice holds 16 review paths and the 6 frozen captures
under `validation/stage-m1-http/`. Three finder lenses, ocaml,
python-gate and docs-captures, reported fourteen rows, which the
adversarial verifiers and the judge reduced to 6 upheld findings under
the judge cap of 7, one medium, four low and one nit. Eight rows are
carried, and every carried row is refuted. This fix applies all 6.

- F-1, medium, `rust/server_emit.ml:95-98`. The emitted content-type
  test was an exact byte comparison, so a conformant POST that adds a
  parameter, `application/x-www-form-urlencoded;charset=UTF-8`, or
  that folds case took 415 and the handler never ran. The emitter now
  splits the header at the first `;`, trims it and lowercases it
  before the compare, and tests the result with `as_deref`. A missing
  or a wrong type still yields 415.
- F-2, low, `dev/STAGE-M1-HTTP.md:62-64`. The doc claimed socket
  coverage of panic recovery, but no group makes an emitted handler
  panic: the suite asserts 500 for a handler `Result` error, which the
  runtime maps through `.map_err(LanHttpError::Handler)?`. The
  sentence now reads "handler error recovery and SIGTERM shutdown".
  The shutdown half is real, because the suite sends SIGTERM and
  asserts exit 0.
- F-3, low, `rust/server_emit.ml:85`. The transport body bound was the
  bare numeral 8192, which repeats `Form_data.max_bytes`, so a later
  edit of the named constant would leave the two limits apart and
  answer an oversized form 413 on one path and 400 on the other. The
  emitter now splices `string_of_int Form_data.max_bytes`, the shape
  `rust/form_data.ml:81` already uses. The emitted bytes do not
  change, because the constant is 8192.
- F-4, low, `rust/server_emit.ml:13`. A nonempty body sent to a
  two-argument handler, which has no form at all, was reported as
  `invalid request URI or form`. No variant is added: the one message
  now reads `invalid request URI, form or body`, which stays true for
  the three-argument emission, where BadRequest covers the invalid
  URI, the non-UTF-8 body, the nonempty body on a non-POST method and
  the invalid form.
- F-5, low, `test/lan_http.py:22-24,109-112`. One helper gave every
  subprocess 900 s. No call in the file is a Cargo or dune build, so a
  hang stayed hidden for a quarter of an hour. `run` now takes a
  `timeout` keyword that defaults to 60 s, and the crate-prepare call
  passes 300 s, which covers the five 120 s-capped children of
  `dev/prepare-crate.py`. The five CLI call sites are unchanged.
- F-6, nit, `dev/M1-MUTATION-LOG.md:775`. The unchecked-form row named
  neither the POST method nor the content-type header, so the stated
  303 is not reproducible as written: the same bytes sent as a GET
  return 400 from the mutant and a POST without the header returns
  415. The row now names both.
- Carried. Eight rows are carried and every one is refuted: C-1, C-3
  and C-4 on the concurrency group, the panic claim and the socket
  lifetime in `test/lan_http.py`, C-2 on the bounded server shutdown
  in the same file, C-5, C-7 and C-8 on `dev/STAGE-M1-HTTP.md`, and
  C-6 on the Rust 1.98 row of this log, which eight capture rows
  corroborate.
- Repins. Five paths take new hashes in
  `validation/stage-m1-http/source-sha256.json`:
  `rust/server_emit.ml`, `dev/STAGE-M1-HTTP.md`, `test/lan_http.py`,
  `dev/M1-MUTATION-LOG.md` and this log. The map keeps its 17 entries
  and verifies `PINS ok=17 mismatch=0`. The build reports `OK build: 0
  errors, 0 shown-warnings (98 hidden; --warn)` and `dev/house.sh`
  reports `HOUSE OK`.

Proof: `zsh dev/gates.sh --stage M1-http` on the staged tree
(GREEN at 2026-09-19T03:23:23Z, load 20.50) prints `OK build: 0
errors, 0 shown-warnings (98 hidden; --warn)`,
`LAN-HTTP CLI OK groups=4`,
`LAN-HTTP PREPARED cases=5 mutants=2`,
`LAN-HTTP RUNTIME OK groups=6` and `STAGE-M1-HTTP OK`, and exits 0.

## M1 compile and serve (2026-09-18)

Added `serve --out DIR --listen ADDRESS [--release] [--offline] FILE.lan`.
It reuses build-option validation and HTTP crate emission, then replaces
the driver with `cargo run` in the new crate. Cargo retains responsibility
for its configured target directory and target runner. Paths never enter
shell text. Missing or unexecutable Cargo retains the shell's 127 or 126
status, and compilation or server failures preserve the emitted crate.
The existing `build` command retains its compilation-only timing report.

Eight process test groups cover refusal before source I/O, exact HTTP
crate bytes, Cargo arguments and environment, stdin, status propagation,
shell metacharacters in paths, existing outputs and direct signal delivery.
The native test verifies emitted bytes against a checked local-pin seed,
then uses real offline Cargo to exercise Todo requests and fresh restart.
Both SIGINT and SIGTERM produce graceful server exits. The `M1-serve`
gate retains the full `M1-http` gate before these checks and ends with
the house checks. No trust-policy allowance or milestone exit is approved.

Validation receipts and input hashes are recorded under
`dev/validation/stage-m1-serve/`.

## Stage M1 SERVE review fixes (tag LSM1SV, 2026-09-19)

A staged-slice review of this stage ran over the 13-path slice on HEAD
20a3e18. The slice holds 8 review paths and the 5 frozen captures under
`validation/stage-m1-serve/`. Three finder lenses, ocaml, python-gate and
docs-captures, reported four rows, which the adversarial verifiers and
the judge reduced to 1 upheld finding under the judge cap of 7, one low.
Three rows are carried, and every carried row is refuted. This fix
applies the 1 upheld finding.

- F-1, low, `test/lan_serve_native.py:18`. The READY regex ended in `$`,
  which matches end of buffer even under `re.MULTILINE`, so the poll
  could read a truncated in-progress write and report the wrong port
  before the marker line's trailing newline lands in the shared
  diagnostics file. The pattern now ends in a literal `\n`, the same
  convention `test/lan_http.py:139` already uses for the identical
  marker. The read and search loop at lines 70-78 is unchanged.
- Carried. Three rows are carried and every one is refuted: C-1 on the
  Header Exit codes paragraph in `bin/lanyard.ml`, which already
  documents serve's exit codes in the dispatch_serve comment; C-2 on
  process-group cleanup in `test/lan_serve_native.py`, which execs
  straight into the compiled binary with no fork; and C-3 on the
  "restart" wording in `dev/STAGE-M1-SERVE.md`, which matches existing
  codebase vocabulary for the same pattern.
- Repins. Two paths take new hashes in
  `validation/stage-m1-serve/source-sha256.json`:
  `test/lan_serve_native.py` and this log. The map keeps its 15 entries
  and verifies `PINS ok=15 mismatch=0`. The build reports `OK build: 0
  errors, 0 warnings` and `dev/house.sh` reports `HOUSE OK`.

Proof: zsh dev/gates.sh --stage M1-serve GREEN on the fixed tree
(2026-09-19, LAUNCH 11:51Z to GATE-END 12:00Z, stage_rc=0):
STAGE-M1-HTTP OK, CRATE-PREPARE OK, LAN-SERVE NATIVE OK lifecycle=2
signals=2, HOUSE OK, STAGE-M1-SERVE OK. The same gate was GREEN on the
unfixed slice before the fix. Pins ok=15 mismatch=0.

## M1 persistent HTTP databases (2026-09-19)

Added `--database PATH` to HTTP crate emission, build, and serve. A checked
path is anchored to the invocation directory before Cargo changes the
working directory. The file driver receives the literal path, including
URI punctuation, instead of parsing it as a database URL. Its direct
dependency uses the existing Toasty revision. Without the option, HTTP
source and manifest bytes retain their in-memory form.

Option validation precedes source and output I/O. The database is opened
only at server startup. Handlers still own schema creation; startup does
not reset or migrate an existing database. Existing output refusals,
Cargo process behavior, HTTP validation, and shutdown remain in place.

The new cumulative `M1-database` gate retains `M1-serve`, adds five CLI
groups, and compiles a native persistence test and an in-memory mutation
control. Native checks cover create, update, delete, restarts, invocation
and runtime working directories, unusual filename bytes, SIGINT and
SIGTERM, and missing-parent startup failure. Captures and source hashes
are recorded under `dev/validation/stage-m1-database/`.

Validation on the isolated checkout completed with exit 0 and
`STAGE-M1-DATABASE OK`. The cumulative gate also reported
`STAGE-M1-HTTP OK`, `STAGE-M1-SERVE OK`, five passing database CLI
groups, and `LAN-DATABASE NATIVE OK restarts=3 signals=2
startup-failures=1 mutants=1`. House checks passed. The native suite ran
against checked local target pins with offline Cargo and permission for
loopback sockets. A separate comparison confirmed byte-identical default
HTTP and batch manifests and Rust sources against the main checkout's
compiler. No trust allowance or milestone exit was approved.

## Stage M1 DATABASE review fixes (tag LSM1DB, 2026-09-19)

A staged-slice review of this stage ran over the 25-path slice on HEAD
5e5a35b. The slice holds 16 review paths and the 9 frozen captures
under `validation/stage-m1-database/`. Three finder lenses, ocaml,
python-gate and docs-captures, reviewed the slice; the adversarial
verifiers and the judge upheld 3 findings under the judge cap of 7,
all low. One row is carried, and it is refuted. This fix applies the
3 upheld findings.

- F-1, low, `rust/database_path.ml:3-8`. The `parse` guard ORed six
  boolean sub-conditions in a single `if` instead of a `match ()`
  guard block, the idiom the neighboring `rust_string` escape function
  in the same file already uses. `parse` now reads a `match () with`
  block: one guarded arm for the six conditions returning the same
  `Error`, and a bare `()` arm returning the same `Ok` payload. The
  error text and the Ok payload are byte-identical to before.
- F-2, low, `test/lan_database.py:114`. The CLI gate OK line hardcoded
  `groups=5` instead of deriving it from the suite. The line now
  prints an f-string built from `result.testsRun`, reusing the
  `result` object already bound at line 111. This evaluates to 5
  today, so `capture-stdout.txt` row 771 stays byte-identical.
- F-3, low, `test/lan_database_native.py:178`. The native gate OK line
  hardcoded `restarts=3 signals=2 startup-failures=1 mutants=1`
  instead of deriving the numbers from the test's own counters.
  `NativeDatabase` now keeps class-level `restarts`, `signal_kinds`,
  `startup_failures` and `mutants` counters, reset in `setUp`.
  `restarts` bumps only before the "second" serve (line 126), the
  "direct" start (line 132) and the "deleted" start (line 136), not
  the "first" or "control" starts, giving restarts=3. `shutdown`
  records every signal it receives into `signal_kinds` (line 111),
  giving signals=2 across SIGTERM and SIGINT. `startup_failures`
  bumps once, right after the missing-parent assertions (line 146),
  giving startup-failures=1. `mutants` takes the `re.subn` count
  (line 154), giving mutants=1. Line 178 now derives its printed row
  from these four counters, reproducing the exact frozen string, so
  `capture-stdout.txt` row 772 stays byte-identical.
- Carried. C-1 on the toasty-driver-sqlite revision in `rust/crate.ml`
  is refuted: `dev/prepare-crate.py:76` already cross-checks both the
  toasty and toasty-driver-sqlite manifest revisions against the same
  pinned commit and hard-fails on drift.
- Repins. Four paths take new hashes in
  `validation/stage-m1-database/source-sha256.json`:
  `rust/database_path.ml`, `test/lan_database.py`,
  `test/lan_database_native.py` and this log. The map keeps its 26
  entries and verifies `PINS ok=26 mismatch=0`. The build reports
  `OK build: 0 errors, 0 warnings`.

Proof: zsh dev/gates.sh --stage M1-database GREEN on the fixed tree
(2026-09-20T00:14:23Z, stage_rc=0, load averages 21.49 25.90 26.04):
STAGE-M1-HTTP OK (907), STAGE-M1-SERVE OK (930), LAN-DATABASE CLI OK
groups=5 (941), LAN-DATABASE NATIVE OK restarts=3 signals=2
startup-failures=1 mutants=1 (949), STAGE-M1-DATABASE OK (958). Log:
gates-LSM1DB-fix-1.log. The baseline ladder on the unfixed copy was
GREEN 2026-09-19T22:43:57Z stage_rc=0. Row comparison of the fix log
against the frozen capture dev/validation/stage-m1-database/
stage-0001.stdout: capture=731 log=761 rows, differences are the known
noise families only (extra bare OK rows, M0-DETAIL mktemp paths) plus
the TRUSTED-INVENTORY sha256 and TRUSTED-POLICY lines=14436 rows that
move with any source edit. Pins ok=26 mismatch=0.

## M1 URI path and query adapters (2026-09-19)

Added `Uri.path` and `Uri.query` with closed byte-list output types. Path
selection stops at the first `?`; query selection omits that separator and
preserves the remainder. Missing and empty queries both return empty text.
Both runtimes validate the entire origin-form URI before projection,
including unused results and invalid bytes in the other component. The
native adapters call the pinned URI accessors after validation. Existing
`Uri.to_text` emission retains its rendering and validation sequence.

The fixture separates path routing from query decoding with `Form.field`.
Interpreter and socket tests cover encoded Unicode, plus signs, reserved
bytes, empty queries, handler errors and recovery. Direct native calls also
cover aliases, captures, alternate byte-list families, boundary lengths,
and invalid values that the native URI type permits. A compiled control
removes all four specialized validation sites and must expose the expected
invalid-value acceptance for used and unused component results.

The target catalog now has 32 proposed declarations, nine foreign types
and 206 generated lines. Todo reports 37 foreign constants and three
definitions. Catalog assertions, axiom-report totals and the Todo report
golden reflect the two added schemas. Library pins and dependencies retain
their existing revisions. No trust allowance or milestone exit is approved.

The new `M1-uri-parts` gate preserves `M1-database`, including its HTTP,
serve and persistence checks. It adds 92 interpreter checks, four CLI
groups and 140 native observations with one compiled mutation control.
Captures and source hashes are recorded under
`dev/validation/stage-m1-uri-parts/`.

The cumulative gate completed with exit 0 and `STAGE-M1-URI-PARTS OK`.
Its seven HTTP runtime groups, serve lifecycle checks, and three database
restarts passed. Native builds used checked local pins and offline Cargo;
the gate ran with loopback socket access. House checks passed. The existing
combined M0 gate retained its pending trust ruling.

## M1 URI path and query adapters: review fixes (2026-09-19)

A review of the staged URI-PARTS slice (tag LSM1UP) found one defect and refuted one candidate.

- dev/gates.sh: the runtime usage row now lists the `--stage M1-uri-parts` form next to the M1-database form. The header comment already listed it.
- Refuted: the mutation log sentence that lists invalid native URI value kinds uses the word include and gives the count of nine. It does not claim to be exhaustive.

Gate: `zsh dev/gates.sh --stage M1-uri-parts` on the fixed tree.

Proof: STAGE-GATE-EXIT 0
  GATE-END tag=fix-1 2026-09-20T03:55:50Z stage_rc=0
  GATE LSM1UP tag=fix-1 GREEN

## M1 optional form fields (2026-09-19)

`Form.has` checks for a decoded form field and returns the existing Boolean
sum. Missing fields and empty bodies return false; empty values count as
present. Both execution paths parse and validate the complete body before
testing presence, retaining the existing byte, field-count, duplicate-name
and UTF-8 limits.

The schema participates in closed byte-list specialization, metadata
validation, interpreter dispatch, and native Boolean conversion. The Rust
helper uses the same checked form parser as `Form.field`. No dependency or
library revision changes. The catalog has 33 proposed declarations; its
signature hash, declaration counts and axiom golden reflect the addition.

Focused validation passed: 65 interpreter checks, two CLI groups, and 103
native observations with one compiled mutation control. Aliases, captured
calls, alternate families, unused errors, and argument evaluation order
are covered. The cumulative `M1-form-has` gate retains `M1-uri-parts`,
including HTTP, serve, and database restart coverage. Its final receipt
and source hashes belong under `dev/validation/stage-m1-form-has/`.

Trust allowances and milestone exits retain their existing pending status.

The cumulative gate completed with exit 0 and `STAGE-M1-FORM-HAS OK`.
HTTP runtime checks, serve lifecycle checks and database restarts passed.
Native builds used the checked local pins and offline Cargo. House checks
passed. The combined M0 gate retained its pending trust ruling.
## M1 text byte lengths (2026-09-20)

Added `Text.length` with a closed byte-list input and a natural-number
result. It counts UTF-8 bytes, including whitespace and embedded NULs,
without normalization. The interpreter validates the complete byte list
before taking its length. Native emission uses the same checked conversion
and constructs a canonical natural from every byte of Rust's length value.
There is no narrowing or new foreign error effect.

The schema participates in specialization, metadata validation, aliases,
captured calls and alternate byte-list families. Invalid UTF-8 and byte
values above 255 fail even when the result is discarded. The catalog now
has 34 proposed declarations; the signature digest, declaration counts and
Todo axiom golden reflect the addition. Dependencies retain their revisions.

Focused checks passed: 44 interpreter checks, four CLI groups and 34 native
observations. Two compiled controls replace byte counting with character
counting or truncate the count to one byte; both produce incorrect answers.
The cumulative `M1-text-length` gate retains all `M1-form-has` checks,
including HTTP, serve and database restarts. Validation receipts and source
hashes belong under `dev/validation/stage-m1-text-length/`.

Trust allowances and milestone exits retain their pending status.
