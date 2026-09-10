# Native recursive families

`lanyard emit --native FILE.lan` prints concrete nominal families as Rust
enums. Nonempty constructor payloads own boxed tuples, giving direct and
mutual recursion a finite representation even when fields contain nested
products, sums or closures. Nullary constructors need no payload allocation.
Constructor tags and runtime fields follow declaration order. Erased fields
do not appear. Existing structural products, sums and closure goldens retain
their bytes.

```sh
zsh dev/gates.sh --stage E-native
_build/default/bin/lanyard.exe emit --native test/fixtures/native-recursive.lan
```

The eraser closes each declaration's existing RData metadata over referenced
families. It includes families mentioned only by signatures and follows
cross-family fields until no new family remains. This closes a gap where an
identity function had a nominal type but no constructor layouts because it
neither constructed nor matched the value. The kernel, carried `.kan`
eraser and fourteen-node Rust IR retain their bytes and constructors.

The printer validates nominal metadata before returning source. Tags must be
canonical nonnegative integers contiguous from zero. Duplicate descriptions
must agree. Constructor and case arities, tag coverage, field types, result
conversions and nested family references are checked. Missing metadata and
unsupported layouts return named errors instead of partial source.

Case payloads move out of their boxes. Source Many binders allocate Arc
storage and clone handles on repeated use; One values stay owned. Nominal
enums derive Clone and Debug. Aggregates containing nominal data omit
structural equality because reachable fields can contain functions.
Copies may recursively clone owned payloads. This slice makes no allocation,
clone-cost, stack-depth or tail-call optimization claim.

Validation includes lists, branching trees with order-sensitive observations,
mutually recursive families, erased constructor fields, repeated shared
values, owned moves, cloned values after dropping their originals, closures
capturing recursive values, recursive values containing closures, nested
aggregates, and Send/Sync plus a future holding data across await.

The byte-compared golden runs under 13 execution observations that
test/lan_recursive.py supplies. The oracle also writes a signature-only
source in a temporary directory and compiles it. Eighteen invalid IR rows
pin diagnostics, and one positive row checks duplicate metadata. Three
mutants reverse same-typed binders, change a constructor tag, and remove
recursive indirection. The first two must compile and disagree with the
oracle. The last must fail with an infinite-size diagnostic. All previous
Stage E legs remain in the gate.

Polymorphic erased fields (including `foreign #0` and `any`), empty families,
foreign types and foreign calls remain unsupported. The former concrete
recursive surface refusal is now a successful execution suite; the second
surface refusal pins the unsupported polymorphic layout instead.

This continues Stage E and does not claim M0-EXIT. Foreign templates, model
printing, handler fusion, the crate command and Todo golden remain ahead.
The current line measurements are 1500 for lib/erase.ml and 535 for
rust/emit.ml. A_emit remains pending the user's numeric ruling.
