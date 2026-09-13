# Classified axiom disclosure

Stage F adds the axioms instrument of M0-PLAN section 8:

```sh
zsh dev/gates.sh --stage F-axioms
_build/default/bin/lanyard.exe axioms corpus/m0/todo.lan
```

The report sorts entries by class and then kernel name, prints each
statement, and ends with four class counts, their total and the two
AXIOM-RATIO inputs. The Todo report is frozen in `corpus/m0/axioms.txt`:

```text
COUNT Framework=1
COUNT Foreign=17
COUNT Classical=0
COUNT Div=0
AXIOMS total=18
AXIOM-RATIO constants=17 definitions=3 status=REPORTED
```

Framework names `imax_zero`, the `imax l zero = zero` assumption already
documented in SPEC section 6. Foreign includes the checked target rows
and generated model instances. Each Foreign entry names its source
schema, and the header identifies the compiled catalog by SHA-256.
Classification uses exact catalog names and checked instance metadata.
An ordinary definition named `ghost_create` is still a definition.

Classical has no installed constants at M0. A source declaration named
`propext` or `Classical_choice` does not acquire a Classical class just
from its name. Div reads the carried checked definition's `partial`
marker. The M0 surface does not construct that marker; a unit test
exercises it directly without adding partial definitions to the language.

The scope is the full checked module before crate dependency selection.
Every installed target row counts once, even when unused. Generated
model operations count separately from their generic schemas. Thus an
empty `.lan` source has 15 Foreign entries and zero definitions. This
is an inventory of the module's assumptions, not a main-only dependency
report. The ambient Nat and native primitive environment is outside the
module inventory, following the carried declaration-disclosure convention.

The AXIOM-RATIO numerator counts Foreign entries only. Its denominator
counts checked `Global.Def` rows without the partial marker, including
model products and type aliases. Family and constructor metadata,
postulates and native primitives do not count as definitions. Todo's
three definitions are Bool, Todo and main. The instrument prints inputs
even when there are zero definitions; it neither divides nor enforces
a bound at M0.

The four-class policy supplies no class for arbitrary source postulates.
The classified command returns exit 1 with the first unclassified name
and no stdout. It does not change which source declarations the checker
accepts. The declaration-name command remains available:

```sh
_build/default/bin/lanyard.exe axioms --names examples/m0-todo.lan
```

`--names` preserves declaration order, including every source postulate.
The default command on `.kan` files retains its old name-only contract.
Malformed argument lists return exit 64. Reports are printed only after
the full file checks and every module postulate has a class, so a type
error or unclassified declaration cannot leave a partial report.

The cumulative gate includes the Todo emission golden and all previous
stages. Focused checks cover 10 CLI observations, 11 refusals and two
checked-entry observations. Four separate compiler mutations remove
model provenance, falsify the ratio count, silently classify a source
postulate and ignore a partial marker. Each must build successfully and
then fail its designated report test. The restored compiler must pass.

Captures and source hashes live in `dev/validation/stage-f-axioms/`.
The kernel, target signature generator, target rows and emitted Rust
retain their committed bytes. The timing instrument, combined M0 gate,
numeric allowance rulings and M0 exit stamp remain ahead.
