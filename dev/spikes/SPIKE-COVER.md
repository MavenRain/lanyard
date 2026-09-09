# SPIKE-COVER, the covering relation from the 570 roots to ledger rows

Spike S5, wave Cover, alone.  Date 2026-09-09.  This file closes fact 5 of
M0-PLAN.md section 12: no proposal published a rule from the 570 roots to
ledger rows, so every parity count in the panel is chosen and not computed.
Stage 0 measures and rules nothing.  The row milestones below are PROPOSED
under decision S0-D4 and the user rules them.

## 1 The rule, in one paragraph, before any count

The rule is this.  A root is one name in
`/Users/oobi/Documents/kanon-m2-corpus/corpus/lean-parity/uat/roots.txt`.  The
export `uat/uat.export` declares every constant of the transitive closure of
those roots, one declaration line per declaration group, and a root is matched
to its declaration line by name, after the guillemet quotes U+00AB and U+00BB
that Lean prints around a name component that is not an identifier are removed
from both sides.  The closure of a root is the least set of declaration lines
that holds the root's own line and, for every line already in the set, every
line that declares a constant which that line names in a `const` node of its
type, its value, a constructor type, a recursor type or a recursor rule right
hand side.  A declaration line needs the ledger rows its own text needs, by
sixteen fixed tests over that text: which expression node kinds it holds, its
declaration kind, how many universe parameters it carries, the binder
information of its binders, whether an inductive block it declares is nested or
unsafe, and whether it names a constant in one of five fixed name sets, which
are the transport set, the classical axiom set, the quotient prefix, the well
founded set and the `Decidable` prefix.  The rows a root needs are the union of
the rows needed by the lines of its closure.  The milestone of a root is the
highest milestone over those rows, on the order M0 below M1 below M2 below M3
below NEVER.  The M2 expectation is the number of roots whose milestone is M0,
M1 or M2, which is the number of roots whose closure lies inside the M0, M1 and
M2 ledger rows, exactly the set the M2-PARITY gate counts.  Nothing in the
count is chosen: rows 1 to 13 are the published feature list of the corpus
census, rows 14 to 16 are the three rungs that the export and the ratified
NEVER list add, the milestone on each row is the first gate of the verdict that
needs that row, and every count below is printed by `awk` over the labelling
table.

## 2 Inputs, all read only

| input | value |
| --- | --- |
| roots | `/Users/oobi/Documents/kanon-m2-corpus/corpus/lean-parity/uat/roots.txt` |
| export | `/Users/oobi/Documents/kanon-m2-corpus/corpus/lean-parity/uat/uat.export` |
| export sha256 | `f4439dce6a0b488e9bc328592e53c47867c4d19fb123b31358aeb35ed5d14354`, from `uat/manifest.json` |
| row source, ranks 1 to 13 | `uat/census.md`, section "Ranked: features kanon M2 must implement to pass the UAT corpus" |
| ratified NEVER list | RATIFICATIONS.md block (c), D-M0-7, NEVER-1 to NEVER-10 |

No file inside the corpus was written.  The labelling table and the two scripts
live under `/Users/oobi/Documents/lanyard-m0/spikes/s5/`.

## 3 The row count, with the command that printed it

```
wc -l /Users/oobi/Documents/kanon-m2-corpus/corpus/lean-parity/uat/roots.txt
```

```
     570 /Users/oobi/Documents/kanon-m2-corpus/corpus/lean-parity/uat/roots.txt
```

The labelling table holds one row per root:

```
awk -F'\t' 'NR>1 {n++} END {print "LABELLED-ROWS " n}' /Users/oobi/Documents/lanyard-m0/spikes/s5/labels.tsv
```

```
LABELLED-ROWS 570
```

570 roots read, 570 rows labelled, 0 unlabelled.  The labelling run printed:

```
ROOTS read=570 labelled=570 unlabelled=0
CLOSURE passes=29 declLines=2945 unresolvedConstants=0
UNLABELLED none
```

`declLines=2945` agrees with `uat/census.json` `declarationLines`, which sums
axiom 3, def 1176, inductive 112, opaque 1, quot 4 and thm 1649 to 2945.
`unresolvedConstants=0` means every constant named by a line is declared by
another line of the same export, so no closure leaves the corpus.

## 4 The ledger, sixteen rows

