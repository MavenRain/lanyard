# Finite checked handlers

Crate emission now specializes statically known signature applications
and eliminations before Rust lowering. Existing `.lan` syntax expresses
each handler as an ordinary, checked match. A finite chain of handlers
can consume a finite sequence of operations. The resulting code contains
the operation bodies and their continuations, with no runtime signature
data or handler dispatch.

```sh
zsh dev/gates.sh --stage E-handlers
_build/default/bin/lanyard.exe emit --crate /tmp/lanyard-handlers-pure test/fixtures/handlers.lan
```

The pure fixture adds through a handler and a captured continuation. The
database fixture creates two rows through two handler layers, then creates
a third row through an unused function argument and a fourth through the
first component of an unused dependent pair. It reads all three keys. The
first created row supplies the second key twice. Successful SQLite execution
checks that creation is not duplicated, schema initialization is retained,
and the unused argument still executes.

The complete source checks before selection or fusion, including unused
definitions and unselected handler branches. The elaborator records the
declared signature names. The specializer visits definitions mentioning
those families, unfolds nonrecursive definitions and reduces known
constructor matches. Native runtime branches remain branches; each branch
can contain its own known handler application. It does not unfold recursive
functions or invent a recursive handler rule.

Substitution applies only to values and erased arguments. Computations
become ordered bindings, including computations whose result is unused.
Constructor fields receive bindings before their branch consumes them.
Capture avoidance covers term binders, dependent shape arguments, dependent
function codomains, motives and branch fields. Each rewritten definition is checked again against its
original type by the carried kernel. Dependency selection then removes
consumed helpers. Any surviving signature program refuses before files
are created. A budget of 4096 visited terms per transformed definition
bounds specialization and reports exhaustion as a refusal. Every global is
specialized once and its specialized body is shared, and a substituted value
keeps one ascription instead of one per binder it passes, so the budget pays
for expansion and not for a second visit to shared work. A helper chain of
depth twelve behind a handler emits; a chain that duplicates its argument at
every level doubles the specialized body and still exhausts the budget.

The executable suite records eight refusals. One of them, the linear
quantity case, is an elaborator refusal that occurs before fusion runs,
not a fusion refusal.

`check`, `axioms`, `emit --native` and `emit --target` retain their previous
behavior. Crates without signatures retain their previous printer path
and golden bytes. The [M0 Todo slice](STAGE-E-TODO.md) adds the complete
executable corpus golden. General recursive handlers, a runtime choice
between signature programs and the timing and exit gates remain ahead.
A recursive call on `resume value` still fails the
carried termination check.

The new modules live in the rechecked surface layer. The kernel, erasers
and target signatures retain their bytes. The printer's measured total
includes the crate pipeline change; numeric allowances remain user rulings.
Validation captures and source hashes live under
`dev/validation/stage-e-handlers/`.
