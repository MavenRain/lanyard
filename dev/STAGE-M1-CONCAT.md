# M1 text concatenation

`Text.concat Bytes left right` joins two checked UTF-8 byte lists in
argument order. It supports empty strings, Unicode and control bytes.
Literal markup and escaped text can now form one HTML response body:

```text
Response.html Bytes
  (Text.concat Bytes b"<h1>"
    (Text.concat Bytes (Html.text Bytes title) b"</h1>"))
```

The `concat-form.lan` fixture reads and trims a submitted title, stores
it in a Todo model, escapes the stored text and returns a heading.

```sh
_build/default/bin/lanyard.exe run --request /todos --form 'title=%3Chello%3E' test/fixtures/concat-form.lan
zsh dev/gates.sh --stage M1-concat
```

The response body is `<h1>&lt;hello&gt;</h1>`.

## Contract

The schema is `(0 Text : Type 0) -> (left : Text) -> (right : Text) ->
Text`. Its type argument is erased, both values have shared quantity and
the operation is synchronous with no declared effects. The selected
nominal family must have the checked byte-list layout.

Each argument is evaluated once, left to right. Both arguments must
independently contain bytes in `0..255` and valid UTF-8. Splitting a
multibyte character between two lists is rejected even if their combined
bytes would be valid. Failures propagate when the result is unused.

The interpreter joins the validated strings. The Rust printer converts
both checked lists to strings, uses standard `String` concatenation and
converts the result back to the selected list family. No dependency or
foreign type is added. Complete schema metadata and print placeholders
are checked before emission.

Concatenation preserves literal bytes. It performs no escaping or
sanitization. Use `Html.text` for dynamic text in ordinary HTML text
nodes; that operation does not validate attributes, scripts, styles
or URLs.

Aliases and captured helpers work. As with the existing foreign adapter
lowering, partially applied value arguments are rejected. Use an
explicit lambda to capture a prefix:

```text
let append : Bytes -> Bytes := fun (value : Bytes) =>
  Text.concat Bytes prefix value in
append b"suffix"
```

The recursive byte-list representation retains its large-value stack
limit. This slice adds no new size limit or streaming representation.

## Validation

The cumulative stage retains the HTML gate and adds 33 OCaml checks,
seven CLI groups and four mutations with clean and restored controls.
The default Dune test alias includes the concat unit suite.

The native harness checks 19 observations in the synchronous error
variant and 20 in the database error variant. It checks ordering, empty
values, Unicode, controls, captures, aliases, shared inputs, escaped
composition, invalid bytes, invalid UTF-8 and unused failures. The
database case creates a row in the left argument, then updates and
deletes it in the right argument. Reversal or repeated evaluation fails.
Four test modules keep a private `contains` helper. This slice changes
the copy in `test/lan_concat.ml` only.

Prepare native checks with `python3 -P test/lan_concat_native.py
--prepare NEW-DIR --toasty TOASTY --topcoat TOPCOAT --lock LOCK`, build
with Rust 1.98, then run `--check` with the `lanyard-program` and
`async_concat` binaries. Captures and source hashes live under
`validation/stage-m1-concat/`.

The catalog now has 26 declarations and nine foreign types. Todo reports
31 foreign constants. The generated catalog has 170 lines, exceeding the
pending proposed 104-line allowance by 66. Library pins, source anchors,
trust approval and the M0 exit stamp retain their previous status.