Ranks 1 to 13 are the census feature list, copied row for row.  Rank 14 is the
one nested inductive block the export holds.  Rank 15 and rank 16 are the two
rungs that make the ladder complete, so a root can reach NEVER or M3 when a
corpus holds such a line.  Milestone rule: the milestone is the first gate of
the design verdict that needs the row.

| row | milestone | feature | test on one declaration line | why that milestone |
| --- | --- | --- | --- | --- |
| LR-1 | M0 | Expression core: bvar, sort, const, app, lam, forallE with binder info | any core node kind present | `lanyard check` at M0 reads every term |
| LR-2 | M0 | Definitional unfolding of definition and theorem values | kind is def, thm or opaque | the M0 model file has definitions to unfold |
| LR-3 | M0 | Inductive types, constructors and recursors with iota | kind is inductive | the M0 model declares data |
| LR-4 | M0 | Universe levels with max and imax, and level substitution | the line carries universe parameters, or a sort node reads a level that uses max, imax or a parameter | the carried kernel holds lib/level.ml at the pin |
| LR-5 | M1 | Proof irrelevance and Prop | kind is thm | M1-NEG accepts the subsingleton half of the Prop family |
| LR-6 | M2 | Eq.rec, Eq.mpr and cast transport | names a constant of the transport set | M2-PARITY is the first gate that re-checks corpus proofs |
| LR-7 | M2 | Structure projections and structure eta | holds a proj node | the eta rule shows up first in corpus equality proofs at structure types |
| LR-8 | M2 | Quotient types and quot reduction | kind is quot, or names Quot or a Quot member | no M0 or M1 leg reduces a quotient |
| LR-9 | M0 | Classical axioms as opaque constants | kind is axiom, or names propext, Classical.choice or Quot.sound | `lanyard axioms` at M0 prints the Classical class |
| LR-10 | M0 | let expressions and zeta reduction | holds a letE node | the pin kernel term holds `Let` in lib/term.ml |
| LR-11 | M0 | Nat and String literals | holds a natVal or a strVal node | the pin kernel term holds `Lit` and lib/literal.ml |
| LR-12 | M2 | Well founded recursion support constants | names WellFounded, Acc.rec or a brecOn | no M0 or M1 leg needs well founded recursion |
| LR-13 | M2 | Decidable instances and instance implicit binders | names Decidable, or holds an instImplicit binder | no M0 or M1 leg reduces a Decidable instance |
| LR-14 | M2 | A nested inductive block | the inductive block reports numNested above 0 | NEVER-1 refuses the kernel former, a mutual mu carries the declaration, and M2-PARITY is the first gate that needs the carrier |
| LR-15 | NEVER | An unsafe or partial declaration inside the trusted base | the line reports isUnsafe true | a trusted base cannot carry an unsafe declaration |
| LR-16 | M3 | Native reduction axioms | names Lean.ofReduceBool, Lean.ofReduceNat or Lean.trustCompiler | such an axiom is outside the four tracked classes of M0 and lands with M3-AXIOM |

The machine form is `/Users/oobi/Documents/lanyard-m0/spikes/s5/ledger.tsv` and
the tests are `row_bits` in
`/Users/oobi/Documents/lanyard-m0/spikes/s5/label-roots.py`.

## 5 The per-milestone counts, computed

```
awk -F'\t' 'NR>1 {n[$2]++} END {for (m in n) printf "MILESTONE %s roots=%d\n", m, n[m]}' /Users/oobi/Documents/lanyard-m0/spikes/s5/labels.tsv | sort
```

```
MILESTONE M0 roots=89
MILESTONE M1 roots=8
MILESTONE M2 roots=473
```

```
awk -F'\t' 'NR>1 {t++; if ($2=="M0"||$2=="M1"||$2=="M2") k++} END {printf "PARITY-EXPECT m2=%d of %d\n", k, t}' /Users/oobi/Documents/lanyard-m0/spikes/s5/labels.tsv
```

```
PARITY-EXPECT m2=570 of 570
```

The M2 expectation is 570 of 570.  It is computed, not chosen: no root of this
corpus needs an M3 row or a NEVER row, because LR-15 and LR-16 match no line of
the export, so every closure lies inside the M0, M1 and M2 rows.  89 roots stop
at M0, so 89 roots are inside the carried kernel alone.  8 more need only the
Prop row on top of the M0 rows.  473 need at least one M2 row.

