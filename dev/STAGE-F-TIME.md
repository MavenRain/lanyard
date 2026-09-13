# M0 timing instrument

Stage F adds the S2 timing method and the R3 reporting shape:

```sh
zsh dev/gates.sh --stage F-time
python3 -P dev/bench.py --refit-go --output /tmp/lanyard-time.json
```

The compiler must already be built. The stage gate builds it through the
cumulative F-axioms gate, runs the timing tests, then measures. A timing
run reports observations and binds no speed, slope or ratio threshold.
A failed child, changed input or missing tool fails the instrument.
The gate saves raw JSON under a fresh `.gatework/stage-f-time.*` directory
and prints its path as `M0-TIME-RAW`.

Every command receives one untimed warm-up and five measured runs. The
Python interpreter starts outside the timer. Compiler commands use the
S2 `/bin/zsh -f -c` invocation with shell-quoted arguments. Each sample
uses `perf_counter_ns` around the child process. Input generation,
dependency warm-up, load sampling and output cleanup are outside that
interval. Both stdout and stderr are discarded during timing, as in S2.
Child failures report the command and exit code. Go metadata probes
capture stderr outside timing to provide preparation diagnostics.
Timed children use S2's blocking wait. Python's timeout wait polls when
pipes are discarded and would distort short measurements. A timeout
for an unattended run should wrap the whole Python invocation.

The native corpus has 100, 500 and 1000 one-line Nat functions. Each
line declares a distinct function with an addition; there are no blank
or comment padding lines. `check` measures checking and `emit --target`
measures checking plus printing the complete module. Both include the
fixed target catalog. Module emission retains every declaration, so
crate dependency selection cannot turn the larger inputs into the same
small output. These synthetic fits describe native declaration tables,
not an application with that many lines. The instrument separately
measures checking and complete crate emission of `corpus/m0/todo.lan`,
including its model-output option. Cargo and execution are outside all
compiler timings. The Todo source is copied before warm-up so both
commands measure identical bytes throughout the run.

Ordinary least squares fits `milliseconds = F + m * kloc` to each native
mode. The report retains F, m, R squared, every raw sample and its
median, minimum and maximum. It compares the total predictions at the
same 1.000 kloc and also reports the slope ratio. A nonpositive Go
denominator yields `UNAVAILABLE` for the affected ratio; a constant
response has no R squared. Negative fitted slopes are kept as measured.

Without `--refit-go`, the denominator is the frozen S4 fit, explicitly
labelled `frozen-S4` and NOISY. This mode never claims a same-minute
comparison. The SHA-256 pins the complete `dev/spikes/denominators.json`
artifact, including its thirteen package names and input sizes.

`--refit-go` repeats S4 over all thirteen packages. It requires the
frozen Go version and platform and checks each package's GoFiles count
and line count. It copies standard packages and their hidden imports
to a private temporary module, using S4's quoted import-path rewrite.
A package with cgo files or embedded files is refused by name. The
scratch `go.mod` takes its language version from the verified Go
release, so it cannot drift from the frozen toolchain.
The selected Go target is explicit; user GOFLAGS and module settings
do not select another build. Go proxy and checksum network access are
disabled. Sources, module files and caches stay in that temporary tree,
which is removed when the run ends. GOROOT is read only.

Go warm-ups fill dependency caches. Appending a fresh comment to one
file before each build forces recompilation of that package while
keeping its dependencies cached. Original GoFiles line counts exclude
these added comments. The JSON records the copied source hashes before
touches, the Go version and the denominator artifact hash. A refit
never replaces the frozen artifact or silently drops a failing package.

All warm-ups finish before the shared measurement window begins. The
compiler and Go commands then run sequentially. `same_minute=true`
means a `--refit-go` run whose window lasted at most sixty seconds.
A longer refit window is reported as false, and a frozen-denominator
run is always false. Neither case retries or discards observations.
Load averages are sampled once at the start of the window and then
before and after each timed child. The untimed warm-ups take no
reading, so a load spike inside a warm-up cannot mark the run NOISY.
Any one-minute load above 4 marks the run NOISY; equality at 4 does not. M0 timings remain
informational at every load and window length.

The last line is the exact S0-D3 Arc-price sentence from the ratified
spike. It reports the historical clone/drop measurement and never
pretends to remeasure Arc. The optional JSON destination must be a new
file, and its parent directory must exist and be writable before the
measurement starts. The document is serialized before the file is
created, so a value the format rejects leaves no partial file. The CLI prints a success report only after all measurements and
the requested JSON write succeed. Invalid arguments exit 2; measurement
and output errors exit 1 with an `M0-TIME ERROR` diagnostic on stderr.

Validation evidence is under `dev/validation/stage-f-time/`. The kernel,
target catalog, emitted Rust and Todo golden keep their existing bytes.
The [combined M0 gate](STAGE-F-GATES.md) now runs this instrument.
Numeric allowance rulings and the user's M0 exit stamp remain open.
