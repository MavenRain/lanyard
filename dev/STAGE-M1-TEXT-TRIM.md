# M1 directional text trimming

`Text.trim_start Bytes text` removes leading Unicode whitespace.
`Text.trim_end Bytes text` removes trailing Unicode whitespace. The other
end and interior bytes are preserved. Empty and whitespace-only inputs
produce empty text. Both operations use the same Unicode White_Space
property as `Text.trim`, including all 25 whitespace characters. NUL,
combining marks, zero-width spaces, byte-order marks and control separators
U+001C through U+001F are preserved. No normalization is performed.

The complete byte list is validated before trimming, including bytes at
the retained end. Invalid UTF-8 and values outside 0 through 255 retain
the existing conversion errors, even when the result is discarded. The
argument is evaluated once. Aliases, captures, shared values and alternate
closed byte-list families use the existing specialization path. Open types
and unsupported families are refused.

Both synchronous schemas have type `(0 Text : Type 0) -> (text : Text) -> Text`.
The interpreter shares the existing validated Unicode scanner. Generated
Rust uses `str::trim_start` or `str::trim_end` after byte-list conversion.
The catalog now contains 41 proposed declarations. Library pins, dependency
versions, trust allowances and milestone decisions retain their status.

```sh
_build/default/bin/lanyard.exe run --request / --form 'start=++left+&end=+right++' test/fixtures/text-trim.lan
zsh dev/gates.sh --stage M1-text-trim
```

The response body is `left  right`. The focused tests cover interpreter
semantics, complete HTTP responses, compiled native observations, metadata
drift and invalid families. Producer traces verify exactly one evaluation
for retained results, discarded results and discarded failures. Four
compiled mutations replace either directional trim with full trimming or
identity; each must compile, return every observation and fail its named
sentinel. The restored baseline must agree with every expected observation.

The cumulative gate retains `M1-text-repeat` and its predecessor gates.
Validation results and source hashes are recorded under
`dev/validation/stage-m1-text-trim/`.