Closure size band over the 570 roots:

```
awk -F'\t' 'NR>1 {s+=$3; if($3>mx)mx=$3; if(mn==0||$3<mn)mn=$3} END {printf "CLOSURE min=%d max=%d mean=%.1f\n", mn, mx, s/(NR-1)}' /Users/oobi/Documents/lanyard-m0/spikes/s5/labels.tsv
```

```
CLOSURE min=1 max=2598 mean=177.2
```

## 6 Rows against roots, and the mutation sensitivity

```
cat /Users/oobi/Documents/lanyard-m0/spikes/s5/row-hits.tsv
```

```
row	milestone	rootsNeeding	declLinesNeeding
LR-1	M0	570	2945
LR-2	M0	547	2826
LR-3	M0	570	112
LR-4	M0	570	932
LR-5	M1	387	1649
LR-6	M2	335	704
LR-7	M2	439	241
LR-8	M2	114	7
LR-9	M0	222	194
LR-10	M0	246	162
LR-11	M0	167	1085
LR-12	M2	133	88
LR-13	M2	402	623
LR-14	M2	41	1
LR-15	NEVER	0	0
LR-16	M3	0	0
```

The M2-PARITY mutation of the verdict is "move one root's ledger row to M3 and
the printed count must drop by exactly that root's contribution".  The
`rootsNeeding` column prices that mutation before the gate exists.  Move LR-8 to
M3 and the M2 expectation drops from 570 to 456.  Move LR-14 to M3 and it drops
to 529.  Move LR-12 to M3 and it drops to 437.

## 7 Eleven worked rows, quoted in full

Each row below is one root, the declaration lines in its closure, the rows the
rule gives it, its milestone, and one witness declaration per row, which is the
first line of the closure whose own text needs that row.  A reader checks a row
by opening the witness declaration in the export.

