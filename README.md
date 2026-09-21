# Lanyard

Lanyard is a language under construction that retains Kanon's kernel and
will emit Rust using Toasty and Topcoat. Its source extension is `.lan`.

Stage A is committed at `52eb5a7`. Stage B adds pinned target signatures,
a generated OCaml metadata library, and source drift checks. Stage C checks
those signatures, elaborates models and operation families, and derives the
foreign-type census. Stage D adds Rust IR, quantity-aware erasure and checked
foreign-call metadata. The Stage E native command prints Rust for pure
programs, including typed closures, captures and recursive data. The target
command adds synchronous foreign constants, concrete and applied foreign
types, async database calls, and model create/lookup for Nat, Bool and text
fields. Direct Db.connect calls and aliases select model schemas and check
URL text. The crate command writes a standalone program with pinned
dependencies and a synchronous or async entry point.
Crate emission specializes finite checked handlers into direct operation
bodies. The M0 Todo corpus emits a complete crate that creates and prints
a row. Stage F adds classified axiom reports, the AXIOM-RATIO inputs,
and informational compiler timings with a Go denominator refit. The
combined M0 gate records all seven legs and unresolved trust decisions,
with a complete OCaml source inventory and per-file hashes.
The M0-E2E gate builds the pinned Todo crate offline and checks its output.
Other model field types, general recursive handlers and the M0 exit stamp
remain ahead. The [trusted-code policy](dev/STAGE-F-POLICY.md) proposes
per-group source budgets. The inventory reports source growth against
that pending proposal. It stays proposed until the user rules; approved
policies enforce each group's budget and source roster. A_sig is
proposed at 104 lines. See [target documentation](target/README.md), the
[Stage B build log](dev/M0-BUILD-LOG.md#lanyard-m0-stage-b-2026-09-09) and
the [Stage C build log](dev/spikes/M0-BUILD-LOG.md#stage-c-2026-09-09) with
its [Stage C mutation log](dev/spikes/MUTATION-LOG.md#stage-c-2026-09-09).
The two stages record their work in separate log families.

The [M1 build command](dev/STAGE-M1-BUILD.md) checks a program, writes its
crate into a fresh directory and invokes Cargo there:

```sh
_build/default/bin/lanyard.exe build --out /tmp/todo-build --print-model Todo corpus/m0/todo.lan
```

Add `--release` for an optimized build or `--offline` to use cached
dependencies. Cargo output and normal exit codes pass through; a separate
`LANYARD-BUILD REPORTED` row reports Cargo wall time. The command compiles
the program without running it. Its driver growth is measured against
the existing proposed budget; no trust allowance or M0 exit is approved.

The [M1 interpreter](dev/STAGE-M1-RUN.md) runs the checked program with a
private in-memory model store:

```sh
_build/default/bin/lanyard.exe run --print-model Todo corpus/m0/todo.lan
# Todo { id: 1, title: "hi", completed: false }
zsh dev/gates.sh --stage M1-run
```

It supports native functions, closures, recursive data, finite checked
handlers and model create/lookup. Connections accept `sqlite::memory:`.
Each connection starts empty, and the program initializes its schema with
`Db.push_schema`. `--steps N` sets the interpreter's reduction limit.
This command runs without Cargo, a database service or an HTTP listener.

The [M1 scripted request harness](dev/STAGE-M1-REQUEST.md) supplies a
private database context and URI to a checked `Cx -> Uri -> SeeOther`
handler and prints its HTTP redirect:

```sh
_build/default/bin/lanyard.exe run --request /next test/fixtures/request.lan
zsh dev/gates.sh --stage M1-request
```

Request URIs use an origin-form path with valid percent escapes. After the
leading slash, `?` is an ordinary path byte from the accepted set. The
interpreter never splits the URI at `?` and never counts the occurrences. Each invocation starts with an empty database, and the handler
initializes its schema with `Db.push_schema`. Request mode supports
`--steps` and is mutually exclusive with `--print-model`.

The [M1 model deletion slice](dev/STAGE-M1-DELETE.md) adds
`Model.delete_by_id`, exposed as `Counter.delete_by_id key db` for each
declared model. It returns unit, accepts a missing key, and preserves other
rows, models and connections. The interpreter and emitted Rust share the
checked key range and asynchronous database metadata.

```sh
_build/default/bin/lanyard.exe run --print-model Counter test/fixtures/delete.lan
# Counter { id: 7, value: 23 }
zsh dev/gates.sh --stage M1-delete
```

The [M1 model update slice](dev/STAGE-M1-UPDATE.md) adds
`Model.update`, exposed as `Counter.update fields db` for each declared
model. It replaces the existing row with the supplied `id` and returns the
updated model. Missing rows fail. Nat, Bool and checked byte-list fields
work in the interpreter and emitted Rust.

```sh
_build/default/bin/lanyard.exe run --print-model Task test/fixtures/update.lan
# Task { title: "updated", id: 7, completed: true, value: 23 }
zsh dev/gates.sh --stage M1-update
```

The [M1 model listing slice](dev/STAGE-M1-ALL.md) adds `Model.all`, exposed
as `Counter.all db : Counter.rows` for each declared model. Lists contain
every row in ascending primary-key order and can be matched with the
generated `Counter.nil` and `Counter.cons head tail` constructors.

```sh
_build/default/bin/lanyard.exe run --print-model Task test/fixtures/all.lan
# Task { title: "updated", id: 3, completed: true, value: 122 }
zsh dev/gates.sh --stage M1-all
```

The [M1 text operations](dev/STAGE-M1-TEXT.md) add `Text.trim Bytes value`
and `Text.is_empty Bytes value` for a checked byte-list family. Trimming
removes Unicode whitespace at both ends. Empty checks return the usual
two-unit Boolean sum. Both operations reject malformed UTF-8 and bytes
outside `0..255` in the interpreter and emitted Rust.

```sh
_build/default/bin/lanyard.exe run --print-model Title test/fixtures/text-ops.lan
# Title { id: 1, text: "write tests", blank: true }
zsh dev/gates.sh --stage M1-text
```

The [M1 URI conversion](dev/STAGE-M1-URI.md) adds `Uri.from_text Bytes value`
for checked byte lists. Request handlers can construct an origin-form URI
and redirect to it. Invalid UTF-8, malformed escapes, absolute URLs and
paths longer than 8192 bytes fail in the interpreter and emitted Rust.

```sh
_build/default/bin/lanyard.exe run --request /todos test/fixtures/uri.lan
# HTTP/1.1 303 See Other, with Location: /
zsh dev/gates.sh --stage M1-uri
```

The [M1 form adapter](dev/STAGE-M1-FORM.md) adds
`Form.field Bytes body name` for explicit URL-encoded text fields.
`run --request URI --form BODY` supplies the encoded body to a checked
`Cx -> Uri -> Bytes -> SeeOther` handler. Bodies are limited to 8 KiB
and 128 fields; malformed encoding, duplicate names and missing fields
fail.

```sh
_build/default/bin/lanyard.exe run --request /todos --form 'title=write+tests' test/fixtures/form-request.lan
zsh dev/gates.sh --stage M1-form
```

The [M1 optional form adapter](dev/STAGE-M1-FORM-HAS.md) adds
`Form.has Bytes body name`, returning whether a decoded field is present.
It accepts missing fields and empty bodies, so handlers can use optional
checkboxes and query parameters. Empty values count as present; malformed
forms still fail validation.

```sh
_build/default/bin/lanyard.exe run --request /todos --form 'completed=' test/fixtures/form-has.lan
zsh dev/gates.sh --stage M1-form-has
```

The [M1 text response adapter](dev/STAGE-M1-RESPONSE.md) adds
`Response.text Bytes body`. Scripted handlers may return `Response` with
status 200 and a UTF-8 plain-text body. The form example stores a Todo
and returns its title:

```sh
_build/default/bin/lanyard.exe run --request /todos --form 'title=write+tests' test/fixtures/response-form.lan
zsh dev/gates.sh --stage M1-response
```

The [M1 HTML adapters](dev/STAGE-M1-HTML.md) add escaped text fragments
and HTML responses. Use `Html.text Bytes value` for text-node content,
then `Response.html Bytes body` to return a UTF-8 HTML body:

```sh
_build/default/bin/lanyard.exe run --request /todos --form 'title=%3Chello%3E' test/fixtures/html-form.lan
zsh dev/gates.sh --stage M1-html
```

The form example stores the title and returns `&lt;hello&gt;`. HTML
responses preserve markup supplied by the program. Text-node escaping
does not make values safe for attributes, scripts, styles or URLs.

The [M1 text concatenation adapter](dev/STAGE-M1-CONCAT.md) joins two
checked UTF-8 byte lists with `Text.concat Bytes left right`. Combine
literal markup with escaped text to build a complete response body:

```sh
_build/default/bin/lanyard.exe run --request /todos --form 'title=%3Chello%3E' test/fixtures/concat-form.lan
zsh dev/gates.sh --stage M1-concat
```

The form example stores the title and returns `<h1>&lt;hello&gt;</h1>`.
Concatenation preserves its inputs, so dynamic text still needs `Html.text`
before it is placed in a text node.

The [M1 natural-number text adapter](dev/STAGE-M1-NAT-TEXT.md) renders
IDs with `Text.from_nat Bytes value`. It supports arbitrary-size naturals
and emits decimal digits without leading zeros. The Todo list example
combines sorted database rows, links containing their IDs, and escaped titles:

```sh
_build/default/bin/lanyard.exe run --request /todos test/fixtures/todo-list.lan
zsh dev/gates.sh --stage M1-nat-text
```

The [M1 decimal text parser](dev/STAGE-M1-TEXT-NAT.md) converts nonempty
ASCII decimal text with `Text.to_nat Bytes value`. Leading zeros are
accepted and values beyond `u64` remain exact. Signs, whitespace and
other malformed input fail. Forms can supply IDs for model operations:

```sh
_build/default/bin/lanyard.exe run --request /todos --form 'id=000257&title=%3Chello%3E' test/fixtures/todo-form-id.lan
zsh dev/gates.sh --stage M1-text-nat
```

The [M1 text comparison](dev/STAGE-M1-TEXT-EQUAL.md) checks exact equality
with `Text.equal Bytes left right`. Both inputs must be valid UTF-8 byte
lists. The result is a Boolean, so form values can select a response:

```sh
_build/default/bin/lanyard.exe run --request / --form 'action=save' test/fixtures/text-equal.lan
zsh dev/gates.sh --stage M1-text-equal
```

The [M1 text length adapter](dev/STAGE-M1-TEXT-LENGTH.md) counts UTF-8 bytes
with `Text.length Bytes value`. It returns a natural number: empty text has
length zero, `b"é"` has length 2, and `b"😀"` has length 4. It validates the
complete byte list even when the result is unused.

```sh
_build/default/bin/lanyard.exe run --request /length --form 'text=%C3%A9' test/fixtures/text-length.lan
zsh dev/gates.sh --stage M1-text-length
```

The [M1 substring adapter](dev/STAGE-M1-TEXT-CONTAINS.md) checks whether
`Text.contains Bytes text needle` finds an exact, case-sensitive substring.
An empty needle matches every valid text. Both inputs are validated as
UTF-8 before searching, including when the result is unused.

```sh
_build/default/bin/lanyard.exe run --request /search --form 'action=autosave' test/fixtures/text-contains.lan
zsh dev/gates.sh --stage M1-text-contains
```

The [M1 prefix and suffix adapters](dev/STAGE-M1-TEXT-BOUNDARIES.md) add
`Text.starts_with Bytes text needle` and `Text.ends_with Bytes text needle`.
They match exact boundaries, validate both complete byte lists as UTF-8,
and accept empty needles. The fixture classifies a path using both adapters:

```sh
_build/default/bin/lanyard.exe run --request '/static/main.css?v=1' test/fixtures/text-boundaries.lan
zsh dev/gates.sh --stage M1-text-boundaries
```

The [M1 replacement adapter](dev/STAGE-M1-TEXT-REPLACE.md) adds
`Text.replace Bytes text needle replacement` for all non-overlapping,
case-sensitive matches. An empty needle inserts at Unicode scalar boundaries.
All three complete inputs are validated as UTF-8, including unused results.

```sh
_build/default/bin/lanyard.exe run --request / --form 'text=banana&needle=na&replacement=!' test/fixtures/text-replace.lan
zsh dev/gates.sh --stage M1-text-replace
```

The [M1 URI text adapter](dev/STAGE-M1-URI-TEXT.md) exposes the full checked
request URI as a byte list with `Uri.to_text Bytes uri`. Handlers can use
`Text.equal` to choose a response from the URI:

```sh
_build/default/bin/lanyard.exe run --request /todos test/fixtures/uri-text.lan
zsh dev/gates.sh --stage M1-uri-text
```

The example returns `todos` for `/todos` and echoes other paths with an
`unmatched: ` prefix. Conversion preserves percent escapes and the full
text after `?`; it does not decode or split the URI.

The [M1 URI component adapters](dev/STAGE-M1-URI-PARTS.md) separate routing
from query data. `Uri.path Bytes uri` returns the path and `Uri.query Bytes uri`
returns the raw query without its leading `?`, or an empty byte list when
absent. Both preserve escapes and validate the complete URI. Pass the query
to `Form.field` when URL-encoded field decoding is needed:

```sh
_build/default/bin/lanyard.exe run --request '/hello?name=Ada+Lovelace' test/fixtures/uri-parts.lan
zsh dev/gates.sh --stage M1-uri-parts
```

The example responds with `hello Ada Lovelace`. It also works with `serve`.

The [M1 request sessions](dev/STAGE-M1-SESSION.md) run a sequence of requests
against one private database. Each script line contains a URI, optionally
followed by a tab and an encoded form body. The Todo example creates,
lists, updates and deletes rows across requests:

```sh
_build/default/bin/lanyard.exe run --requests test/fixtures/todo-session.requests test/fixtures/todo-session.lan
zsh dev/gates.sh --stage M1-session
```

Responses are concatenated in request order with their HTTP content lengths.
A failed session prints no transcript. Each invocation starts empty, and
`--steps` supplies one budget for the whole sequence.

The [M1 native sessions](dev/STAGE-M1-NATIVE-SESSION.md) embed the same
handler and script in a standalone Rust executable:

```sh
_build/default/bin/lanyard.exe build --out /tmp/native-todo --requests test/fixtures/todo-session.requests test/fixtures/todo-session.lan
/tmp/native-todo/target/debug/lanyard-program
```

The executable shares one private SQLite store across requests and prints
the complete HTTP transcript on success. Native execution uses the Rust
backend's error semantics and does not accept `--steps`.

The [M1 HTTP listener](dev/STAGE-M1-HTTP.md) serves checked request handlers
on loopback with one shared SQLite store:

```sh
_build/default/bin/lanyard.exe build --out /tmp/todo-http --listen 127.0.0.1:3000 test/fixtures/todo-session.lan
/tmp/todo-http/target/debug/lanyard-program
```

Initialize this example with `GET /init`, submit URL-encoded forms with
`POST /todos/create`, and read the current list with `GET /todos`.
Port zero selects an available port, reported on stderr. Each process
starts empty, and Ctrl+C shuts the server down gracefully.

The [M1 serve command](dev/STAGE-M1-SERVE.md) compiles and starts that
checked HTTP handler in one command:

```sh
_build/default/bin/lanyard.exe serve --out /tmp/todo-serve --listen 127.0.0.1:3000 test/fixtures/todo-session.lan
```

The output directory must be fresh. Add `--offline` to use cached
dependencies or `--release` for an optimized server.

The [M1 database option](dev/STAGE-M1-DATABASE.md) keeps HTTP state across
restarts with `--database ./todo.sqlite3`. It works with `emit --crate`,
`build`, and `serve` when `--listen` is present. Relative paths use the
invocation directory. Initialize the Todo schema once with `/init`, then
reuse that database on subsequent starts. Without this option, each server
continues to start with an empty in-memory database.

Build and validate through Stage D:

```sh
zsh dev/gates.sh --stage D
_build/default/bin/lanyard.exe check --erased examples/m0-todo.lan
```

Validate and use the native Rust printer:

```sh
zsh dev/gates.sh --stage E-native
_build/default/bin/lanyard.exe emit --native test/fixtures/native.lan
```

The [native printer slice](dev/STAGE-E-NATIVE.md) supports arithmetic,
products, sums, native calls, [typed closures](dev/STAGE-E-CLOSURES.md), and
[recursive families](dev/STAGE-E-RECURSIVE.md).
It reports unsupported foreign and polymorphic field layouts explicitly.
The complete M0 Todo crate golden is under `corpus/m0/golden/`.

Validate and use the [synchronous foreign printer](dev/STAGE-E-FOREIGN.md):

```sh
zsh dev/gates.sh --stage E-foreign
_build/default/bin/lanyard.exe emit --target test/fixtures/foreign.lan
```

This prints a Rust source module using the pinned target paths, including
`topcoat.db` and `topcoat.see_other`.

Validate and use the [async database printer](dev/STAGE-E-ASYNC.md):

```sh
zsh dev/gates.sh --stage E-async
_build/default/bin/lanyard.exe emit --target test/fixtures/async.lan
```

`Db.push_schema` prints an awaited call. Its callers become async functions
and propagate database errors. Async closures and recursive async calls
remain explicit refusals. Model schemas are described below.

Validate [applied foreign types](dev/STAGE-E-FOREIGN-TYPES.md):

```sh
zsh dev/gates.sh --stage E-foreign-types
_build/default/bin/lanyard.exe emit --target test/fixtures/foreign-types.lan
```

`Form T` and `Deferred T` retain their checked type arguments, including
nested wrappers and native data layouts. A One binder moves its wrapper;
a Many binder shares it through `Arc`.

Validate [scalar model schemas](dev/STAGE-E-MODELS.md):

```sh
zsh dev/gates.sh --stage E-models
_build/default/bin/lanyard.exe emit --target test/fixtures/models.lan
```

`Counter.create` and `Counter.get_by_id` print awaited Toasty operations.
The `id` field is the supplied primary key. Database fields use checked
integer conversions; overflow and negative stored values return an error.
Two-unit sums, including aliases, use Boolean columns with tag 0 as false
and tag 1 as true. Keys remain Nat.
Checked byte lists, including the Todo title type, use String columns.
Writes reject elements above 255 and invalid UTF-8 before the database call.

Validate [database connections](dev/STAGE-E-CONNECTIONS.md):

```sh
zsh dev/gates.sh --stage E-connections
_build/default/bin/lanyard.exe emit --target test/fixtures/connections.lan
```

A checked alias such as `def open : Bytes -> Db := Db.connect Todo Bytes`
prints an async connection function. A product of declared model types
selects several schemas. Callers can connect, push the schema and create
rows in one generated program. URL conversion rejects invalid bytes and
UTF-8 before opening a connection.

Direct calls such as `Db.connect Todo Bytes url` work inside functions,
let bodies and case branches. Several calls in one body can select different
models and URLs. Model and text type arguments must be closed; generic
connection functions and stored connection function values still refuse.

Emit a [standalone target crate](dev/STAGE-E-CRATE.md):

```sh
zsh dev/gates.sh --stage E-crate
_build/default/bin/lanyard.exe emit --crate /tmp/lanyard-todo test/fixtures/crate.lan
cargo run --manifest-path /tmp/lanyard-todo/Cargo.toml
```

The output directory must be new and its parent must exist. The generated
entry point runs a zero-argument `main`, discards its returned value and
propagates errors through Rust's `Result`. This fixture connects to SQLite
in memory, creates a Todo and looks it up. Emission does not run Cargo.

Crates now keep the [dependencies of main](dev/STAGE-E-REACHABLE.md).
Unused functions and model schemas are omitted before lowering. The full
source still typechecks; references in types and untaken branches are
retained. Module emission continues to print every definition.

```sh
zsh dev/gates.sh --stage E-reachable
```

Crates also specialize [finite checked handlers](dev/STAGE-E-HANDLERS.md).
Known signature constructors and their continuations reduce to direct
code. Database operations keep their order and execute once, including
calls whose results are unused. Remaining runtime signature programs
refuse before output is created.

```sh
zsh dev/gates.sh --stage E-handlers
_build/default/bin/lanyard.exe emit --crate /tmp/lanyard-handlers test/fixtures/handlers-db.lan
```

Emit and validate the [M0 Todo crate](dev/STAGE-E-TODO.md):

```sh
zsh dev/gates.sh --stage E-todo
_build/default/bin/lanyard.exe emit --crate /tmp/lanyard-m0 --print-model Todo corpus/m0/todo.lan
```

The generated program creates one row and prints
`Todo { id: 1, title: "hi", completed: false }`.
The optional model formatter checks scalar conversions and propagates
output errors. EMIT-DIFF compares the whole crate without normalization.

Inspect the [classified axioms](dev/STAGE-F-AXIOMS.md):

```sh
zsh dev/gates.sh --stage F-axioms
_build/default/bin/lanyard.exe axioms corpus/m0/todo.lan
_build/default/bin/lanyard.exe axioms --names examples/m0-todo.lan
```

The report lists Framework, Foreign, Classical and Div, sorted by class
and name, with class totals and the compiled target catalog's SHA-256.
Todo reports 43 foreign constants and 3 definitions of the checked
module (Bool, Todo and main). These are informational inputs, with no
ratio bound. The scope is the whole checked module, including unused
catalog rows and model operations.
Source postulates without an M0 class produce a diagnostic; `--names`
prints their declaration names. The carried `.kan` output stays unchanged.

Measure the [M0 compiler timings](dev/STAGE-F-TIME.md):

```sh
zsh dev/gates.sh --stage F-time
python3 -P dev/bench.py --refit-go --output /tmp/lanyard-time.json
```

The instrument reports check and target-module fits, Todo crate medians,
load averages and ratios at the same input size. It uses one warm-up and
five samples. The Go refit uses all thirteen frozen S4 packages; omitting
`--refit-go` labels the comparison as historical. High-load runs are
NOISY, and all M0 timings are informational.

Run the [combined M0 gate](dev/STAGE-F-GATES.md):

```sh
zsh dev/gates.sh M0
zsh dev/gates.sh --stage F-gates
```

The combined command saves per-check logs and a JSON report. It returns
exit 2 while the whole-base trust allowances and scope remain unruled;
an actual failure returns exit 1. The stage command validates the gate
implementation and retains that pending M0 result. The M0 exit stamp
remains the user's decision.

Inspect the [compiler source inventory](dev/STAGE-F-TRUST.md):

```sh
python3 -P dev/trusted-inventory.py --output /tmp/lanyard-trust.json
```

The saved JSON records 47 current OCaml sources, including handler
fusion, and leaves the open limits and scope decisions pending. M0
verifies the inventory against the current source bytes and retains it
beside the gate report.

Run the [M0 SQLite execution gate](dev/STAGE-F-E2E.md) with clean local
checkouts of the pinned libraries and the locked dependencies cached:

```sh
zsh dev/gates.sh M0-E2E --toasty /path/to/toasty --topcoat /path/to/topcoat
```

This rebuilds the compiler and emitted crate, runs the program, and
requires exactly `Todo { id: 1, title: "hi", completed: false }` plus a
newline. The retained report records build and runtime failures as well
as successful output. The seven-leg M0 verdict keeps its pending ruling.

See [Stage C](dev/STAGE-C.md) for the `.lan` declaration grammar and checked
Todo example, and [Stage D](dev/STAGE-D.md) for Rust erasure, its current
limits and the proposed IR allowance. The carried `.kan` checker is also available:

```sh
_build/default/bin/lanyard.exe check test/fixtures/b01-function-eta.kan
_build/default/bin/lanyard.exe axioms test/fixtures/b08-axiom-disclosure.kan
_build/default/bin/lanyard.exe spec-count
```

Use an existing file under `test/fixtures` for `check`. The driver also
supports `check --print FILE` and `check --erased FILE`. The fork removed
the Wasm backend and runtime commands.

The kernel and its foundation documents are inherited from Kanon at
`046689a`. [SPEC.md](SPEC.md) and the older build-log sections record that
history. [KERNEL-CARRIED.md](dev/KERNEL-CARRIED.md) records the fork's carry
contract. Lanyard's current plan is in the sibling `lanyard-m0` directory.

Licensed under MIT OR Apache-2.0.
