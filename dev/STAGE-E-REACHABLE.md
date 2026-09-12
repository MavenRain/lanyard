# Crates from the main dependency graph

`emit --crate DIR FILE.lan` now selects the checked definitions reachable
from `main` before connection specialization, model printing and erasure.
Unused helpers can contain layouts or operations that the Rust printer
does not support. They no longer prevent an independent main from emitting.
The complete source must still parse and typecheck, including unused code.

```sh
zsh dev/gates.sh --stage E-reachable
_build/default/bin/lanyard.exe emit --crate /tmp/lanyard-small test/fixtures/reachable.lan
```

The fixture computes 31 through a captured closure, an indirect call and
an aliased result. Its unused generic database helper and unsupported model
field are checked but omitted from the crate. The resulting Rust compiles
without database libraries. The generated manifest retains the four
dependencies required by the target contract.

The pass follows global references in bodies, types, shape payloads,
addresses, motives, branches and recursive family declarations. It also
follows retained foreign schema arguments. Those arguments preserve model
identity when two models have the same structural type. A model selected
only by `Db.connect` still gets its schema. Each reachable name is visited
once; source declaration order stays fixed.

Selection is conservative. A reference in a type, an erased argument or
an untaken branch is retained. This pass does not evaluate branches or
fuse handlers. Reachable unsupported code still refuses before the driver
creates any output. The complete checked environment stays available to
lowering for type evaluation. `check`, `axioms`, `emit --native` and
`emit --target` continue to process the full source.

The cumulative gate includes all preceding stages. The new tests execute
six Rust observations covering closures, aliases, mutual recursion and
nested recursive layouts. They check six refusals, preserve three selected
model schemas and require deletion of a transitive function to fail Rust
compilation. The existing crate golden retains its bytes because all of
its runtime definitions are reachable.

`test/fixtures/reachable-models.lan` connects three schemas, creates rows
with the same key in two distinct models, and reads both back. A fourth,
unused model has an unsupported field. The pinned SQLite execution is
recorded under `dev/validation/stage-e-reachable/`.

`rust/reachable.ml` joins the measured printer total. The kernel and the
numeric allowances retain their existing rules. Handler fusion, the frozen
M0 Todo golden and the M0 timing and exit gates remain ahead. The plan puts
the build command and interpreted run command at M1.
