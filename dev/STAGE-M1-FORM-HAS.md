# M1 optional form fields

`Form.has Bytes body name` checks whether a decoded field name occurs in a
URL-encoded form. It returns the existing Boolean sum: tag 1 for present,
tag 0 for absent. A present field with an empty value is present. An empty
body has no fields. Names are case sensitive and are compared after form
decoding, including percent escapes and `+` as a space. The `name` argument
is already decoded text.

This lets handlers accept unchecked checkboxes and optional query fields:

```sh
_build/default/bin/lanyard.exe run --request /todos --form '' test/fixtures/form-has.lan
_build/default/bin/lanyard.exe run --request /todos --form 'completed=' test/fixtures/form-has.lan
```

The first request responds with `pending`, and the second with `completed`.
Use `Form.has Bytes (Uri.query Bytes uri) name` for query parameters. Once
presence is known, `Form.field` retrieves the value and retains its existing
missing-field error.

The entire form is validated before testing presence. Invalid percent
escapes, invalid UTF-8, empty or duplicate decoded names, missing `=`,
more than 128 fields, and bodies exceeding 8192 bytes fail even if the
requested field was found earlier or the result is unused. Absent fields
do not hide a malformed body. The interpreter and emitted Rust share
the existing form parsing rules.

The schema is `(0 Text : Type 0) -> (text : Text) -> (field : Text) ->
sum ((prod () : Type 0), (prod () : Type 0))`. Its erased argument must
be a closed byte-list family. Named aliases, captured calls, and alternate
byte-list families use the existing specialization path. Both arguments
are evaluated once, from left to right, before byte-list conversion. The
synchronous adapter declares `topcoat::Error` because parsing can fail.

Run the cumulative gate with the pinned Toasty and Topcoat checkouts and
the locked dependencies cached:

```sh
zsh dev/gates.sh --stage M1-form-has
```

It preserves `M1-uri-parts`, including the HTTP and database restart checks,
and adds interpreter, CLI and native coverage. A compiled mutation removes
decoding and whole-body validation from the presence helper; the native
checks expose its incorrect answers and accepted malformed forms.
Validation receipts live under `dev/validation/stage-m1-form-has/`.

The target catalog now contains 33 proposed declarations. Library revisions
and dependencies are unchanged. Trust allowances and the M0 exit stamp
retain their existing pending status.
