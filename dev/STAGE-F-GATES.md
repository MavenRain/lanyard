# Combined M0 gate

Run the seven legs from M0-PLAN section 9:

```sh
zsh dev/gates.sh M0
zsh dev/gates.sh M0 --output /tmp/lanyard-m0-report
```

The output directory must be new. By default, a fresh directory under
`.gatework/` holds each check's stdout and stderr, their hashes, the raw
timing JSON and `report.json`. Every default run keeps its own
`.gatework/m0.*` directory as evidence. The command removes no directory,
because the printed `M0-REPORT` path must stay readable after the run.
The operator prunes `.gatework/` when the evidence is no longer needed.
The command builds through `dunecho`, then
checks and erases the Todo corpus, compares its classified axioms with
the golden, and runs HOUSE. These prerequisites supplement the seven
named legs; they do not replace one.

| Leg | Assertion |
| --- | --- |
| R0-COUNT | The compiler census equals the SPEC fenced block. |
| R0-TARGET | The generated signatures pass the closed-atom checks. |
| TARGET-PIN | PIN, ANCHOR and DIFF all pass against the source libraries. |
| TRUSTED-LINES | The kernel bound passes; the whole-base ruling is pending. |
| KERNEL-CARRY | The carry ledger matches the pinned kernel commit. |
| EMIT-DIFF | The complete Todo crate equals the golden, without normalization. |
| M0-TIME | The compiler timings and Go refit complete, with no speed bound. |

Every independent leg runs after a successful build, including after
an assertion fails. A failed build stops before any existing executable
can supply results. Each child needs both a zero exit and its complete
success markers. The corpus prerequisites assert their bytes too: the
check must print nothing, and the erasure must print its pinned `erased`
lines. Deadlines kill the child's process group and count as failures.
A descendant in another session can survive and hold the captured pipes,
so the read after the kill has a 30-second bound. The leg then reports
exit 124 with the bytes it has. Per-check logs retain the child's bytes
without normalization.
M0-TIME always requests the thirteen-package Go refit and preserves its
raw samples. A noisy or longer-than-one-minute run remains informational.

Exit 1 means failure, exit 2 means pending rulings, and exit 0 is reserved
for a complete green gate. Failure takes precedence over pending. The
current unruled tree produces six passing legs and one pending leg.
Invalid command arguments also use argparse's exit 2, print usage to
stderr and produce no report. Read `report.json` to distinguish a
completed pending run from an invocation error.

A program must never read the verdict from a stdout row. The gate replays
the complete child stream of TRUSTED-LINES and M0-TIME, so a child can
print text that looks like a gate row. Take the report path from the LAST
`M0-REPORT ` row, because that row is always the gate's own final row.
Then read `summary` from that file. `python3 -P dev/m0-gates.py
--verify-stage-log <log>` does exactly this: it exits 0 only for a saved
gate log whose last report holds the pending ruling.

## The trust decision remains open

`dev/trusted-lines.sh` currently enforces the kernel's 4000-line bound.
Its success does not enforce the M0 formula. The combined runner marks
that result PENDING and returns a nonzero exit. It cannot certify the
whole base by treating measured counts as approved allowances. A later
slice must implement the user's numeric and scope rulings before this
leg can pass. The command never writes the user's M0-EXIT stamp.

The current measurements are:

| Component | Lines | Decision |
| --- | ---: | --- |
| Kernel | 3997 | Existing limit 4000. |
| Rust eraser | 1519 | Original base reserved 1484. |
| Rust IR | 155 | A_rir is open. |
| Printer and seven helper modules | 1231 | A_emit amount and scope are open. |
| Generated signatures | 104 | A_sig is open. |
| Carried eraser | 1484 | Whole-base treatment is open. |
| Carried erased terms | 117 | Whole-base treatment is open. |
| Target lowering and specialization | 191 | Whole-base treatment is open. |

The kernel plus Rust eraser measures 5516, which is 35 above the fixed
5481 base. Including the IR, complete printer and signatures measures
7006. Including the additional three measured groups yields 8798.
These are inventories, not proposed or ratified limits. The base growth
and the additional files need explicit treatment in the user ruling.

## Validation and controls

```sh
zsh dev/gates.sh --stage F-gates
python3 -P test/lan_m0_gates.py
python3 -P test/lan_m0_gate_mutations.py
```

The stage command retains the cumulative F-axioms compiler and emission
tests, the timing tests, and the new gate tests. It runs M0 once at the
end. Its success line is `STAGE-F-GATES OK m0=PENDING`: this validates
the implementation while preserving the unresolved M0 result.

The stage saves the gate stdout under `.gatework/`, like the gate report
directories, and removes that scratch log when the stage exits. It reprints
every row in order, and then verifies the report. An exit 2 alone is not sufficient, because argparse
also exits 2. The stage pins the pending ruling: it accepts only a report
with status PENDING, exit code 2, six passing legs, one pending leg and
no failed check. The slice that implements the user rulings must also
change this stage, so that it accepts a green report and a zero exit.

Five assertion controls mutate the actual census, add a tenth atom,
flip a copied upstream anchor byte, change a carried kernel file and
delete the Model.create print-rule row. Each must fail its designated
leg with the expected diagnostic, then pass after restoration. Scratch
compilers must build successfully. An additional control makes the
census command print correct bytes and exit 7; R0-COUNT must reject it.

The specified 50-line emitter control exposes the remaining gap: the
kernel-only script still exits 0, while the combined leg stays PENDING.
It is reported as pending, never as a killed control. M0-TIME has no
speed mutation because section 9 explicitly makes it informational.
Thus the plan's prose about seven mutations resolves to five killed
assertion controls, one unresolved assertion control and one
informational leg. M0-EXIT remains open.

Captures and source hashes are under `dev/validation/stage-f-gates/`.
Earlier stage captures retain their historical bytes.
