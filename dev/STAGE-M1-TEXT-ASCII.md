# M1 ASCII case conversion

`Text.to_ascii_lowercase Bytes text` converts ASCII `A` through `Z` to
`a` through `z`. `Text.to_ascii_uppercase Bytes text` converts ASCII `a`
through `z` to `A` through `Z`. Both return a byte list in the input family.

Every other byte is preserved. This includes non-ASCII letters, combining
marks, whitespace, punctuation and NUL. For example, lowercasing `ÅBCß`
produces `Åbcß`, and uppercasing it produces `ÅBCß`. The operations do not
perform Unicode case folding or locale-sensitive conversion.

The complete byte list is validated before conversion. Out-of-range bytes
and invalid UTF-8 are errors even when the result is discarded. Arguments
are evaluated once. Closed type aliases, function aliases, captures and
shared input values use the existing checked text specialization path.
Open text parameters and unsupported layouts retain explicit refusals.

The interpreter uses OCaml's ASCII case conversion after byte-list
validation. Rust emission uses `str::to_ascii_lowercase` or
`str::to_ascii_uppercase` after the checked conversion to UTF-8 text.
Both catalog rows remain proposed and have no target-library effects.

```sh
_build/default/bin/lanyard.exe run --request / --form 'lower=HeLLo+&upper=world' test/fixtures/text-ascii.lan
zsh dev/gates.sh --stage M1-text-ascii
```

The gate retains the directional-trimming gate and all its predecessors.
Focused coverage checks all 128 ASCII bytes in the interpreter and compiled
Rust, non-ASCII case pairs, combining marks, alternate byte-list families,
invalid input, aliases, captures, sharing and metadata drift. Native
producer traces check single evaluation for ordinary and discarded calls,
including failing conversions. Six compiled mutations substitute the
opposite case operation, identity or full Unicode conversion. Each must
fail its named sentinel, with clean and restored baselines agreeing.
