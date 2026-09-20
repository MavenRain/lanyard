# M1 loopback HTTP listeners

`emit --crate DIR --listen 127.0.0.1:PORT FILE.lan` emits a standalone
HTTP server for a checked request handler. `build --out DIR --listen
127.0.0.1:PORT FILE.lan` also invokes Cargo; `--offline` and `--release`
retain their build meanings. Run the resulting executable to start it.

```sh
_build/default/bin/lanyard.exe build --out /tmp/todo-http --listen 127.0.0.1:3000 test/fixtures/todo-session.lan
/tmp/todo-http/target/debug/lanyard-program
```

The example initializes its schema on `/init`. With the server running:

```sh
curl http://127.0.0.1:3000/init
curl -d 'id=1&title=write+tests' http://127.0.0.1:3000/todos/create
curl http://127.0.0.1:3000/todos
```

Only the numeric IPv4 loopback address is accepted. Ports use one through
five decimal digits and range from 0 through 65535; zero asks the OS for an available port.
After binding, stderr reports `LANYARD-LISTEN http://127.0.0.1:PORT`.
The address is embedded at emission time. Invalid addresses, repeated or
conflicting options, and an existing output destination exit 64. Address
validation precedes source I/O. A type or emission failure exits 1 and
publishes no crate. `--listen`, `--requests` and `--print-model` are
mutually exclusive, and `--steps` applies only to the interpreter.

Handlers have type `Cx -> Uri -> SeeOther`, `Cx -> Uri -> Response`, or
either response type with a third checked byte-list form argument. The
server registers GET and POST routes for the root and all nested paths.
Parsed URIs retain their path and query bytes and use the existing
8192-byte origin-form validator. The pinned HTTP parser removes fragments
before the adapter sees the URI: `/path#fragment` reaches the handler as
`/path`. Scripted request mode still rejects fragments in its raw input.
A two-argument handler accepts an empty body. A
three-argument handler receives an empty form for a bodyless request, or
a POST body with content type `application/x-www-form-urlencoded`.
Form parsing retains the 8192-byte and 128-field limits, UTF-8 checks,
percent-escape checks and duplicate-name rejection, including when the
handler ignores its form argument.

Invalid parsed URIs or forms return 400, oversized or unreadable bodies return
413, a body read exceeding five seconds returns 408, and an unsupported
content type on a nonempty POST form returns 415. Handler errors return
500 without their details in the response. Topcoat also converts handler
panics to 500. Subsequent requests can still run. The server delegates
HTTP framing and graceful Ctrl+C or SIGTERM shutdown to pinned Topcoat.

By default all requests share one private in-memory SQLite database.
The [database option](STAGE-M1-DATABASE.md) selects a persistent SQLite
file with `--database PATH`. Handler calls
are serialized after input validation; this does not add transactions or
roll back a failed handler's writes. The handler initializes its schema
with `Db.push_schema`. An in-memory process starts empty. Startup database and
socket errors exit 1. Native recursion and errors retain the backend's
existing semantics. This slice serves local development over plain HTTP.

The cumulative gate preserves the native-session and interpreter gates,
checks CLI validation, and compiles five server programs and two mutation
controls offline. Real socket tests cover URI preservation, redirects,
Todo state and restart, forms, body limits and timeouts, concurrency,
handler error recovery and SIGTERM shutdown. The controls remove URI or
form validation and must exhibit the specific bad response rejected by
the unmodified runtime.

```sh
LANYARD_TOASTY=/path/to/toasty LANYARD_TOPCOAT=/path/to/topcoat zsh dev/gates.sh --stage M1-http
```

The gate respects `CARGO_HOME`, `CARGO_TARGET_DIR` and `RUSTUP_TOOLCHAIN`.
The server manifest enables Topcoat's `serve` feature and Tokio's network,
time and synchronization features. Existing batch manifests, target
signatures and dependency revisions retain their bytes. Trust budgets
and the M0 exit stamp remain pending.
