# M1 scripted request sessions

`lanyard run --requests SCRIPT FILE.lan` checks a handler once and runs each
scripted request against the same private database context. This makes it
possible to test a Todo lifecycle across requests with the existing form,
model, URI and response operations.

```sh
_build/default/bin/lanyard.exe run --requests test/fixtures/todo-session.requests test/fixtures/todo-session.lan
zsh dev/gates.sh --stage M1-session
```

Each script line is either `URI` or `URI<TAB>FORM`. `FORM` is a URL-encoded
body, so literal tabs and newlines within a value must be percent encoded.
A trailing tab supplies an explicitly empty body. A line without a tab
supplies no body. The former requires a `Cx -> Uri -> Bytes -> Response`
or `SeeOther` handler; the latter requires the existing two-argument form.
The byte-list family is checked by the interpreter.

LF and CRLF line endings are accepted, including an optional final newline.
Empty scripts, blank lines and extra tabs fail. Scripts have a limit of
1,048,576 bytes and 128 requests. The byte limit is a post-read check. The
CLI reads the script file in full, then refuses it. Every URI and form body
passes the existing validation, including their separate 8192-byte bounds.
Invalid options or script contents exit 64 before reading the program
source. Script syntax errors identify the line. Program checking and
execution failures exit 1; execution errors identify the request number.

The context starts empty once per invocation. The handler initializes its
schema explicitly; the example uses `/init`. Requests run in order and
share their model rows. Explicit `Db.connect` calls keep their existing
behavior and create separate connections. `--steps N` is one reduction
budget across the entire session, with the existing default and maximum.
The session stops at its first failure and prints nothing to stdout. On
success it prints the concatenated HTTP responses in order, using each
response's byte `Content-Length` for framing. The private store is discarded
when the invocation finishes, including after a failure.

`--requests` is mutually exclusive with `--request`, `--form` and
`--print-model`. The existing single-request mode still starts with a fresh
store on every invocation. This slice adds no listener, database service,
library dependency or target signature.

The Todo fixture initializes a schema, creates rows out of order, lists
them by ID, updates a title and completion flag, and deletes both an existing
and a missing ID. Its pages escape titles as HTML text and preserve UTF-8.
The CLI tests also cover blank titles, URI matching, isolated sessions,
empty forms, redirects, late failures and option conflicts.

The cumulative gate retains M1 URI text and adds the session checks. Four
mutations reset the store, reset the step budget, reverse the responses or
remove URI validation. Each must fail a named behavioral check, and clean
and restored controls must pass. Captures and final input hashes are recorded
under `validation/stage-m1-session/`. Trust proposals and the M0 exit stamp
remain pending; the source inventory measures the added driver and
interpreter code against the existing proposal.
