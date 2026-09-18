# M1 native request sessions

`emit --crate DIR --requests SCRIPT FILE.lan` embeds a validated request
script in a standalone Rust crate. `build --out DIR --requests SCRIPT
FILE.lan` emits the same crate and invokes Cargo. The existing `--offline`
and `--release` build options apply.

```sh
_build/default/bin/lanyard.exe emit --crate /tmp/native-todo --requests test/fixtures/todo-session.requests test/fixtures/todo-session.lan
cargo run --manifest-path /tmp/native-todo/Cargo.toml
```

The script format, URI and form validation, byte limit and request limit
are the same as for `run --requests`. A malformed script exits 64 before
reading the program. Checking, handler-layout and emission failures exit
1 before creating the output directory. `--requests` and `--print-model`
are mutually exclusive. Repeated options fail. The existing crate writer
requires a fresh destination and publishes it only after emission succeeds.

The emitted executable opens one SQLite database in memory, registers the
reachable models and passes its context to every request in order. The
handler initializes its schema with `Db.push_schema`. Explicit connections
inside a handler retain their separate databases. Each process starts with
an empty store. Both two-argument handlers and handlers with a checked byte
list form argument work, including handlers that ignore their form body.

Responses have the interpreter's deterministic HTTP transcript format:
200 text or HTML responses include UTF-8 byte lengths, and 303 redirects
include their location and a zero content length. All requests finish
before stdout is written. A handler or response failure exits 1 and
identifies its request number. A database or output failure exits 1
and names no request. Requests execute as sequential Tokio tasks, so
Rust checks that their futures are `Send`. A task panic also produces
an indexed failure; the Rust panic hook may print its diagnostic to
stderr. The pinned SQLite driver currently panics on a missing schema.

Native execution retains the existing Rust backend's recursion and error
semantics. It has no interpreter reduction budget, and these commands do
not accept `--steps`. Source and scripts are embedded at emission time;
the executable does not read them again. No HTTP listener is added.

The cumulative gate retains the interpreted session checks, runs five CLI
test groups, builds eight native programs offline against clean local
checkouts of the target pins, and executes each program twice. It checks
the Todo lifecycle, request ordering, URI preservation, UTF-8 and control
bytes, ignored and empty forms, 128 requests, late failures and a missing
schema. Independent expected transcripts also have to match the
interpreter. Repeated executions check fresh process state.
Two runtime mutants reverse the responses or publish a partial transcript;
the checks require the specific incorrect transcript from each control.

```sh
LANYARD_TOASTY=/path/to/toasty LANYARD_TOPCOAT=/path/to/topcoat zsh dev/gates.sh --stage M1-native-session
```

The dependency checkouts default to siblings of this repository. The gate
uses the preceding native slice's lockfile and respects `CARGO_HOME`,
`CARGO_TARGET_DIR` and `RUSTUP_TOOLCHAIN`. Its generated suite is temporary;
the Cargo target directory is retained for reuse. Validation captures and
source hashes are recorded under `validation/stage-m1-native-session/`.
Target signatures and dependency pins retain their existing bytes. Trust
budgets and the M0 exit stamp remain pending.
