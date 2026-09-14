# M1 interpreted execution

`lanyard run` checks and lowers a `.lan` file, then evaluates its `main`
function over the Rust erasure IR. This implements the in-memory execution
part of M0-PLAN section 8. A source program can script database operations
and finite handlers in one run. HTTP request parsing and a server harness
remain future work.

```sh
zsh dev/dunecho.sh build
_build/default/bin/lanyard.exe run --print-model Todo corpus/m0/todo.lan
```

The result is:

```text
Todo { id: 1, title: "hi", completed: false }
```

`--print-model MODEL` and `--steps N` may appear in either order before the
final source path. Each option may appear once. The final path must have
a stem and the `.lan` suffix. A path beginning with a dash needs a `./`
prefix or an absolute path. Invalid options and missing input return 64.
Checking, lowering and runtime errors return 1 with a diagnostic on stderr.
Successful execution returns 0. Source I/O retains the existing driver's
guarded-read behavior, including loud failures after a filesystem race.

By default, the result is discarded. With `--print-model`, main must return
the selected reachable model layout. Output is assembled after successful
execution, so a failed run prints no partial result. Fields appear in source
order. Nat and Boolean fields print as decimal integers and `true` or
`false`. Quoted text uses OCaml byte escaping, including decimal escapes
for non-ASCII bytes.

Native interpretation covers the IR's literals, variables, lets, direct
calls, captured closures, products, tags, cases and clones. Function
arguments and captured values retain declaration order. Evaluation visits
arguments from left to right and only enters the selected case branch.
The five Nat primitives use arbitrary-precision arithmetic; subtraction
truncates at zero. The existing reachability, connection specialization
and finite-handler fusion passes run before evaluation. Runtime postulates
and unsupported lowerings retain their explicit refusals.

The model store supports the existing Nat, Boolean and UTF-8 byte-list
fields. Database integers must fit in nonnegative i64, bytes must fit in
0..255, and text must be valid UTF-8. The implemented foreign operations
are `Db.connect`, `Db.push_schema`, `Model.create` and `Model.get_by_id`.
Other foreign operations return an unsupported-operation error.

Every `Db.connect` accepts exactly `sqlite::memory:` and creates a fresh
store for its selected model schemas. Other URLs are refused before host
I/O. A schema must be initialized before create or lookup. Repeated schema
initialization preserves the rows. Keys are unique within each model and
connection. Duplicate inserts and missing lookups fail explicitly. Database
aliases share a handle, while separate connections and separate runs have
independent rows. No file, network connection, Cargo process or listener is
created by interpreted database operations.

The default reduction budget is 100000. `--steps` accepts decimal integers
from 1 through 1000000. Evaluating an IR term or invoking a function consumes
one step. Nesting also has a fixed limit of 512 units of evaluation depth.
Each subterm evaluation and each call consumes one unit, so one source-level
call consumes several units.
Both limits return errors on exhaustion. These limits apply to evaluation;
they do not bound source checking, individual arithmetic costs or value
sizes. General recursive handlers retain the existing fusion refusal.

The interpreter's three OCaml sources live under `rust/`, beside their
model metadata dependencies. The complete source inventory measures them
in its existing `unassigned` group. Their trust classification stays open,
and the proposed budget and source roster remain unchanged. Driver growth
also remains measured against the existing proposal. This stage records no
trust-policy approval or milestone exit.

Validation is reproducible with:

```sh
zsh dev/gates.sh --stage M1-run
```

The gate retains the cumulative M1 build gate, then runs 40 interpreter
checks, 26 CLI tests and five isolated mutation controls. The CLI suite also
checks 11 observations from existing native closure and recursive fixtures,
the four-row database handler, and the M0 Todo output. The controls alter
argument order, step accounting, foreign refusal, connection identity and
lookup key selection. A control must compile and fail its named behavioral
assertion. Captures and source hashes live under
`dev/validation/stage-m1-run/`.
