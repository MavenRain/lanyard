# M0 compiler source inventory

TRUSTED-LINES now measures every current OCaml compiler source and saves
the file paths, newline counts, byte counts and SHA-256 hashes. The
inventory includes the generated target module and the handler fusion
module used by crate emission. Removing a required file or an entire
compiler source directory fails the check, including directories that
the older measurement blocks could skip.

After building the compiler, write a new inventory file:

```sh
python3 -P dev/trusted-inventory.py --output /tmp/lanyard-trust.json
zsh dev/trusted-lines.sh . --output /tmp/lanyard-trust-with-counts.json
```

The Python command defaults to its own repository. Its optional first
argument selects another root. The shell command takes the root before
`--output`. The shell command rejects a first argument that starts with
`-`: it prints a usage row and fails before it writes anything.
An output file must be new and its parent must exist. Neither
command builds the compiler or generates signatures. The existing build
must have produced `_build/default/target/target_generated.ml`.

The JSON is deterministic and uses paths relative to the measured root.
Both commands print the SHA-256 of those exact JSON bytes, even when no
output file was requested. Lines count newline bytes, as `wc -l` does;
comments and blank lines count, and a final unterminated line adds no
newline. Byte counts and hashes include the complete contents.

## Measured groups and open decisions

The source inventory at this slice is:

| Group | Files | Lines | Current treatment |
| --- | ---: | ---: | --- |
| Kernel | 12 | 3997 | Existing 4000-line limit. |
| Rust eraser | 1 | 1519 | Original base reserved 1484. |
| Rust IR | 1 | 155 | A_rir is open. |
| Printer and helpers | 8 | 1231 | A_emit amount and scope are open. |
| Generated signatures | 1 | 104 | A_sig is open. |
| Carried eraser and erased terms | 2 | 1601 | Scope is open. |
| Lowering, specialization and fusion | 3 | 409 | Scope is open. |
| Other kernel-library sources | 10 | 618 | Scope is open. |
| Frontend | 7 | 2920 | Scope is open. |
| Driver | 1 | 212 | Scope is open. |

The fusion module accounts for 218 of the bridge's 409 lines. Earlier
measurements counted only lowering and specialization, at 191 lines.
The additional library, frontend and driver groups make the remaining
OCaml source scope explicit. These are candidate measurements, and do
not expand the ratified twelve-file kernel bucket.

The required path roster covers the current `.ml` and `.mli` compiler
sources. The scanner also inventories new `.ml`, `.mli`, `.mll` and
`.mly` paths under `lib`, `surface`, `rust`, `bin` and `target`, including
subdirectories. New paths go into an `unassigned` group whose scope is
pending. Removing or moving a required path needs an explicit roster
update. Symlinks and nonregular source files fail before their contents
are read. The shell kernel bucket must match the inventory's twelve
paths. This source census excludes build scripts, vendor sources,
tests, and emitted Rust; it is not a ruling on the whole trust base.

The JSON leaves all three allowances and the whole-base ceiling total
as `null`. It retains `5481 + A_rir + A_emit + A_sig`, marks base growth
and source scope as pending, and leaves M0-EXIT unstamped. A valid
inventory with a passing kernel check exits zero while reporting
`PENDING`. Missing files, unreadable paths, invalid output and kernel
overflow fail. Adding 50 printer lines changes the measurements and
hashes, but the allowance control remains pending until the user rules
on A_emit and its scope.

## M0 evidence and validation

`zsh dev/gates.sh M0` writes `trusted-inventory.json` beside its command
logs. The TRUSTED-LINES leg records that file's path and hash. Before
accepting the measurement, the runner requires the complete inventory,
checks its stdout hash and compares its data with a fresh measurement
of the current compiler sources. Missing, malformed, stale or changed
evidence fails the leg. The runner also requires an empty stderr from
the TRUSTED-LINES child: one stderr byte fails the leg. A repeated
mutation check removes only its own
prior inventory before invoking the child. Other legs still run after
an inventory failure.

The implementation checks remain part of the cumulative Stage F gate:

```sh
python3 -P test/lan_trusted_inventory.py
python3 -P test/lan_m0_gates.py
zsh dev/gates.sh --stage F-gates
```

The inventory suite exercises every required path, omitted directories,
fusion counts, new sources, kernel boundaries, links, special files,
deterministic output and output refusal. The gate tests cover missing
and reused evidence, source drift, stdout hash mismatch and continued
execution after failure. Captures and the measured inventory live under
`dev/validation/stage-f-trust/`.
