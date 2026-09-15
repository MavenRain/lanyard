# M1 Todo title operations

`Text.trim` and `Text.is_empty` supply the string operations used before
creating a Todo in the pinned Topcoat example. They accept a checked
byte-list family as their erased first argument:

```text
mu Bytes : Type 0 :=
| nil : Bytes
| cons (head : Nat) (tail : Bytes) : Bytes

def Bool : Type 0 := sum ((prod () : Type 0), (prod () : Type 0))
def trim : Bytes -> Bytes := Text.trim Bytes
def empty : Bytes -> Bool := Text.is_empty Bytes
def main : Bool := empty (trim b"   ")
```

Trimming removes Unicode White_Space at both ends and preserves interior
bytes, embedded NULs and non-whitespace scalars. `Text.is_empty` examines
the complete validated string. A string of spaces is nonempty until it
is trimmed. The result is the two-unit sum, with tag zero for false and
tag one for true.

Both operations validate byte ranges and UTF-8 even when their result is
unused. Malformed, truncated, overlong, surrogate and out-of-range UTF-8
encodings fail. Trimming returns a fresh value in the original nominal
family. Shared input values keep their contents.

## Checked target contract

The schemas are:

```text
(0 Text : Type 0) -> (text : Text) -> Text
(0 Text : Type 0) -> (text : Text) -> sum ((prod () : Type 0), (prod () : Type 0))
```

Specialization retains closed erased text arguments for direct calls,
aliases and captured calls. The target adapter accepts the erased layout
with an empty constructor and a constructor containing Nat and the same
recursive family. Unsupported layouts and open type parameters fail
before execution or emission. The adapter checks call metadata, schema
types, quantities, arity, effects and template placeholders.

The templates use `str::trim().to_owned()` and `str::is_empty()`, matching
`topcoat/examples/toasty-todo/src/main.rs` at commit
`51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a`, lines 133 through 135.
The operations are synchronous and add no database effect. The existing
byte-list adapters report conversion failures through the emitted
program's `Error` value. No foreign type or kernel primitive is added.

The catalog now contains 20 declarations and nine foreign types. Todo's
axiom report contains 25 foreign constants, including `Text_trim` and
`Text_is_empty`. The Topcoat signature hash records the two added rows;
library commits and source anchors keep their existing pins.

## Validation

```sh
zsh dev/gates.sh --stage M1-text
_build/default/bin/lanyard.exe run --print-model Title test/fixtures/text-ops.lan
# Title { id: 1, text: "write tests", blank: true }
```

The gate retains the cumulative model listing gate. It adds 63 unit
checks, four CLI/native test groups and five isolated mutations with
clean and restored controls. Rust 1.98 compiles the emitted source; its
111 observations check trimming, Boolean conversion and encoding errors.
The tests cover all 25 Unicode whitespace scalars and nearby scalars
that must remain in the result.

The complete gate passed. Its captures, tested input hashes and environment
details are retained in [the validation receipt](validation/stage-m1-text/receipt.json).

The new adapter is included in the compiler inventory and proposed
printer roster. The policy remains proposed, its budgets retain their
existing values, and trust and the M0 exit stamp remain pending.