```
ROOT UnifiedAggregation.Bridge.Spin
  kind: inductive
  closure declaration lines: 1
  rows: LR-1,LR-3,LR-4
  milestone: M0
  witness LR-1: UnifiedAggregation.Bridge.Spin (inductive)
  witness LR-3: UnifiedAggregation.Bridge.Spin (inductive)
  witness LR-4: UnifiedAggregation.Bridge.Spin (inductive)

ROOT UnifiedAggregation.Bridge.Spin.casesOn
  kind: def
  closure declaration lines: 2
  rows: LR-1,LR-2,LR-3,LR-4
  milestone: M0
  witness LR-1: UnifiedAggregation.Bridge.Spin (inductive)
  witness LR-2: UnifiedAggregation.Bridge.Spin.casesOn (def)
  witness LR-3: UnifiedAggregation.Bridge.Spin (inductive)
  witness LR-4: UnifiedAggregation.Bridge.Spin (inductive)

ROOT CompCatTheory.Category.Hom
  kind: def
  closure declaration lines: 3
  rows: LR-1,LR-2,LR-3,LR-4,LR-7,LR-13
  milestone: M2
  witness LR-1: Eq (inductive)
  witness LR-2: CompCatTheory.Category.Hom (def)
  witness LR-3: Eq (inductive)
  witness LR-4: Eq (inductive)
  witness LR-7: CompCatTheory.Category.Hom (def)
  witness LR-13: CompCatTheory.Category.Hom (def)

ROOT UnifiedAggregation.Z2.one_mul
  kind: thm
  closure declaration lines: 10
  rows: LR-1,LR-2,LR-3,LR-4,LR-5
  milestone: M1
  witness LR-1: Eq (inductive)
  witness LR-2: rfl (def)
  witness LR-3: Eq (inductive)
  witness LR-4: Eq (inductive)
  witness LR-5: UnifiedAggregation.Z2.one_mul (thm)

ROOT CompCatTheory.Functor.comp
  kind: def
  closure declaration lines: 25
  rows: LR-1,LR-2,LR-3,LR-4,LR-5,LR-6,LR-7,LR-9,LR-13
  milestone: M2
  witness LR-1: Eq (inductive)
  witness LR-2: rfl (def)
  witness LR-3: Eq (inductive)
  witness LR-4: Eq (inductive)
  witness LR-5: trivial (thm)
  witness LR-6: Eq.symm (thm)
  witness LR-7: CompCatTheory.Category.Hom (def)
  witness LR-9: propext (axiom)
  witness LR-13: CompCatTheory.Category.Hom (def)

ROOT UnifiedAggregation.heq_comp
  kind: thm
  closure declaration lines: 10
  rows: LR-1,LR-2,LR-3,LR-4,LR-5,LR-6,LR-7,LR-10,LR-13
  milestone: M2
  witness LR-1: Eq (inductive)
  witness LR-2: rfl (def)
  witness LR-3: Eq (inductive)
  witness LR-4: Eq (inductive)
  witness LR-5: eq_of_heq (thm)
  witness LR-6: Eq.ndrec (def)
  witness LR-7: CompCatTheory.Category.Hom (def)
  witness LR-10: eq_of_heq (thm)
  witness LR-13: CompCatTheory.Category.Hom (def)

ROOT UnifiedAggregation.BetaChoiceFamily.mk.injEq
  kind: thm
  closure declaration lines: 25
  rows: LR-1,LR-2,LR-3,LR-4,LR-5,LR-6,LR-7,LR-9,LR-10,LR-13
  milestone: M2
  witness LR-1: Eq (inductive)
  witness LR-2: rfl (def)
  witness LR-3: Eq (inductive)
  witness LR-4: Eq (inductive)
  witness LR-5: eq_of_heq (thm)
  witness LR-6: Eq.ndrec (def)
  witness LR-7: CompCatTheory.Category.Hom (def)
  witness LR-9: propext (axiom)
  witness LR-10: eq_of_heq (thm)
  witness LR-13: CompCatTheory.Category.Hom (def)

ROOT UnifiedAggregation.Bridge.SpinConfig.flip_flip
  kind: thm
  closure declaration lines: 29
  rows: LR-1,LR-2,LR-3,LR-4,LR-5,LR-6,LR-7,LR-8,LR-9,LR-10,LR-13
  milestone: M2
  witness LR-1: Eq (inductive)
  witness LR-2: rfl (def)
  witness LR-3: Eq (inductive)
  witness LR-4: Eq (inductive)
  witness LR-5: congrArg (thm)
  witness LR-6: congrArg (thm)
  witness LR-7: LT.lt (def)
  witness LR-8: Quot (quot)
  witness LR-9: Quot.sound (axiom)
  witness LR-10: funext (thm)
  witness LR-13: LT.lt (def)

ROOT UnifiedAggregation.Bridge.Spin.noConfusionType
  kind: def
  closure declaration lines: 41
  rows: LR-1,LR-2,LR-3,LR-4,LR-5,LR-6,LR-7,LR-10,LR-11,LR-12,LR-13
  milestone: M2
  witness LR-1: False (inductive)
  witness LR-2: Not (def)
  witness LR-3: False (inductive)
  witness LR-4: False (inductive)
  witness LR-5: Nat.eq_of_beq_eq_true (thm)
  witness LR-6: Eq.ndrec (def)
  witness LR-7: Nat.brecOn (def)
  witness LR-10: Nat.eq_of_beq_eq_true._f (def)
  witness LR-11: UnifiedAggregation.Bridge.Spin.ctorIdx (def)
  witness LR-12: Nat.beq (def)
  witness LR-13: Decidable (inductive)

ROOT UnifiedAggregation.Bridge.Allocation.anonymous_eq_at_zero
  kind: thm
  closure declaration lines: 147
  rows: LR-1,LR-2,LR-3,LR-4,LR-5,LR-6,LR-7,LR-8,LR-9,LR-10,LR-11,LR-12,LR-13
  milestone: M2
  witness LR-1: Exists (inductive)
  witness LR-2: Not (def)
  witness LR-3: Exists (inductive)
  witness LR-4: Exists (inductive)
  witness LR-5: Classical.indefiniteDescription._proof_1 (thm)
  witness LR-6: Eq.symm (thm)
  witness LR-7: Subtype.val (def)
  witness LR-8: Quot (quot)
  witness LR-9: Classical.choice (axiom)
  witness LR-10: _private.Init.Classical.0.Classical.em.match_1_1 (def)
  witness LR-11: UnifiedAggregation.Bridge.Allocation.anonymous_eq_at_zero (thm)
  witness LR-12: Nat.beq (def)
  witness LR-13: Decidable (inductive)

ROOT UnifiedAggregation.Bridge.pottsUniform
  kind: def
  closure declaration lines: 533
  rows: LR-1,LR-2,LR-3,LR-4,LR-5,LR-6,LR-7,LR-8,LR-9,LR-10,LR-11,LR-12,LR-13,LR-14
  milestone: M2
  witness LR-1: Exists (inductive)
  witness LR-2: Not (def)
  witness LR-3: Exists (inductive)
  witness LR-4: Exists (inductive)
  witness LR-5: trivial (thm)
  witness LR-6: Eq.symm (thm)
  witness LR-7: Iff.mpr (thm)
  witness LR-8: Quot (quot)
  witness LR-9: propext (axiom)
  witness LR-10: funext (thm)
  witness LR-11: Nat.mul.match_1 (def)
  witness LR-12: Nat.sub (def)
  witness LR-13: Decidable (inductive)
  witness LR-14: Lean.Syntax (inductive)
```

