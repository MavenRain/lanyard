# M1 scripted requests

`lanyard run --request URI FILE.lan` checks and lowers one handler, supplies
a private database context and the URI, and prints its redirect response.
This adds the scripted request portion of M0-PLAN section 8 to the existing
interpreter. It uses the pinned `Cx`, `Uri`, `SeeOther`, `topcoat.db` and
`topcoat.see_other` signatures.

```sh
zsh dev/dunecho.sh build
_build/default/bin/lanyard.exe run --request /next test/fixtures/request.lan
```

The response uses CRLF line endings, a blank line after the headers, and
an empty body:

```text
HTTP/1.1 303 See Other
Location: /next
Content-Length: 0

```

The entry point must have the checked runtime signature
`Cx -> Uri -> SeeOther`. Type aliases and native closures work through the
existing lowering pipeline. The quantity checker still checks the source
before interpretation. `topcoat.db` returns a shared handle to the
context's database. All reachable supported models are registered in that
database, and the handler must call `Db.push_schema` before creating or
reading rows. Repeated context lookups share rows. Each invocation starts
empty, including repeated calls to the interpreter API in one process.
Explicit `Db.connect` calls allocate separate databases as before.

The accepted URI is an ASCII origin-form path beginning with one slash.
After that slash, `?` is an ordinary path byte from the accepted set. The
interpreter never splits the URI at `?` and never counts the occurrences,
so `/a?x=1?y=2` is accepted. Percent escapes must contain two hexadecimal
digits. The interpreter preserves every byte it accepts. The URI limit
is 8192 bytes. Absolute URLs, leading double slashes, fragments, spaces,
control characters, backslashes and raw non-ASCII characters are refused.
Encode non-ASCII text as UTF-8 percent escapes. These restrictions also
apply when constructing and rendering a redirect inside the runtime.

`--request` and `--steps` may occur in either order before the final source
path, once each. `--request` and `--print-model` are mutually exclusive.
Invalid arguments, including malformed URIs, return usage exit 64 before
source I/O. Checking, lowering and execution failures return exit 1 and
print no response. Success returns exit 0. The reduction and nesting bounds
of the existing interpreter apply to the complete handler invocation.

This slice handles a single URI and redirect. It does not parse raw HTTP,
select routes, decode forms, produce HTML bodies or open a listener.
Database effects stay in memory. The pinned target signatures and emitted
Rust are unchanged. Plain `run` still invokes a nullary `main`.

The later [form slice](STAGE-M1-FORM.md) adds `--form BODY` and explicit
URL-encoded field decoding through `Form.field`.

Validation is reproducible with:

```sh
zsh dev/gates.sh --stage M1-request
```

The gate retains the cumulative M1 run gate and adds 23 interpreter checks,
18 CLI tests and four mutation controls. The controls change the redirect
status, allow header control characters, corrupt the context handle and
remove the foreign-metadata check. Each control must compile and fail its
named assertion. Clean controls must pass first. Frozen captures and source
hashes live under `dev/validation/stage-m1-request/`.

The complete source inventory measures the added `rust/run_http.ml` and
the changes to the existing interpreter and driver. The trust policy stays
proposed, its roster and budgets stay unchanged, and M0 remains pending.
