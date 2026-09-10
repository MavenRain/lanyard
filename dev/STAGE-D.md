# Lanyard M0 Stage D

`zsh dev/gates.sh --stage D` checks the prior stages, the Rust erasure
suite, the driver boundary, and three erasure mutations. The Todo fixture
now supports `lanyard check --erased examples/m0-todo.lan`.

The checked kernel syntax feeds `lib/erase.ml`, which emits `lib/rir.ml`.
The fourteen term nodes distinguish direct calls, closure calls, foreign
calls, closures and their captures, cloning, products, sums, projections,
cases, lets, literals, global references, variables and runtime unit.
`surface/lower.ml` attaches checked per-model target instances, their
schema names, print rules, effect rows, type arguments and runtime arities.
Missing target metadata, incorrect foreign arity and an argument count that
differs from the emitted parameter count are explicit errors. A native name
in a value position is refused unless it takes no parameter.
Signature constructors remain ordinary data in this stage. Handler fusion
and Rust text printing are subsequent work.

Zero binders have no parameter or argument slot. One binders retain a
move representation; Many binders retain an Arc representation and explicit
clone nodes. Lifted functions retain the ownership of their captures.
The `quantity_runtime` function remains byte-identical to the fork.
An erased instantiation of a generic runtime field is refused instead of
manufacturing a placeholder. Symbolic data layout groups retain the
carried eraser's structural identities; Stage E must interpret those
layouts and implement representation conversions at expression boundaries.

The proposal says fourteen nodes but lists thirteen. Stage D adds RUnit
as the fourteenth because foreign calls such as Db.push_schema return
unit and still have observable effects. The carried kernel assigns an
unannotated empty product its minimal Prop universe. Rust erasure retains
that canonical product as runtime unit. An explicitly Prop-annotated
product remains erased, as do other proof results, universe results and
functions returning those results. This is a lowering convention; the
kernel, its universes and its conversion rules are unchanged.

The original eraser is retained byte for byte as `lib/erase_kan.ml` for
the `.kan` command and its existing goldens. The Stage D driver check
compares it with `046689a:lib/erase.ml`. It is outside the Rust erasure
path. All twelve files in the kernel carry bucket retain their bytes.
The tree now carries two erasers with the second IR. The trusted-lines gate
measures the carried eraser at 1484 lines and `lib/eterm.ml` at 117 lines,
because only the carried eraser reads that file. The place of both files in
the M0 base is an open user ruling.

The IR file measures 153 lines. The author wrote 142 lines and proposed
A_rir = 142. The review fix of the direct-call arity check added 10 lines,
and the round 3 doc-comment restatement added 1 line.
A_rir stays a proposal for the user's ruling, not a ratified allowance.
The trusted-lines gate prints its measurement and the existing symbolic
ceiling. A_sig remains pending at 104 lines, and A_emit remains unmeasured.
No M0-EXIT claim is made.
The 71-line surface/lower.ml bridge also affects output metadata and is
measured separately as trusted output plumbing. Its inclusion in the
named ceiling needs a ruling; the symbolic formula is not a measured
total or a claim that this additional file costs zero.

The tests cover quantities, eta expansion, captures, constructors, cases,
lets, unit effects, erased types and proofs, foreign metadata, and named
refusals. Three compiled mutants remove cloning, retain a Zero parameter,
and discard a unit effect. The review adds four more compiled mutants. One
drops the Arc of a Many binder. One disables the direct-call arity check.
One accepts a runtime use of an erased binder. One drops the parameter
count of a prim. The tests also refuse a partial prim application and a
runtime use of an erased binder.
Each must fail its corresponding test after a clean control passes. Mutation copies have their own Dune workspace,
retain no Git link to the source tree, and are removed after the run.

Stage E still owns Rust printing and the byte-for-byte crate golden.
The complete CLI main, schema instantiation beyond checked model instances,
first-class foreign function values, handler fusion and Rust compilation
are not claimed by this slice.
