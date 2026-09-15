# M1 URI conversion and fixed redirects

`Uri.from_text Bytes value` constructs a URI from a checked byte-list
family. It supplies the fixed redirect destination needed by Todo's
create, toggle and delete handlers. The existing `topcoat.see_other`
operation turns that URI into a redirect.

```text
mu Bytes : Type 0 :=
| bytesNil : Bytes
| bytesCons (head : Nat) (tail : Bytes) : Bytes

def main : Cx -> Uri -> SeeOther :=
  fun (cx : Cx) (request : Uri) =>
    topcoat.see_other (Uri.from_text Bytes b"/")
```

## Contract

The schema is `(0 Text : Type 0) -> (text : Text) -> Uri`. It accepts the
same nominal byte-list layouts as `Text.trim`, including direct calls,
aliases and captured calls. Unsupported layouts and open type arguments
fail before execution or emission. The adapter checks the schema type,
quantities, runtime arity, effects, placeholders and complete instance
metadata.

Conversions validate byte ranges and UTF-8 before the URI grammar, even
when the result is unused. A URI must start with one slash, contain at
most 8192 bytes and use the existing request character set. Percent
escapes require two ASCII hex digits. Absolute URLs, a leading `//`,
spaces, raw non-ASCII bytes, control characters, backslashes and fragments
are refused. Escapes remain encoded, including `%00` and `%0d`; no
percent decoding, normalization or query splitting is performed by the
interpreter. The full accepted input is preserved when the emitted URI
is converted back to text.

The emitted adapter validates this grammar before parsing
`topcoat::router::Uri`, reexported from `http` by the pinned Topcoat
router. Failures use the generated `Error::InvalidUri` variant. The
operation declares `topcoat::Error` in its foreign effect metadata and
remains synchronous. Both synchronous and database-using programs can
call it. No foreign atom or kernel primitive is added.

## Validation

```sh
zsh dev/gates.sh --stage M1-uri
_build/default/bin/lanyard.exe run --request /todos test/fixtures/uri.lan
```

The fixture returns `303 See Other` with `Location: /`. The stage gate
retains the cumulative text gate, then runs 41 URI unit checks, five CLI
test groups and three isolated mutations with clean and restored
controls. The native harness checks accepted and rejected paths, the
8192-byte boundary, byte and UTF-8 conversion failures, and redirect
composition against both generated error variants.

Prepare the native harness with `python3 -P test/lan_uri_native.py
--prepare NEW-DIRECTORY --toasty TOASTY --topcoat TOPCOAT --lock LOCK`.
Build that crate with Rust 1.98 and run `--check` with both resulting
executables, `lanyard-program` and `async_uri`. Preparation verifies
the local library commits and cleanliness before replacing git pins
with local paths. The original emitted manifest is retained.

The catalog now has 21 declarations and nine foreign types. Todo's
axiom report includes 26 foreign constants. Library pins, anchor
fingerprints and proposed trust budgets retain their existing values.
The trust policy and M0 exit stamp remain pending. Captures and tested
input hashes are recorded in `validation/stage-m1-uri/receipt.json`.
