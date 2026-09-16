# M1 HTML text and responses

`Html.text Bytes value` escapes a checked UTF-8 byte list for an HTML
text node. `Response.html Bytes body` constructs a status 200 response
with `Content-Type: text/html; charset=utf-8`.

```text
def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) =>
  Response.html Bytes (Html.text Bytes b"<hello>")
```

The body is `&lt;hello&gt;`. The browser displays the literal text
`<hello>`.

## Contract

The schemas are `(0 Text : Type 0) -> (text : Text) -> Text` and
`(0 Text : Type 0) -> (text : Text) -> Response`. Both erase the
checked nominal byte-list type argument, share the value argument and
run synchronously without declared effects. They add no foreign type
or kernel primitive.

`Html.text` replaces `&`, `<` and `>` with `&amp;`, `&lt;` and
`&gt;`. This matches the pinned Topcoat `TEXT_ESCAPES` table in
`crates/topcoat-view/src/html/escape.rs`. Quotes, Unicode and control
bytes are preserved. Existing entities are escaped again: `&lt;`
becomes `&amp;lt;`. The Rust printer uses standard string replacements,
with ampersand replacement first.

This operation is for ordinary text nodes. It does not sanitize HTML
documents or validate attributes, JavaScript, CSS or URLs. Do not use
its result as protection in those contexts. `Response.html` preserves
its input markup, so dynamic text must pass through `Html.text` before
being inserted in a text node. These operations return ordinary byte
lists and responses; they do not introduce a typed template language.

Every element must fit in a byte and the complete input must be UTF-8.
Failures propagate even when an adapter's result is unused. Empty
bodies, NUL and CR/LF are preserved. Scripted responses compute the
content length from body bytes, and body bytes cannot supply headers.

The native response construction follows the pinned Topcoat content
response idiom and the HTML content type in
`crates/topcoat-router/src/content/html.rs`. Both synchronous programs
and modules with database effects use the same adapters. Schema types,
quantities, effects, placeholders and complete instantiated rows are
checked before emission.

Aliases and captured byte-list helpers are supported. Shared foreign
ownership, foreign aggregate and closure-layout restrictions still
apply to `Response`. Recursive byte lists retain their large-value
stack limit.

## Scripted requests

```sh
_build/default/bin/lanyard.exe run --request /hello test/fixtures/html.lan
_build/default/bin/lanyard.exe run --request /todos --form 'title=%3Chello%3E' test/fixtures/html-form.lan
zsh dev/gates.sh --stage M1-html
```

The form fixture trims and stores a Todo title, then returns the escaped
stored title. Request errors produce no response bytes. The existing
plain-text and redirect entry points remain supported.

## Validation

The stage gate retains the cumulative response gate and adds 43 OCaml
checks, six CLI groups and five mutations with clean and restored
controls. The default Dune test alias also includes the HTML unit suite.

The native harness checks 25 observations in each of the two generated
error variants. It covers raw and escaped Unicode, special characters,
existing entities, control bytes, captures, plain responses and rejected
inputs. Prepare it with `python3 -P test/lan_html_native.py --prepare
NEW-DIR --toasty TOASTY --topcoat TOPCOAT --lock LOCK`, build with
Rust 1.98, then run `--check` with the `lanyard-program` and
`async_html` binaries.

The catalog has 25 declarations and nine foreign types. Todo reports
30 foreign constants. The generated catalog has 164 lines; its proposed
104-line allowance is still pending and is exceeded by 60 lines.
Library pins, source anchors, trust approval and the M0 exit stamp are
unchanged. Captures and source hashes are retained under
`validation/stage-m1-html/`.

The mutation leg ships no standalone capture trio. Its record is
`validation/stage-m1-html/stage.stdout` rows 677 to 683: the
`LAN-HTML-MUTATIONS CONTROL OK` row, five KILLED rows and
`LAN-HTML-MUTATIONS OK killed=5/5 restored=GREEN`.
