# M1 URI path and query adapters

`Uri.path Bytes uri` returns the path before the first `?`.
`Uri.query Bytes uri` returns everything after that first separator,
without the separator itself. A missing query and a present empty query
both produce an empty byte list. `Uri.to_text` retains the full URI when
that distinction matters.

```sh
_build/default/bin/lanyard.exe run --request '/hello?name=Ada+Lovelace' test/fixtures/uri-parts.lan
_build/default/bin/lanyard.exe serve --out /tmp/lanyard-hello --listen 127.0.0.1:3000 test/fixtures/uri-parts.lan
```

The fixture matches `/hello` independently of the query and responds with
`hello Ada Lovelace`. An absent or empty query returns `hello world`.
For nonempty queries, the fixture requires the `name` field. Other paths
are echoed without their query.

The adapters preserve percent escapes, their case, `+`, repeated slashes,
dot segments and further `?` bytes. They do not decode or normalize either
component. `Form.field Bytes (Uri.query Bytes uri) b"name"` applies the
existing URL-encoded form decoder, including its UTF-8, duplicate-name,
field-count and missing-field checks. A URI can contain valid raw query
text that is not a valid form. Form errors remain handler errors, which
the HTTP server converts to 500. Malformed URI escapes fail at the request
boundary with 400, or exit 64 for `run --request`.

Both schemas are `(0 Text : Type 0) -> (uri : Uri) -> Text`. The erased
output argument must be a closed byte-list family. The shared URI argument
is evaluated once. Named aliases, captured values and alternate output
families follow the existing specialization path. The adapters are
synchronous and declare no library effect.

The complete origin-form URI is validated before either component is
extracted, even if the result is unused or the invalid bytes are in the
other component. The existing 8192-byte bound applies to the whole URI.
Native callers receive the existing `InvalidUri` adapter error for values
outside that contract. HTTP parser behavior, including fragment removal
before the adapter sees a request, follows the pinned Topcoat transport.

Run the cumulative gate with the pinned libraries and cached dependencies:

```sh
LANYARD_TOASTY=/path/to/toasty LANYARD_TOPCOAT=/path/to/topcoat \
  zsh dev/gates.sh --stage M1-uri-parts
```

The gate preserves `M1-database`, adds interpreter and CLI coverage, and
compiles native adapter checks. The HTTP suite also exercises query routing,
decoding, errors and recovery over real sockets. A compiled mutation removes
the four native component-validation sites and must exhibit the precise
invalid-value acceptance rejected by the original program. Validation
captures and source hashes are in `dev/validation/stage-m1-uri-parts/`.

The catalog has 32 proposed declarations and nine foreign types. The Todo
axiom report has 37 foreign constants and three definitions. The generated
catalog has 206 lines, 102 above its proposed 104-line allowance. Trust
approval and the M0 exit stamp remain pending. Library revisions, source
anchors and dependencies retain their existing pins.
