# Typed native closures

`lanyard emit --native FILE.lan` now emits typed closures, calls through
closure values and closures nested in products and sums. The Stage E gate
command includes the new fixture, golden and execution harness:

```sh
zsh dev/gates.sh --stage E-native
_build/default/bin/lanyard.exe emit --native test/fixtures/native-closures.lan
```

The Rust eraser encodes a function layout as `fn<PARAMS;RESULT>`.
Parameters use the same erased representations as lifted functions:
Zero and proof parameters are absent, One parameters are owned and Many
parameters carry Arc. The existing TyFunc and RLam constructors stay in
place. Layout generation and eta expansion share one typed traversal.
The carried `.kan` eraser and kernel retain their bytes.

The printer checks every closure's lifted function, argument arity,
capture count and capture types before returning any source. It decodes
nested function and Arc layouts with nesting-aware separators. Old
arity-only layouts fail with an explicit diagnostic. No type is guessed
from an arity or a particular use site.

Each closure representation holds a boxed `Fn(...) -> Result<_, Error>`
and a boxed duplication callback. Both require Send and Sync. Factories
move captures into these callbacks. The duplication callback reconstructs
an owned closure, so a closure remains Clone without an extra dependency.
Many captures copy Arc handles; owned captures copy their values when the
factory prepares the duplication environment and when callbacks run.
This implementation has no allocation or clone cost claim. It does not
implement a liveness pass or change the source quantity checker.

Products and sums containing functions derive Clone and Debug. They do
not derive Eq or PartialEq because functions have no structural equality.
Function-free declarations and the original native golden keep their
bytes. Closure calls propagate the same explicit runtime Error as native
calls.

Validation covers captures in source order, repeated calls, One and Many
parameters, erased parameters, nullary closures, higher-order functions,
nested captures and aggregate fields. It calls an owned clone after
dropping the original, then calls an Arc clone after dropping its original
handle. A Rust generic bound checks Send and Sync and a second checks a
future holding the closure across await. Three mutations swap captures,
drop a cloned capture and remove Send. The first two must compile and
produce different observations; the last must fail for thread safety.

Foreign printing, polymorphic foreign representations, bare named function
values and partial applications remain unsupported. Explicit lambdas can
wrap fully saturated native calls. This slice does not add the Todo crate
command or claim M0-EXIT. A_emit was measured at 437 lines for this slice
and remains pending the user's numeric ruling.
The later [recursive family slice](STAGE-E-RECURSIVE.md) supports nominal
data containing these typed closures.

The full Stage E command passed on 2026-09-10 with 29 erasure cases,
25 IR refusals, 928 arithmetic observations, 15 closure observations and
all twelve erasure/native/closure mutations. Captured output and source
hashes are in validation/stage-e-closures/.
