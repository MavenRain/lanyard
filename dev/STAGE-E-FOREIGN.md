# Synchronous foreign printing

`lanyard emit --target FILE.lan` checks, lowers and prints a Rust source
module. It extends native emission with concrete foreign type paths and
synchronous constant print rules. The fixture exercises `topcoat.db`,
`topcoat.see_other`, local bindings, native forwarding calls and owned
moves. `emit --native` retains its foreign refusals and all three goldens.
The exact flag, one `.lan` path and no trailing arguments are required.
Usage errors exit 64. Compiler errors exit 1 with empty stdout.

```sh
zsh dev/gates.sh --stage E-foreign
_build/default/bin/lanyard.exe emit --target test/fixtures/foreign.lan
```

The printer checks each foreign call against its generated catalog row:
name, schema, print rule, effect row, absence of type arguments, arity and
quantities. Argument and result representations come from the catalog's
type telescope. The existing checked lowering still resolves the call;
the kernel and IR gain no constructor or axiom.

Templates are parsed into literal segments and named slots before any
substitution. Replacement text is never parsed again. Bindings must be
unique, every runtime argument must be used, One slots occur exactly once,
and unknown slots fail. Erased type bindings may be absent from a template.
Runtime arguments are evaluated once in telescope order into block-local
variables. Many arguments borrow their Arc payload at each template use;
One arguments move once. An explicit clone inside the trusted target rule
decides whether a foreign payload is copied. Neither argument reordering
nor repeated slots repeat evaluation of an argument expression.

Foreign types are opaque. No blanket Clone, Debug, equality or Send claim
is inferred from their kernel types. Moving an owned foreign value and
cloning an Arc handle are supported. Copying an opaque payload from shared
storage, cloning an owned foreign value, owned foreign closure captures,
and foreign fields in products, sums, function signatures or nominal
families are refused. In particular, the pinned SeeOther type lacks Clone;
a checked Many identity cannot silently emit a payload clone.

Effectful constants, schemas, parameterized foreign types, model printing,
handler fusion and the crate driver remain ahead. Unsupported definitions
are never pruned to make the rest print. The Todo example still refuses
its CLI family's foreign payload layout. An inline model source in
test/lan_foreign.py pins the `foreign schema Model.create` refusal. This slice does not claim EMIT-DIFF
for the Todo crate or M0-EXIT. Target rows retain PROPOSED status.

The cumulative gate retains every Stage E native leg. The new OCaml suite
checks malformed templates and IR metadata, deleted catalog entries, type
and quantity mismatches, and unsupported ownership conversions. The Rust
golden is compared byte for byte. Thirteen runtime observations use strict
API doubles to expose argument evaluation order, evaluation count, Arc
handle count, the explicit database clone and owned redirect moves.
The doubles require borrowed Cx and omit Clone on both URI and redirect
values. They validate printer behavior independently of target libraries.
Five checked surface refusals, the Todo refusal and three usage errors
exercise the driver. Three mutants change argument order, repeat argument
evaluation or drop the required Cx borrow. Two must compile and disagree
with the oracle; the missing borrow must fail the input type check.

TRUSTED-LINES counts all printer implementation files: rust/emit.ml at
575 lines, rust/foreign.ml at 52 and rust/template.ml at 71, totaling 698.
A_emit and the symbolic total still await the user's numeric ruling.
The existing target and kernel pins retain their bytes.

An additional local library build compiled the exact golden against Topcoat
51caa01 and Toasty 7bd502cb with rustc 1.98.1, edition 2024. It used the
upstream Topcoat lockfile plus the three local Toasty package entries,
Topcoat's router feature and no default features. Missing locked packages
were downloaded; both upstream tracked trees stayed clean. Toasty retained
an unrelated untracked .DS_Store. The manifest,
compiler capture and receipt hashes are in dev/validation/stage-e-foreign/.
This validates the real API types; the standard cumulative gate uses the
instrumented doubles for deterministic observations and mutations.
