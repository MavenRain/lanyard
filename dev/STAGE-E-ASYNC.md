# Async database printing

`lanyard emit --target FILE.lan` now prints `Db.push_schema` using the pinned
awaited target rule. Functions that call it directly or through other named
functions become `async fn`. Calls evaluate in source order and propagate
errors before evaluating later expressions. Functions with no async call
remain synchronous, including pure functions in the same module.

```sh
zsh dev/gates.sh --stage E-async
_build/default/bin/lanyard.exe emit --target test/fixtures/async.lan
```

`rust/effects.ml` walks the erased expressions and propagates the checked
database effect through the direct call graph to a fixed point. It accounts
for lets, arguments, branches, aggregates and evaluated closure captures.
A lifted closure body has its own effect. Any runtime closure whose body
needs async is refused, including one that calls an async function indirectly.
Direct and mutual cycles through async functions are refused because their
futures would need a recursive representation. Synchronous recursive families
retain their existing behavior.

The target policy still validates each call against its catalog row. The
supported effect rows are empty and `[DbExec, toasty::Error]`; other effects
are refused. Empty products have the runtime unit layout needed by
`Db.push_schema`. A module using the database effect gets an explicit
`Error::Database(toasty::Error)` variant with `From`, `Display` and `source`.
The original error object survives forwarding calls. Synchronous modules
retain their previous runtime and golden bytes.

The cumulative gate retains every Stage E foreign and native leg. The new
OCaml suite checks six refusals plus propagation independent of declaration
order and the distinction between closure bodies and evaluated captures.
One printed-text row pins a mixed module. Its async function awaits the
database call and calls a synchronous helper with no await.
The Rust fixture covers direct calls, forwarding, sequencing, branches,
and a URI retained across an await. Its 17 observations check lazy start,
actual suspension, cancellation cleanup, exact call order and counts,
early error return, the original error source, shared handle counts and
the synchronous helper's result. A strict database double has no Clone
implementation and suspends each push before returning. Every observed
future must implement Send. Four mutants swallow an error, remove an await,
reverse calls or replace Arc with Rc. The first and third must compile and
disagree with the oracle; the others must fail the relevant Rust type check.

The exact golden also compiled offline with Rust 1.98.1 against
Toasty 7bd502cb and Topcoat 51caa01. A separate compile probe proves
`Future + Send` for all six generated async functions using those real API
types. Captures, the validation manifest, the probe and their hashes are in
`dev/validation/stage-e-async/`. That library build does not execute a database.

The source checker, eraser, IR, kernel and target pin bytes stay unchanged.
Their existing proof and Zero erasure rules still apply. This slice prints
runtime direct calls; fused handlers, model/schema printing, parameterized
foreign layouts, the Todo crate golden and the M0 driver remain ahead.
Target rows retain PROPOSED status. No complete Stage E or M0 exit is claimed.

TRUSTED-LINES counts emit.ml at 604 lines, foreign.ml at 55, template.ml at
71 and effects.ml at 46, totaling 776 printer lines. A_emit and the symbolic
ceiling remain pending the user's numeric ruling.
