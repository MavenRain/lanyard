# SPIKE-ARC, the price of Arc

Date: 2026-09-09.  Spike S7 of M0-PLAN.md section 2, wave Rustc.  Owner
of decision S0-D3.  Gate S0-G10.

Fact 7 of M0-PLAN.md section 12: the Arc atomic is unpriced.  Probe 3b
proves that the Rc form fails the Send assertion, and it does not price
the atomic.  This spike prices the atomic.  It measures and it rules
nothing.  R-Q7 stays ruled: every Many binder lowers to `Arc<T>`, there
is no Rc arm, and the number below is REPORTED and never bound.

## 1 Method

Two single-file probes, one body under `Arc<str>` and one body under
`Rc<str>`.  Neither body holds an `await` and neither body names a
crate.  Both use the standard library only.  No cargo runs and no build
system runs.  Each probe clones the shared pointer 20000000 times inside
a fold, and each clone is dropped at the end of the closure body.  The
measured cost is therefore one clone and its matching drop, which is the
true price of one shared reference.  `std::hint::black_box` wraps the
borrow and the clone, so the optimizer cannot remove the work.  The
probe prints the elapsed time from `std::time::Instant` and the cost per
clone in nanoseconds.

Each binary ran six times: one untimed warm-up and five recorded runs,
per R-V8.  The reported figure per form is the median of the five.

## 2 Probe source, the Arc form

Path: /Users/oobi/Documents/lanyard-m0/spikes/s7/arc_probe.rs

```rust
// lanyard M0 Stage 0 spike S7 probe, the Arc form.
// One body under Arc<str>, no await, no crate, std only.
use std::hint::black_box;
use std::sync::Arc;
use std::time::Instant;

const CLONES: u32 = 20_000_000;
const CLONES_F: f64 = 20_000_000.0;

fn main() {
    let base: Arc<str> = Arc::from("lanyard many binder payload");
    let start = Instant::now();
    let sink = (0..CLONES).fold(0usize, |acc, _| {
        let copy = black_box(Arc::clone(black_box(&base)));
        acc.wrapping_add(copy.len())
    });
    let elapsed = start.elapsed();
    let ns_per_clone = elapsed.as_secs_f64() * 1.0e9 / CLONES_F;
    println!("ARC clones={CLONES} elapsed_ns={} ns_per_clone={ns_per_clone:.4} sink={sink} strong={}", elapsed.as_nanos(), Arc::strong_count(&base));
}
```

## 3 Probe source, the Rc form

Path: /Users/oobi/Documents/lanyard-m0/spikes/s7/rc_probe.rs

```rust
// lanyard M0 Stage 0 spike S7 probe, the Rc form.
// One body under Rc<str>, no await, no crate, std only.
use std::hint::black_box;
use std::rc::Rc;
use std::time::Instant;

const CLONES: u32 = 20_000_000;
const CLONES_F: f64 = 20_000_000.0;

fn main() {
    let base: Rc<str> = Rc::from("lanyard many binder payload");
    let start = Instant::now();
    let sink = (0..CLONES).fold(0usize, |acc, _| {
        let copy = black_box(Rc::clone(black_box(&base)));
        acc.wrapping_add(copy.len())
    });
    let elapsed = start.elapsed();
    let ns_per_clone = elapsed.as_secs_f64() * 1.0e9 / CLONES_F;
    println!("RC clones={CLONES} elapsed_ns={} ns_per_clone={ns_per_clone:.4} sink={sink} strong={}", elapsed.as_nanos(), Rc::strong_count(&base));
}
```

## 4 The two compile lines, verbatim

```
rustup run 1.98 rustc --edition 2024 -O /Users/oobi/Documents/lanyard-m0/spikes/s7/arc_probe.rs -o /Users/oobi/Documents/lanyard-m0/spikes/s7/arc_probe
rustup run 1.98 rustc --edition 2024 -O /Users/oobi/Documents/lanyard-m0/spikes/s7/rc_probe.rs -o /Users/oobi/Documents/lanyard-m0/spikes/s7/rc_probe
```

Both compiles exited 0 and printed no diagnostic.  The runner recorded
`COMPILE-ARC exit=0` and `COMPILE-RC exit=0`.  The compiler is `rustc
1.98.1 (48a229cea 2026-09-01)` from `rustup run 1.98 rustc --version`.

