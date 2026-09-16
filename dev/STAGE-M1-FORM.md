# M1 explicit form fields and scripted bodies

`Form.field Bytes body name` reads a named text field from a URL-encoded
body. `Bytes` is a checked nominal byte-list family, as for `Text.trim`.
This supplies explicit field access for Todo's create handler. Field
names are written in the program; automatic form records remain ahead.

```text
def title : Bytes :=
  Text.trim Bytes (Form.field Bytes b"title=++write+tests++" b"title")
```

## Contract

The schema is `(0 Text : Type 0) -> (text : Text) -> (field : Text) ->
Text`. Direct calls, aliases with the type argument fixed, and calls
inside captured local functions use the same adapter. Open type
arguments and unsupported layouts fail before execution or emission.
Runtime arguments, quantities, effects, schema type, placeholders and
complete instance metadata are checked.

Bodies contain at most 8192 bytes and 128 `name=value` fields separated
by `&`. The first `=` separates a name from its value. Empty values are
accepted. Empty names, missing `=`, empty segments and duplicate decoded
names fail. The empty body is valid but contains no fields. Looking up
a missing field fails. Names are case-sensitive and are supplied as
decoded text.

`+` decodes to space. `%HH` decodes exactly once, with either hex case.
Both names and values must decode to valid UTF-8. Every field is
validated, including fields the program does not select. Encoded
delimiters stay within their field; no Unicode normalization is done.
Malformed byte-list elements and UTF-8 also fail when the result is
unused. The native adapter validates these rules before invoking
`topcoat::router::content::Form::<Vec<(String, String)>>::from_bytes`
from the pinned library. Failures use `Error::InvalidForm`; byte-list
conversion retains `ModelByteRange` and `ModelUtf8`.

The operation is synchronous and declares `topcoat::Error` in its
foreign metadata. It can be called by both synchronous and async
database programs. No foreign type or kernel primitive is added.

## Scripted requests

```sh
_build/default/bin/lanyard.exe run --request /todos --form 'title=write+tests' test/fixtures/form-request.lan
_build/default/bin/lanyard.exe run --print-model Title test/fixtures/form.lan
zsh dev/gates.sh --stage M1-form
```

With `--form BODY`, the handler has type `Cx -> Uri -> Bytes ->
SeeOther`. The third parameter receives the original encoded body in
its checked byte-list family. `--form` requires `--request`; each option
may occur once and either order is accepted. It cannot be combined with
`--print-model`. The command validates the body before source I/O.
Malformed arguments exit 64. A missing selected field, a mismatched
handler or an exhausted step limit exits 1 with no response output.
An explicit empty body is distinct from omitting the option.

The request fixture trims the supplied title, stores a Todo in its
private database, and redirects to `/`. The interpreter supplies one
scripted request. Routes, content-type negotiation, a listener and
native request entry points remain future work.

## Validation and limits

The stage gate retains the cumulative URI gate and adds 53 unit checks,
six CLI test groups and four isolated mutations with clean and restored
controls. The native harness checks 38 observations in each of two
programs, including both generated error variants, local captures,
byte conversion errors, the body and field-count boundaries, and
malformed values outside the selected field.

Prepare it with `python3 -P test/lan_form_native.py --prepare NEW-DIR
--toasty TOASTY --topcoat TOPCOAT --lock LOCK`, build with Rust 1.98,
then run `--check` with the `lanyard-program` and `async_form` binaries.
Preparation checks local library commits and cleanliness, and retains
the original git-pinned manifest before using local paths.

The 8 KiB contract covers the current recursive byte-list runtime. A
64 KiB candidate overflowed the generated list destructor's stack in a
debug native run and was not adopted. Arbitrarily large program-created
byte lists remain a general runtime limitation. This slice does not
change their representation or certify their resource use.

The catalog has 22 declarations and nine foreign types. Todo reports
27 foreign constants. The proposed printer roster includes
`rust/form_data.ml`; its proposed budget is unchanged. Library pins,
anchor fingerprints, trust approval and the M0 exit stamp are unchanged.
Captures and tested input hashes are in `validation/stage-m1-form/`.
