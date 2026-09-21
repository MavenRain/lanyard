# M1 prefix and suffix matching

`Text.starts_with Bytes text needle` checks whether `text` begins with
`needle`; `Text.ends_with Bytes text needle` checks its end. Both return
the standard Boolean sum, with variant 1 for a match and variant 0 for
a miss. Matching is case-sensitive and preserves whitespace, UTF-8 bytes
and embedded NULs. It performs no Unicode normalization. An empty needle
matches every valid text, including empty text. A longer needle cannot match.

Both arguments must use the same closed byte-list family. Aliases,
captures, shared values, computed inputs and alternate families follow
the existing specialization path. Each argument is evaluated once, in
source order. Both complete byte lists are validated before matching,
including when a result is unused, the needle is empty, or an invalid
byte occurs beyond a matching boundary. Invalid UTF-8 and bytes outside
0..255 retain the existing conversion errors. The adapters add no input
limit; limits from Form and URI adapters still apply to their inputs.

Each synchronous schema has type `(0 Text : Type 0) -> (text : Text) ->
(needle : Text) -> sum ((prod () : Type 0), (prod () : Type 0))` and declares
no foreign error effect. Native emission uses Rust's `str::starts_with`
and `str::ends_with` after checked conversion. The interpreter uses
OCaml's corresponding string functions. Conversion takes linear time in
the combined input size; matching compares at most the needle length.

The fixture uses both adapters to classify a URI path:

```sh
_build/default/bin/lanyard.exe run --request '/static/main.css?v=1' test/fixtures/text-boundaries.lan
zsh dev/gates.sh --stage M1-text-boundaries
```

The response body is `stylesheet`. Query text is excluded by `Uri.path`.
The cumulative gate retains `M1-text-contains` and adds 142 interpreter
checks, 18 CLI/native test groups and 560 native observations. Ten compiled
mutations cover substring matching, swapped boundaries, reversed arguments,
rejected empty needles and skipped needle validation. Both operations have
clean and restored baselines. Captures belong under
`dev/validation/stage-m1-text-boundaries/`.

The catalog contains 37 proposed declarations. Library revisions and
dependencies are unchanged. Trust allowances and milestone exits remain
pending.