All eleven rows are in
`/Users/oobi/Documents/lanyard-m0/spikes/s5/worked-rows.txt`.  The script picks
the first ten by label class, largest class first, and the eleventh,
`UnifiedAggregation.Z2.one_mul`, was named on the command line so that the M1
class carries a worked row too.  Its line in the labelling table is
`UnifiedAggregation.Z2.one_mul	M1	10	LR-1,LR-2,LR-3,LR-4,LR-5`, printed by:

```
awk -F'\t' '$2=="M1" {print $1"\t"$3"\t"$4}' /Users/oobi/Documents/lanyard-m0/spikes/s5/labels.tsv
```

```
UnifiedAggregation.Bridge.Spin.flip_flip	11	LR-1,LR-2,LR-3,LR-4,LR-5
UnifiedAggregation.Bridge.Z2.actOnSpin_one	14	LR-1,LR-2,LR-3,LR-4,LR-5
UnifiedAggregation.Z2.inv_mul	13	LR-1,LR-2,LR-3,LR-4,LR-5
UnifiedAggregation.Z2.mul_assoc	11	LR-1,LR-2,LR-3,LR-4,LR-5
UnifiedAggregation.Z2.mul_inv	13	LR-1,LR-2,LR-3,LR-4,LR-5
UnifiedAggregation.Z2.mul_one	11	LR-1,LR-2,LR-3,LR-4,LR-5
UnifiedAggregation.Z2.one_mul	10	LR-1,LR-2,LR-3,LR-4,LR-5
UnifiedAggregation.Z2Group	22	LR-1,LR-2,LR-3,LR-4,LR-5
```

## 8 The name normalization clause, and the five roots that need it

Five roots of roots.txt carry the guillemet quotes U+00AB and U+00BB that Lean
prints around a name component that is not an identifier.  The export name
table holds the raw component.  Without the normalization clause of the rule,
those five roots have no declaration line and the labelling stops at 565 of
570.  The five are:

```
CompCatTheory.Category.«term_≫_»
CompCatTheory.Category.«term𝟙»
CompCatTheory.Functor.«term_⋙_»
CompCatTheory.«term_⟹_»
CompCatTheory.«term_⥤_»
```

The first run printed `ROOTS read=570 labelled=565 unlabelled=5` with those five
names.  With the clause the run prints `labelled=570 unlabelled=0`.  Any
implementation of M2-PARITY must carry this clause or it loses five roots.

## 9 Every command line, verbatim

