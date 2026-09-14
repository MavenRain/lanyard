# M0 trusted-code policy

`dev/trusted-policy.json` makes the remaining ceiling decisions reviewable.
Its checked-in status is `PROPOSED`, and its ruling is `null`. No allowance
or scope has been approved by this slice. M0-EXIT remains unstamped.

The proposal includes all 46 inventoried compiler sources at their Stage F
policy baseline line counts, with no additional margin:

| Group | Proposed limit |
| --- | ---: |
| Kernel | 3997 |
| Rust eraser | 1519 |
| Rust IR, A_rir | 155 |
| Printer and helpers, A_emit | 1231 |
| Generated signatures, A_sig | 104 |
| Carried eraser and erased terms | 1601 |
| Lowering, specialization and fusion | 409 |
| Other kernel-library sources | 618 |
| Frontend | 2920 |
| Driver | 212 |
| Unassigned sources | 0 |
| Total | 12766 |

This is a conservative compiler-source proposal, including the frontend
whose trust scope was previously open. It does not measure external
libraries, build tools, gate scripts or generated Rust. The proposed
base is 5516, which adds the measured eraser growth of 35 to the original
5481. The five additional compiler groups total 5760. Thus the proposal
is `5516 + 155 + 1231 + 104 + 5760 = 12766`. The separately ratified
kernel limit of 4000 still applies; the proposed group limit is 3997.

The user can revise these proposed limits and scope before ruling. An
approved policy must carry `status: "APPROVED"` and a nonempty `ruling`
reference to the user's recorded decision. These fields record a ruling;
editing them is not evidence that the user authorized it. This slice
does not modify RATIFICATIONS.md or provide an approval command.

Each group names its exact source paths, its scope and its line budget.
The kernel, eraser, IR, printer and signatures must remain included.
Other groups can be explicitly excluded only with a reason and a null
budget. Excluded sources remain measured and hashed. A policy cannot
raise the ratified kernel ceiling or silently omit a group.

After building, run the existing commands:

```sh
zsh dev/trusted-lines.sh . --output /tmp/lanyard-policy-inventory.json
zsh dev/gates.sh M0
zsh dev/gates.sh --stage F-gates
```

The inventory records the policy hash, its ruling, each group's scope
and budget, and the proposed or approved total. `PROPOSED` reports the
candidate checks but keeps the whole-base gate pending, even if a
candidate budget is exceeded. Invalid policy data or missing policy
files fail. `APPROVED` requires every included group to fit its own
budget and every group's file roster to match the current inventory.
An empty new source therefore fails scope validation even though it
adds no lines. Unused budget in one group cannot cover another group.

The combined gate rereads both source and policy evidence. A policy
change after the child measurement fails the leg even when its byte
length and budgets stay the same. The printed inventory status must
match the fresh report. An approved passing policy permits seven
passing M0 legs and exit 0. An unruled policy retains six passing legs,
one pending leg and exit 2. A failed check takes precedence over pending.
The stage wrapper verifies the matching JSON verdict in either case.
No successful command stamps M0-EXIT.

The cumulative Stage F gate includes the inventory, policy and combined
gate tests. Its printer mutation remains pending for a proposal. With
an approved policy it adds at least 50 lines, enough to exceed the
printer allowance, and must fail TRUSTED-LINES before restoring the
source. The timing leg remains informational under the existing ruling.

The approved path can also be checked without changing the shipped policy:

```sh
python3 -P test/lan_approved_policy.py
```

This probe overlays current tracked and untracked source changes into a
temporary Git checkout, records a test-only approval there, and runs the
complete mutation harness. It verifies that the original policy bytes
are unchanged. It never records a user ruling.

Validation on 2026-09-14 passed the cumulative Stage F gate, including
18 inventory tests, 17 policy tests and 36 combined-gate tests. M0 reported
`PENDING passed=6/7 pending=1 failed=0`. The separate approved probe killed
six assertion controls with no pending control; timing stayed informational.
Captures, source hashes and the measured inventory are retained under
`dev/validation/stage-f-policy/`.

The subsequent [M1 build command](STAGE-M1-BUILD.md) adds 56 driver lines.
Its measured total is 12822, while this proposal remains 12766 with a
212-line driver limit. The candidate driver check now fails, and the
unapproved whole-base gate remains pending. The Stage F captures above
record the earlier policy baseline and are not refreshed by the M1 slice.
