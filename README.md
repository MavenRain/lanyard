# Lanyard

Lanyard is a language under construction that retains Kanon's kernel and
will emit Rust using Toasty and Topcoat. Its source extension is `.lan`.

Stage A is committed at `52eb5a7`. Stage B adds pinned target signatures,
a generated OCaml metadata library, and source drift checks. Stage C checks
those signatures, elaborates models and operation families, and derives the
foreign-type census. Rust emission and the complete M0 driver remain ahead.
The generated signature allowance is proposed at 104 lines and awaits the
user's ruling. See [target documentation](target/README.md), the
[Stage B build log](dev/M0-BUILD-LOG.md#lanyard-m0-stage-b-2026-09-09) and
the [Stage C build log](dev/spikes/M0-BUILD-LOG.md#stage-c-2026-09-09) with
its [Stage C mutation log](dev/spikes/MUTATION-LOG.md#stage-c-2026-09-09).
The two stages record their work in separate log families.

Build and validate through Stage C:

```sh
zsh dev/gates.sh --stage C
_build/default/bin/lanyard.exe check examples/m0-todo.lan
```

See [Stage C](dev/STAGE-C.md) for the `.lan` declaration grammar and checked
Todo example. The carried `.kan` checker is also available:

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
