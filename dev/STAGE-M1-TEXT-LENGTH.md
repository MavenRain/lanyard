# M1 text byte lengths

`Text.length Bytes text` returns the number of UTF-8 bytes as a `Nat`.
Empty text returns zero. Whitespace, embedded NULs, and multibyte characters
retain their bytes: `b"é"` has length 2 and `b"😀"` has length 4. The adapter
does not normalize text or count Unicode characters or grapheme clusters.

The input must be a closed byte-list family. Named aliases, captured calls,
and alternate byte-list families use the existing specialization path.
Byte values outside 0..255 and invalid UTF-8 fail before measurement,
including when the result is unused. The argument is evaluated once before
conversion. Form and URI limits still apply when those adapters supply the
text; `Text.length` adds no input length limit.

The native adapter uses Rust's byte length and converts its complete
little-endian representation into a canonical `Nat`, without narrowing.
The interpreter uses the validated string's byte length. The schema is
`(0 Text : Type 0) -> (text : Text) -> Nat`, synchronous with no foreign
error effect. Invalid byte-list representations retain the existing runtime
conversion errors.

The fixture measures a decoded form field:

```sh
_build/default/bin/lanyard.exe run --request /length --form 'text=%C3%A9' test/fixtures/text-length.lan
zsh dev/gates.sh --stage M1-text-length
```

The response body is `2`. The cumulative gate preserves `M1-form-has`,
including the HTTP, serve and database restart checks. It adds 44 interpreter
checks, four CLI groups and 34 native observations. Two compiled mutations
must expose counting Unicode characters and narrowing the count to one byte.
Receipts belong under `dev/validation/stage-m1-text-length/`.

The catalog contains 34 proposed declarations. Library pins and dependencies
retain their revisions. Trust allowances and milestone exits remain pending.
