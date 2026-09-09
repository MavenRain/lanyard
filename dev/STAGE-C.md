# Lanyard M0 Stage C

Stage C implements the census and elaboration slice of M0-PLAN section 10.
Run `zsh dev/gates.sh --stage C` from the repository. This includes the
Stage B battery, target type checks and adversarial cases, the carried
kernel and surface suites, the Todo fixture, driver checks and HOUSE.

The `.lan` entry point installs the generated target catalog before checking
source declarations. Every foreign declaration passes the ordinary kernel
postulate checker. Type rows are installed before value rows, allowing
cross-library references independently of file order. R0-TARGET inspects
the checked telescope's result, compares it with the row kind and enforces
the nine-name atom inventory. `spec-count` derives its ninth line from that
checked inventory. The preceding eight census lines retain their bytes.

The lexer, parser, surface syntax tree and kernel are carried unchanged.
Lanyard's elaborator reads the two additional declaration forms and sends
ordinary syntax to the same checker. `.kan` still uses the original entry
point. In `.lan`, `model` and `signature` are reserved declaration words.
Qualified names such as `Todo.create` and `toasty::Error` map to flat kernel
names `Todo_create` and `toasty_Error`. Numeric projections keep their
meaning. Declarations that collide after this mapping are rejected.

## Models

```text
model Todo with
| id : Nat
| title : Bytes
| completed : Bool
end
```

A model is a checked `prod` over its field types in declaration order.
It adds no opaque model or key type. Each `Model.*` schema is instantiated
using the model and its `id` field type. The kernel infers the specialized
application type before a new foreign postulate is added. Instance metadata
retains the original schema, print rule, effect row and type arguments for
the next lowering stage. A model requires an `id` field because the current
catalog includes `Model.get_by_id`. Repeated fields and generated-name
collisions are errors.

The example declares Bytes as the carried strictly positive byte-list
family and Bool as a sum of units. Byte literals use the existing parser's
`bytesNil` and `bytesCons` encoding. These are checked source definitions,
not additional foreign atoms. `Todo.create` and `Todo.get_by_id` appear in
the axiom disclosure; the model product does not.

## Signatures

```text
signature Cli : Todo with
| DbExec (db : Db) (row : Todo) : Todo
end
```

Each declaration creates one monomorphic family with a `Cli.pure`
constructor for the declared result and one constructor per operation.
An operation constructor holds its argument telescope and a continuation
from its response to this family. For example, `Cli.DbExec` accepts a Db,
a Todo and a `Todo -> Cli` continuation. Positivity and constructor typing
run through the existing family checker.

Result and response types are checked and normalized before the first-order
test. The test traverses products, sums, foreign type arguments and fields
of closed inductive families. It rejects exponents hidden by aliases or
inside recursive data, and names the offending operation. Parameterized
or indexed inductive responses, unknown opaque responses, and responses
dependent on operation arguments remain unsupported in this M0 slice.
Ordinary target values, Nat, Bytes, Bool and model products are supported.

This stage checks family formation and program construction. Fused handler
lowering and Rust printing belong to the following stages. It makes no
claim that a recursive handler over a continuation passes Order's guard;
the carried guard and its 510-line source remain unchanged. Foreign effect
rows remain explicit metadata for lowering, and are not kernel type formers.

## Validation and remaining milestones

The target suite includes a tenth atom, a mislabelled universe result,
parenthesized and parameterized universe results, and declaration collisions.
The CLI suite changes the ninth SPEC count to ten in a scratch tree and
requires R0-COUNT to fail. It also checks silent success, named refusal with
exit 1, checked-form output, axiom disclosure and the carried `.kan` path.

KERNEL-CARRY checks all thirteen existing rows. The twelve-file kernel
bucket remains 3997 lines; generated target source remains 104 lines.
The numeric A_sig allowance remains a pending user ruling. Stage C does
not amend that ruling or claim M0-EXIT. Stage D owns the Rust IR and erasure,
Stage E owns printing, and Stage F owns the completed driver and M0 gate.