```
wc -l /Users/oobi/Documents/kanon-m2-corpus/corpus/lean-parity/uat/roots.txt
head -20 /Users/oobi/Documents/kanon-m2-corpus/corpus/lean-parity/uat/roots.txt
ls -l /Users/oobi/Documents/kanon-m2-corpus/corpus/lean-parity/uat/
fd -g 'roots*.txt' /Users/oobi/Documents/kanon-m2-corpus /Users/oobi/Documents/kanon /Users/oobi/Documents/kan-rust-lang-kanon-pin
mkdir -p /Users/oobi/Documents/lanyard-m0/spikes/s5 /Users/oobi/Documents/lanyard-m0/spikes/dev
zsh /Users/oobi/Documents/lanyard-m0/spikes/s5/run-parse.sh
python3 -P /Users/oobi/Documents/lanyard-m0/spikes/s5/parse-export.py /Users/oobi/Documents/kanon-m2-corpus/corpus/lean-parity/uat/uat.export /Users/oobi/Documents/lanyard-m0/spikes/s5/decls.json
python3 -P /Users/oobi/Documents/lanyard-m0/spikes/s5/label-roots.py /Users/oobi/Documents/lanyard-m0/spikes/s5/decls.json /Users/oobi/Documents/kanon-m2-corpus/corpus/lean-parity/uat/roots.txt /Users/oobi/Documents/lanyard-m0/spikes/s5
awk -F'\t' 'NR>1 {n++} END {print "LABELLED-ROWS " n}' /Users/oobi/Documents/lanyard-m0/spikes/s5/labels.tsv
awk -F'\t' 'NR>1 {n[$2]++} END {for (m in n) printf "MILESTONE %s roots=%d\n", m, n[m]}' /Users/oobi/Documents/lanyard-m0/spikes/s5/labels.tsv | sort
awk -F'\t' 'NR>1 {t++; if ($2=="M0"||$2=="M1"||$2=="M2") k++} END {printf "PARITY-EXPECT m2=%d of %d\n", k, t}' /Users/oobi/Documents/lanyard-m0/spikes/s5/labels.tsv
awk -F'\t' 'NR>1 {s+=$3; if($3>mx)mx=$3; if(mn==0||$3<mn)mn=$3} END {printf "CLOSURE min=%d max=%d mean=%.1f\n", mn, mx, s/(NR-1)}' /Users/oobi/Documents/lanyard-m0/spikes/s5/labels.tsv
awk -F'\t' '$2=="M1" {print $1"\t"$3"\t"$4}' /Users/oobi/Documents/lanyard-m0/spikes/s5/labels.tsv
awk -F'\t' '$2=="M0" {print $1"\t"$3"\t"$4}' /Users/oobi/Documents/lanyard-m0/spikes/s5/labels.tsv | head -4
cat /Users/oobi/Documents/lanyard-m0/spikes/s5/row-hits.tsv
cat /Users/oobi/Documents/lanyard-m0/spikes/s5/worked-rows.txt
du -sk /Users/oobi/Documents/lanyard-m0/spikes/s5
uptime
df -g /System/Volumes/Data
ls -d /Users/oobi/Documents/lanyard
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin status --porcelain | wc -l
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin rev-parse HEAD
git -C /Users/oobi/Documents/toasty rev-parse HEAD
git -C /Users/oobi/Documents/topcoat rev-parse HEAD
```

The pin worktree was not read by this spike and it was not written.  The
corpus was read only.

## 10 Load averages, date, disk

| item | value |
| --- | --- |
| date | 2026-09-09 |
| uptime before | ` 7:25  27 users, load averages: 14.08 17.59 16.53` |
| uptime after | ` 7:34  27 users, load averages: 16.15 18.55 17.66` |
| NOISY | NOISY.  The plan marks a spike NOISY above load average 4 and this window read 14.08 before and 16.15 after.  S5 has no timing number, so NOISY costs it nothing and no number is dropped. |
| bytes left under spikes/s5 | 1364 KiB by `du -sk`, which is 1372637 bytes over nine files by `ls -l` and awk: the two scripts, the runner, the parse log, decls.json at 1297302 bytes, and the four table files labels.tsv, ledger.tsv, row-hits.tsv and worked-rows.txt |
| build outputs deleted | none to delete.  No compiler ran.  decls.json is the machine intermediate of the rule and it is regenerated in 1.68 seconds by `run-parse.sh` |
| df before | 29 GiB free on /System/Volumes/Data |
| df after | 27 GiB free on /System/Volumes/Data |

The `df` reading after the work is 27 GiB, which is under the 29 GiB line of
halt blocker S0-B6.  The blocker is recorded and reported.  This spike wrote
1.3 MiB in total, so it did not cause the fall.  Nothing was deleted.

## 11 Decision record S0-D4, the S5 covering rule

- Owner: S5.  Status: RECORDED, PROPOSED.  The user rules it.
- The rule: section 1 of this file, in one paragraph, with the machine form in
  `/Users/oobi/Documents/lanyard-m0/spikes/s5/label-roots.py` and the row table
  in `/Users/oobi/Documents/lanyard-m0/spikes/s5/ledger.tsv`.
