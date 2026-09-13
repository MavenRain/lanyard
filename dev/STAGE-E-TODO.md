# M0 Todo crate and model output

The M0 corpus now holds a complete program and its complete crate golden.
`corpus/m0/todo.lan` declares Todo with Nat, text and Bool fields. Its main
connects to SQLite in memory, pushes the schema and creates one row.
The crate entry point prints the returned row:

```sh
zsh dev/gates.sh --stage E-todo
_build/default/bin/lanyard.exe emit --crate /tmp/lanyard-m0 --print-model Todo corpus/m0/todo.lan
cargo run --manifest-path /tmp/lanyard-m0/Cargo.toml
```

```text
Todo { id: 1, title: "hi", completed: false }
```

`--print-model MODEL` is an explicit crate option. The named model must
be retained by main's dependencies, and main must return its runtime
layout with no runtime arguments. Type aliases are accepted. Lanyard
models are structural: the explicitly selected model supplies the field
names when two models have the same layout. Module emission and ordinary
crate emission keep their existing output bytes. An unknown name and a
declared but unreached name share one refusal.

The formatter uses source field names and declaration order. Nat fields
use the checked database integer conversion, Bool uses false for tag 0
and true for tag 1, and text uses the checked byte-list conversion and
Rust's quoted string formatting. All fields convert before stdout is
written. Invalid values return an error with no output. The main result
is evaluated once, and write errors, including a closed stdout pipe,
return through a separate entry-point error enum that wraps the program
error and the I/O error. This is a driver output policy, with no new
language primitive or target axiom.

An async printed entry point passes its future through a generic Send
bound before awaiting it. The M0 crate exercises that bound with the
pinned libraries. This check applies to the entry future, not to every
function in every generated module.

`python3 -P dev/emit-diff.py` is the EMIT-DIFF leg. It compares the complete
file set and every byte of `Cargo.toml` and `src/main.rs` against
`corpus/m0/golden/`. It performs no normalization. Its controls append a
newline, add an unexpected golden file, and delete the Model.create
print-rule row from a scratch signature catalog. The last control builds
a separate compiler and requires this same leg to refuse the Todo source.

The cumulative gate retains the earlier stages and adds ten compiled
output observations, nine CLI refusals and two Rust output mutations.
The focused synchronous observations use an empty model derive macro;
they test the generated formatter without executing database calls.
The separate pinned SQLite validation builds and runs the emitted source
unchanged. Its original Git manifest, locally resolved manifest, lockfile,
captures and source hashes are in `dev/validation/stage-e-todo/`.

To repeat the pinned validation with local checkouts:

```sh
mkdir -p .gatework
python3 -P dev/prepare-crate.py --toasty /path/to/toasty --topcoat /path/to/topcoat \
  --source corpus/m0/todo.lan --print-model Todo \
  --lock dev/validation/stage-e-todo/Cargo.lock --output .gatework/m0-pinned
cargo build --offline --locked --manifest-path .gatework/m0-pinned/Cargo.toml
.gatework/m0-pinned/target/debug/lanyard-program
```

The preparer verifies both pinned revisions and clean tracked sources.
Only dependency locations change in the manifest. The registry cache
must contain the locked dependencies. Use the installed compact build
commands and validation ledger in the development workspace.

The earlier `examples/m0-todo.lan` remains a Stage C/D checker fixture.
The new corpus supplies the executable M0 source and golden required by
D-M0-1 and D-M0-2. The classified axioms instrument, timing instrument,
combined M0 gate and M0 exit stamp remain ahead. Numeric trusted-line
allowances remain user rulings. The plan places build and run in M1.
