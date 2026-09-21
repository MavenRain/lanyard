# M1 text replacement

`Text.replace Bytes text needle replacement` replaces every non-overlapping
occurrence of `needle`, searching left to right. Replacement text is copied
literally and is not searched again. Matching is case-sensitive, preserves
UTF-8 bytes and embedded NULs, and performs no Unicode normalization.
An empty needle inserts the replacement at every Unicode scalar boundary,
including at the beginning and end. Empty input then yields one
copy of the replacement. Combining characters remain separate scalars.

All three arguments use the same closed byte-list family. Aliases, captured
calls, shared values and alternate families follow the existing text
specialization path. Arguments run once each in source order, before
conversion. Complete inputs are validated in the same order, even when
there is no match, the needle is empty, or the result is unused. Invalid
UTF-8 and byte values outside 0..255 retain the existing conversion errors.
The adapter adds no input limit; Form and URI limits still apply upstream.

The synchronous schema has type `(0 Text : Type 0) -> (text : Text) ->
(needle : Text) -> (replacement : Text) -> Text`, with no foreign error
effect. Generated Rust calls `str::replace` after checked conversion. The
interpreter shares the immutable prefix-fallback table used by substring
search and assembles the result from disjoint input spans. Nonempty search
takes O((n + m) log(m + 1) + output) time for input sizes n and m. Empty
needle insertion walks the input bytes and inserts only at scalar boundaries.

The form fixture exposes all three inputs:

```sh
_build/default/bin/lanyard.exe run --request / --form 'text=banana&needle=na&replacement=!' test/fixtures/text-replace.lan
zsh dev/gates.sh --stage M1-text-replace
```

The response body is `ba!!`. Focused checks cover 54 interpreter cases,
2,835 small-input oracle comparisons, six CLI/native groups and 461 native
observations. Compiled argument producers record evaluation order and counts,
including unused results and conversion failures. A database fixture makes
skipped, repeated or reordered calls observable. Six compiled mutations
target first-only replacement, swapped arguments, empty-needle handling and
each input conversion, with clean and restored baselines.

The cumulative gate retains `M1-text-boundaries`, including native sessions,
HTTP, serve and database restart coverage. Captures and source hashes belong
under `dev/validation/stage-m1-text-replace/`. The catalog now contains 38
proposed declarations. Library revisions and dependencies are unchanged.
Trust allowances and milestone exits remain pending.