- The ledger: sixteen rows.  Ranks 1 to 13 are the census feature list of
  `uat/census.md`, unchanged.  Rank 14 is the nested inductive block, which the
  export reports once, at `Lean.Syntax`.  Rank 15 is the unsafe declaration,
  which is NEVER by the trusted base.  Rank 16 is the native reduction axiom,
  which is M3 by M3-AXIOM.
- The milestone rule: the first gate of the design verdict that needs a row
  owns that row.  Seven rows are M0, one is M1, six are M2, one is M3 and one
  is NEVER.
- The counts the rule computes: M0 89 roots, M1 8 roots, M2 473 roots, M3 0
  roots, NEVER 0 roots, and the M2 expectation 570 of 570.
- What M2-PARITY reads: the M2 expectation 570, and the `rootsNeeding` column
  of `row-hits.tsv` for the mutation, which prices the drop for every row.
- What is NOT ruled here: the milestone on any row.  Stage 0 measures and rules
  nothing, so the sixteen milestones are PROPOSED.

## 12 Gate S0-G8, COVER

| gate item | evidence | pass |
| --- | --- | --- |
| the rule paragraph | section 1, one paragraph, before every count | yes |
| 570 labelled rows counted by a printed command | `LABELLED-ROWS 570` from the awk line of section 3 | yes |
| the per-milestone counts | `MILESTONE M0 roots=89`, `MILESTONE M1 roots=8`, `MILESTONE M2 roots=473` | yes |
| at least ten worked rows | eleven, section 7 | yes |
| the M2 expectation is computed, not stated | `PARITY-EXPECT m2=570 of 570`, printed by awk over the table the rule wrote | yes |

S0-G8 PASS.

## 13 Findings

1.  LR-5 under counts Prop.  The test for the Prop row is the `thm`
    declaration kind, which the export marks.  `uat/census.md` reports 2030
    declarations whose type is a Prop against 1649 theorems, so 381 Prop typed
    definitions are invisible to the test.  The error is one sided: it can only
    hold a root at M0 that belongs at M1, and it can never move a root out of
    the M2 set, so the M2 expectation of 570 stands.  A later gate that needs
    the M0 count of 89 to be exact must read Prop-ness from
    `dev/lean-parity/census-meta.lean`, which needs elaboration.
2.  LR-7 pairs two features with two milestones.  The census row pairs
    structure projections, which the M0 emitter needs, with structure eta,
    which only the parity proofs need.  The row is kept whole so the row set
    stays the published one, and it is priced at M2, which is the higher of the
    two.  Splitting it would move roots from M2 to M0 and it is a ruling for
    the user, not for this spike.
3.  Five roots need the name normalization clause of section 8.  A gate that
    matches root names to export names without removing U+00AB and U+00BB
    labels 565 of 570 and silently loses five roots.

## 14 Window gates, the pair this agent printed

Start of the S5 window, 07:25 on 2026-09-09:

```
S0-G1  ls: /Users/oobi/Documents/lanyard: No such file or directory
S0-G2  0
S0-G2  046689a78ef6708404bd190dc86845cbee0bb36f
S0-G3  7bd502cbf44cc47f70db9f2b27ab35d77a096364
S0-G3  51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a
uptime  7:25  27 users, load averages: 14.08 17.59 16.53
df -g   29 GiB free on /System/Volumes/Data
```

End of the S5 window, 07:38 on 2026-09-09:

```
S0-G1  ls: /Users/oobi/Documents/lanyard: No such file or directory
S0-G2  0
S0-G2  046689a78ef6708404bd190dc86845cbee0bb36f
S0-G3  7bd502cbf44cc47f70db9f2b27ab35d77a096364
S0-G3  51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a
uptime  7:38  27 users, load averages: 12.63 15.30 16.40
df -g   28 GiB free on /System/Volumes/Data
git -C /Users/oobi/Documents/kanon-m2-corpus status --porcelain | wc -l  0
```

S0-G1, S0-G2 and S0-G3 pass at both ends of the window.  The corpus porcelain
is 0, so this spike wrote nothing inside the corpus.  Halt blocker S0-B6 fired:
`df -g /System/Volumes/Data` read 27 GiB free at 07:34 and 28 GiB free at
07:38, both under the 29 GiB line.  The number is reported and nothing was
deleted.
