# M1 UTF-8 text responses

`Response.text Bytes body` builds a `Response` with status 200 and
`Content-Type: text/plain; charset=utf-8`. `Bytes` is a checked nominal
byte-list family. The schema is `(0 Text : Type 0) -> (text : Text) ->
Response`; its type argument is erased and its byte-list argument is
shared. The operation is synchronous and adds no foreign type or kernel
primitive.

```text
def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) =>
  Response.text Bytes b"Hello from Lanyard!"
```

## Contract

Every element must fit in a byte, and the complete body must be valid
UTF-8. Invalid values fail even when the constructed response is unused.
Empty bodies, Unicode, NUL and CR/LF bytes are preserved. Text is neither
trimmed nor HTML-escaped; it always has the plain-text content type.
Body bytes cannot become response headers.

The native adapter follows the pinned Topcoat `content_response` idiom
at `crates/topcoat-router/src/response.rs`: construct `Response<Body>`
from a string, then set the static content-type header. Header insertion
requires a mutable local because the pinned API exposes `headers_mut`.
Byte-list conversion retains `ModelByteRange` and `ModelUtf8` errors.
Both synchronous programs and programs with database effects can use
the adapter. Checked schema metadata, quantities, effects, placeholders
and the full instantiated foreign row are enforced before emission.

Top-level aliases and local helpers that capture and return text are
supported; the response can be constructed after a helper returns.
The existing native foreign-value restrictions still apply: copying a
shared response into an owned return value and storing responses in
generated aggregates or closure layouts are rejected before Rust
compilation. The interpreter can share such values, so interpreter
success alone does not establish native support. The recursive
byte-list representation also retains its existing large-value stack
limit.

## Scripted requests

`run --request URI` accepts `Cx -> Uri -> Response` alongside the
existing `Cx -> Uri -> SeeOther`. With `--form BODY`, either result may
follow the checked byte-list body parameter. The text response is
serialized as HTTP/1.1 with a content length measured in UTF-8 bytes.
Redirect behavior is unchanged. Argument, type, body or step-limit
errors produce no response output.

```sh
_build/default/bin/lanyard.exe run --request /hello test/fixtures/response.lan
_build/default/bin/lanyard.exe run --request /todos --form 'title=caf%C3%A9' test/fixtures/response-form.lan
zsh dev/gates.sh --stage M1-response
```

The form fixture trims the title, creates a Todo in the private request
database and returns the stored title. The native adapter constructs a
Topcoat response value; the scripted interpreter supplies HTTP wire
framing. The [HTML adapters](STAGE-M1-HTML.md) add text-node escaping
and HTML bodies. Routing, listeners, streaming bodies, custom statuses
and native request entry points remain future work.

## Validation

The default Dune test alias retains the form suite and includes the
response suite. The grouped kernel tests now declare their fixture
directories and run from the workspace root, so `zsh dev/dunecho.sh test`
can locate their inputs.

The stage gate retains the cumulative form gate and adds 32 unit checks,
six CLI test groups and four mutations with clean and restored controls.
The native harness checks exact status, content type and body bytes,
including Unicode and control bytes, text captures and malformed input.
It runs the same 12 observations with both generated error variants.

Prepare it with `python3 -P test/lan_response_native.py --prepare NEW-DIR
--toasty TOASTY --topcoat TOPCOAT --lock LOCK`, build with Rust 1.98,
then run `--check` with the `lanyard-program` and `async_response`
binaries. Preparation checks the local library commits and cleanliness
and retains the original git-pinned manifest before using local paths.

The catalog now has 23 declarations and nine foreign types. Todo reports
28 foreign constants. Pins, anchor fingerprints, trust approval and the
M0 exit stamp are unchanged. Validation captures and tested source hashes
are in `validation/stage-m1-response/`.
