# M1 substring search

`Text.contains Bytes text needle` returns a Boolean indicating whether
`needle` occurs anywhere in `text`. Matching is case-sensitive and preserves
UTF-8 bytes, whitespace and embedded NULs. It performs no Unicode
normalization: `b"é"` and a decomposed accented `e` remain distinct.
An empty needle matches every valid text, including empty text.

Both inputs must use the same closed byte-list family. Aliases, captures,
computed arguments and alternate families use the existing specialization
path. Each argument is evaluated once, in source order. Both complete byte
lists are validated before searching, including when a result is unused or
an empty needle would match. Invalid UTF-8 and bytes outside 0..255 retain
the existing conversion errors. The adapter adds no input limit; limits
from Form and URI adapters still apply when they supply the inputs.

Native emission uses Rust's `str::contains` after checked conversion. The
interpreter uses prefix fallback with immutable maps and total lookups,
avoiding repeated scans of overlapping prefixes. For text length `n` and
needle length `m`, it takes O((n + m) log(m + 1)) time and O(m) extra space.

The synchronous schema is `(0 Text : Type 0) -> (text : Text) ->
(needle : Text) -> sum ((prod () : Type 0), (prod () : Type 0))`.
Variant 1 means a match; variant 0 means no match. It declares no foreign
error effect.

The fixture searches a decoded form field:

```sh
_build/default/bin/lanyard.exe run --request /search --form 'action=autosave' test/fixtures/text-contains.lan
zsh dev/gates.sh --stage M1-text-contains
```

The response body is `found`. The cumulative gate retains `M1-text-length`
and adds 73 interpreter checks, eight CLI/native test groups and 280 native
observations. The interpreter checks include an exhaustive comparison
against a separate substring oracle and long overlapping matches and misses.
Five compiled mutations must expose equality-only matching, prefix-only
matching, reversed arguments, rejection of empty needles and skipped needle
validation. Captures belong under `dev/validation/stage-m1-text-contains/`.

The catalog contains 35 proposed declarations. Library revisions and
dependencies are unchanged. Trust allowances and milestone exits remain
pending.
