# Native Rust printer slice

This is the first Stage E slice. `lanyard emit --native FILE.lan` checks,
lowers and prints native Rust source to stdout. An unsupported definition
fails the whole request before any source is printed. The exact argument
form and `.lan` extension are required; usage errors exit 64 and compiler
errors exit 1.

```sh
zsh dev/gates.sh --stage E-native
_build/default/bin/lanyard.exe emit --native test/fixtures/native.lan
```

The printer supports naturals, runtime unit, products, projections, sums,
exhaustive cases, lets and saturated native calls. Every one of the fourteen
IR nodes has an explicit arm. Recursive family layouts, arity-only closure
layouts, closure calls, foreign types and foreign calls produce named
errors. No definition is pruned to hide an unsupported body.

Product and sum layouts are decoded with nesting-aware separators.
Identifiers encode every byte of the source name or structural type key.
Products have private fields and projections destructure them. Cases cover
exactly the declared tags and bind exactly one payload.

Zero parameters remain absent. One parameters move their values. Many
parameters use Arc. Clone uses identify shared local and case bindings;
those bindings allocate once and subsequent uses clone the Arc handle.
Expression boundaries wrap owned values or clone shared payloads when an
owned representation is required. This slice makes no allocation cost claim.

The generated Nat newtype uses canonical little-endian base-256 limbs.
Arithmetic preserves arbitrary precision, subtraction truncates at zero,
and comparisons follow false=0, true=1. Limb arithmetic fits u16 and checked
narrowing returns a typed Error. Repeated vector collection is deliberately
simple and has no performance claim. Runtime support is embedded inside
rust/emit.ml and included in its line count. The output needs only std;
the eventual application's dependency allowlist remains the M0 plan's.

The native fixture and its Rust golden are compared byte for byte. Rust
1.98.1 with edition 2024 compiles the output. Python integers supply the
oracle for 928 observations, including 1024-bit boundaries. Tests cover
quantities, aggregates, calls, branches and all five arithmetic primitives.
Sixteen invalid IR cases fail with the diagnostic each case names. Three
checked surface programs refuse emission with empty stdout and five CLI
forms fail usage. Arithmetic and Boolean mutants must compile and then
disagree with the same oracle.

The gate retains every Stage D leg and extends HOUSE to rust/ sources.
TRUSTED-LINES measures rust/emit.ml as A_emit, still pending the user's
numeric ruling. It does not ratify a new ceiling or claim M0-EXIT.

Next Stage E work: typed closure and recursive layouts, foreign templates,
model printing, handler fusion, the CLI main and the Todo crate golden with
its deleted-print-rule mutation. The Todo fixture is not yet printable.
`emit FILE.lan` without `--native` remains reserved for the crate command.
Stage F still owns the remaining driver instruments and M0 close.
