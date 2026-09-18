# M1 request URI text

`Uri.to_text Bytes uri` converts an origin-form request URI to a checked
byte-list family. It preserves the full spelling, including percent-escape
case, repeated slashes, dot segments and every `?` byte. It neither decodes
escapes nor separates a query. The output can be compared with `Text.equal`
or included in a response. Dynamic HTML text still needs `Html.text`.

```sh
_build/default/bin/lanyard.exe run --request /todos test/fixtures/uri-text.lan
zsh dev/gates.sh --stage M1-uri-text
```

The fixture returns `todos` for exactly `/todos`; `/todos?` and other paths
return their full spelling after `unmatched: `. The existing scripted
request boundary rejects malformed URIs with exit 64 before reading the
source file. Each scripted invocation retains its private database.

The schema is `(0 Text : Type 0) -> (uri : Uri) -> Text`. Its output type
argument must be a closed byte-list family and is erased. The URI argument
has shared quantity and is evaluated once. The operation is synchronous
and declares no library effect. Conversion uses the existing adapter error
channel if validation fails. Named aliases, captured URIs and alternate
byte-list families follow the existing specialization path.

Both runtimes recheck the origin-form contract and 8192-byte bound at the
adapter boundary, including when its result is unused. This also covers
native callers that supply a Topcoat URI outside Lanyard's accepted subset.
The interpreter preserves its URI string; generated Rust formats the pinned
Topcoat URI, validates that text and constructs the requested byte list.
No library dependency or foreign type is added.

The cumulative gate retains exact text comparison and adds 43 OCaml checks,
four CLI groups and three compiler mutations. The mutations remove
interpreter validation, replace the URI text with `/`, or remove emitted
validation. Clean and restored controls must pass.

The separate native harness uses the real pinned Topcoat URI type. Its 70
observations cover exact rendering, round trips, captures, alternate output
families and validation with used and unused results:

```sh
python3 -P test/lan_uri_text.py --prepare NEW-DIR --toasty TOASTY --topcoat TOPCOAT --lock LOCK
python3 -P test/lan_uri_text.py --check PATH-TO-LANYARD-PROGRAM
```

Build the prepared crate offline with the supplied lock before running
`--check`. The recorded preparation uses the preceding stage's lock at
`dev/validation/stage-m1-text-equal/native/Cargo.lock`.

Validation captures and source hashes are in `validation/stage-m1-uri-text/`.
The catalog has 30 proposed declarations and nine foreign types. Todo
reports 35 foreign constants. The generated catalog has 194 lines, 90 above
the proposed 104-line allowance. Trust approval and the M0 exit stamp remain
pending. The signature digest changes for the new row; pinned library
revisions and source anchors stay the same.