The runner is /Users/oobi/Documents/lanyard-m0/spikes/s7/run-s7.sh and it
ran as one foreground call:

```
zsh /Users/oobi/Documents/lanyard-m0/spikes/s7/run-s7.sh
```

## 5 Loop count and raw runs

Loop count per run: 20000000 clones.  Runs per form: 5 recorded, after 1
untimed warm-up.  The raw log is
/Users/oobi/Documents/lanyard-m0/spikes/s7/runs.txt and every line of it
is quoted here.

```
COMPILE-ARC
COMPILE-ARC exit=0
COMPILE-RC
COMPILE-RC exit=0
UPTIME-BEFORE  6:56  27 users, load averages: 14.84 13.59 10.97
WARMUP-ARC ARC clones=20000000 elapsed_ns=1272136750 ns_per_clone=63.6068 sink=540000000 strong=1
RUN-ARC 1 ARC clones=20000000 elapsed_ns=613504750 ns_per_clone=30.6752 sink=540000000 strong=1
RUN-ARC 2 ARC clones=20000000 elapsed_ns=124823042 ns_per_clone=6.2412 sink=540000000 strong=1
RUN-ARC 3 ARC clones=20000000 elapsed_ns=1395466958 ns_per_clone=69.7733 sink=540000000 strong=1
RUN-ARC 4 ARC clones=20000000 elapsed_ns=448418667 ns_per_clone=22.4209 sink=540000000 strong=1
RUN-ARC 5 ARC clones=20000000 elapsed_ns=196610958 ns_per_clone=9.8305 sink=540000000 strong=1
WARMUP-RC RC clones=20000000 elapsed_ns=89136875 ns_per_clone=4.4568 sink=540000000 strong=1
RUN-RC 1 RC clones=20000000 elapsed_ns=87960250 ns_per_clone=4.3980 sink=540000000 strong=1
RUN-RC 2 RC clones=20000000 elapsed_ns=98419000 ns_per_clone=4.9210 sink=540000000 strong=1
RUN-RC 3 RC clones=20000000 elapsed_ns=83900792 ns_per_clone=4.1950 sink=540000000 strong=1
RUN-RC 4 RC clones=20000000 elapsed_ns=81480041 ns_per_clone=4.0740 sink=540000000 strong=1
RUN-RC 5 RC clones=20000000 elapsed_ns=82196042 ns_per_clone=4.1098 sink=540000000 strong=1
UPTIME-AFTER  6:57  27 users, load averages: 16.85 14.03 11.14
```

The warm-up run of each form is untimed by the method and it is not in
any median.  It is quoted for the record.

## 6 The medians and the price of the atomic

The median came from `python3 -P` over the five recorded values per
form.  The printed lines:

```
ARC sorted [6.2412, 9.8305, 22.4209, 30.6752, 69.7733]
RC sorted [4.074, 4.1098, 4.195, 4.398, 4.921]
ARC median_ns_per_clone=22.4209 runs=5 min=6.2412 max=69.7733
RC  median_ns_per_clone=4.1950 runs=5 min=4.0740 max=4.9210
DIFF median 18.2259
DIFF min-to-min 2.1672
```

| form | cost per clone | runs | loop count | min | max |
| --- | --- | --- | --- | --- | --- |
| `Arc<str>` | 22.4209 ns | 5 | 20000000 | 6.2412 ns | 69.7733 ns |
| `Rc<str>` | 4.1950 ns | 5 | 20000000 | 4.0740 ns | 4.9210 ns |

The price of the atomic is the difference of the two medians:

```
22.4209 ns minus 4.1950 ns = 18.2259 ns per clone
```

The quietest run of each form gives a second view of the same price:
6.2412 ns minus 4.0740 ns is 2.1672 ns per clone.  The two views differ
by a factor of eight, and the load average is the reason.  The median is
the reported figure, per R-V8.  The min to min figure is recorded beside
it as an observation, and it is not a second number to choose from.

## 7 NOISY

NOISY.  The load average was 14.84 before the measured leg and 16.85
after it, and the plan marks a timing spike NOISY above load average 4.
The Arc spread of 6.2412 ns to 69.7733 ns across five runs is the shape
of that load.  The Rc spread of 4.0740 ns to 4.9210 ns is tight, because
the Rc body is a non atomic increment and it stays on one core.

