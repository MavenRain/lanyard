# M1 text repetition

`Text.repeat Bytes text count` concatenates `count` copies of the complete
text. Counts are arbitrary natural numbers. Zero produces empty text, and
empty text stays empty for any count. UTF-8 bytes, embedded NULs, whitespace
and combining characters are preserved without normalization.

Both arguments run once in source order before conversion. The complete
text is validated even for count zero or an unused result. The text family
must be a closed byte list, while the second argument retains its Nat type.
Aliases, captures, shared values and alternate byte-list families use the
existing specialization path. Partial applications retain its restrictions.

The result size must fit the compiler host's maximum OCaml string length.
The interpreter checks the product with arbitrary precision before narrowing
the count. It constructs logarithmically many immutable doubled chunks.
Generated Rust retains the same size bound, checks its own machine-size
arithmetic and reserves output storage fallibly before appending copies.
Empty text needs no count narrowing or output allocation. Size failures
return an interpreter error or the native `Arithmetic` error. The bound is
the host string limit, not available memory. A size inside the bound can
exhaust memory. The interpreter then stops with the OCaml runtime
`Out_of_memory` exception, or the operating system stops the process.
Generated Rust returns `Arithmetic` only when the allocator refuses the
reservation. The native `Arithmetic` error keeps its display text
`natural limb invariant failed`. Callers must match the variant, not the
text. Invalid text retains the existing byte-range and UTF-8 conversion
errors.

The synchronous schema has type `(0 Text : Type 0) -> (text : Text) ->
(count : Nat) -> Text` and declares `topcoat::Error` for fallible calls.
The catalog contains 39 proposed declarations. Library revisions, dependency
versions, trust allowances and milestone rulings retain their existing status.

```sh
_build/default/bin/lanyard.exe run --request / --form 'text=ab&count=3' test/fixtures/text-repeat.lan
zsh dev/gates.sh --stage M1-text-repeat
```

The response body is `ababab`. The focused suite covers 96 interpreter checks,
78 native observations and complete CLI responses. Compiled producer traces
and dependent interpreter database writes check evaluation order and counts.
Coverage includes invalid text at count zero, discarded failures, arbitrary
counts, Unicode, aliases, captures, family refusals and metadata drift.

Four compiled mutations target a fixed single copy, one fewer copy, rejection
of empty input and narrowing to one count byte. Each must compile, return the
full observation count and fail its named sentinel. Clean and restored
baselines must agree with all expected rows.

The cumulative gate retains `M1-text-replace`, including native sessions,
HTTP, serve and database restart checks. Captures and source hashes live in
`dev/validation/stage-m1-text-repeat/`.