NOISY is recorded here and in the log row.  It is not a halt blocker.
No number was dropped and no run was repeated to find a quiet minute.
The gate S0-G10 passes by SHAPE, so the NOISY mark does not change the
result.

## 8 Load averages and disk

| point | command | load averages |
| --- | --- | --- |
| window start | `uptime` | 13.12 13.17 10.73 |
| before the measured leg | `uptime` inside the runner | 14.84 13.59 10.97 |
| after the measured leg | `uptime` inside the runner | 16.85 14.03 11.14 |
| window end | `uptime` | 29.99 17.55 12.56 |

Both binaries were deleted once the medians were recorded:

```
rm -f /Users/oobi/Documents/lanyard-m0/spikes/s7/arc_probe /Users/oobi/Documents/lanyard-m0/spikes/s7/rc_probe
```

`ls -l` before the delete printed arc_probe at 490408 bytes and rc_probe
at 490584 bytes, 980992 bytes of build output in total.  `ls -l` after
the delete printed four text files and no binary.

Bytes left under /Users/oobi/Documents/lanyard-m0/spikes/s7: 4865 bytes
in five text files, which is 20 KB by `du -sk`.  The five files are
arc_probe.rs at 769 bytes, rc_probe.rs at 759 bytes, run-s7.sh at 833
bytes, runs.txt at 1317 bytes and check-s7.sh at 1187 bytes.  They are
the two sources, the runner, the raw log and the closing check script,
which section 3.1 of the brief keeps in the spike directory.  No build
output remains, and the largest file left is 1317 bytes.  `df -g
/System/Volumes/Data` printed 29 GiB free after the delete.

## 9 Decision S0-D3, the Arc price wording

Owner: S7.  Status: RECORDED by this agent.  The user rules it.

The exact sentence M0-TIME prints for the REPORTED column:

```
REPORTED: one Arc clone and its matching drop costs 22.4209 ns and one Rc clone and its matching drop costs 4.1950 ns, so the price of the atomic is 18.2259 ns per clone, median of five runs at 20000000 clones, NOISY at load average 16.85;  this number is reported at M0 and it binds at no milestone.
```

The statement that goes with the number: the Arc price is REPORTED at M0
and it is bound at no milestone.  M0-TIME prints the medians and the
ratio and binds nothing, per M0-PLAN.md section 9.  R-Q4 keeps the Arc
price out of R3, and R-Q7 and R-V7 keep the Arc lowering with no Rc arm.
A later milestone may print a new number, and no milestone may turn this
number into a bound.

## 10 What this spike closes and what it does not

Closed: fact 7.  The atomic now has a price on this machine, 18.2259 ns
per clone by the median of five, with the raw runs and the load beside
it.

Not closed and out of scope: any change to the R-Q7 lowering, any Rc arm
in the emitter, any claim that binds the number, any cargo or crate
work, and the Send assertion, which is spike S9.

## 11 Gate pair for this window

S0-G1, S0-G2 and S0-G3 ran at the start of this agent's work and again
at the end.  The two readings match.

| gate | start | end |
| --- | --- | --- |
| S0-G1 | `ls: /Users/oobi/Documents/lanyard: No such file or directory` | same line |
| S0-G2 | porcelain 0, HEAD 046689a78ef6708404bd190dc86845cbee0bb36f | porcelain 0, same HEAD |
| S0-G3 | toasty 7bd502cbf44cc47f70db9f2b27ab35d77a096364, topcoat 51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a | same two sha values |

S0-G10 shape check over this file, by rg line counts: 16 lines carry the
per clone cost token, 2 lines carry the compile command, 5 lines carry
the three nanosecond figures 22.4209, 4.1950 and 18.2259, and 8 lines
carry the Arc or the Rc pointer type.  The only await token in either
probe source is the comment on line 2 of each file, printed by rg with
the file and the line number, and no probe body holds one.

S0-G13 prose check over this file, the two probe sources and the runner:
the rg pattern was built with `printf` over the two code points U+2014
and U+2013, and rg printed no match and exited 1.  Zero em-dashes and
zero en-dashes.  `tail -c 1` on this file prints `0a`, so the file ends
with a newline.

No path outside /Users/oobi/Documents/lanyard-m0/spikes was written by
this spike.  Nothing was staged and nothing was committed.
