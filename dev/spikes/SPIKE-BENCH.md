# SPIKE-BENCH, spike S2, the timing tool

Date: 2026-09-09.  Wave Timing, first of two.  This spike ran alone.  No
other timing spike ran beside it.

Fact 2 of M0-PLAN.md section 12: P3 cites dev/bench.sh:1-9 as the timing
tool while probes 1 and 1b timed by hand.  This spike runs the pin's own
dev/bench.sh over a fixed input and compares its median against a
python3 perf_counter median of five over the same command.

NOISY: YES.  The load average is far above 4 for the whole window, so
this spike is NOISY by M0-PLAN.md section 9 and R-V8.  Every number below
is kept.  NOISY never drops a number and it never orders a rerun.

## 1 Inputs

Pin worktree: /Users/oobi/Documents/kan-rust-lang-kanon-pin at
046689a78ef6708404bd190dc86845cbee0bb36f.  The worktree is READ ONLY.

Binary under test: /Users/oobi/Documents/kan-rust-lang-kanon-pin/_build/default/bin/kanon.exe.
The binary is prebuilt and it was run READ ONLY.  Nothing rebuilt it and
nothing built a copy of it.

Input file: /Users/oobi/Documents/kan-rust-lang-kanon-pin/test/corpus/m1-corpus.kan.
It is the pin's own corpus file and its line count is 1000 lines, which
is the "about 1000 lines" the brief asks for.

```
$ wc -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/test/corpus/m1-corpus.kan
    1000 /Users/oobi/Documents/kan-rust-lang-kanon-pin/test/corpus/m1-corpus.kan
```

The input was chosen with this command, which lists every corpus file of
the pin by line count:

```
$ fd -g '*.kan' /Users/oobi/Documents/kan-rust-lang-kanon-pin -x wc -l | sort -rn | head -12
```

m1-corpus.kan at 1000 lines is the only pin file at exactly 1000 lines.
The five agreement files above it are 1132 to 1134 lines.

Timed command, one string, identical on both legs:

```
/Users/oobi/Documents/kan-rust-lang-kanon-pin/_build/default/bin/kanon.exe check /Users/oobi/Documents/kan-rust-lang-kanon-pin/test/corpus/m1-corpus.kan
```

It exits 0 on this input:

```
$ /Users/oobi/Documents/kan-rust-lang-kanon-pin/_build/default/bin/kanon.exe check /Users/oobi/Documents/kan-rust-lang-kanon-pin/test/corpus/m1-corpus.kan > /dev/null 2>&1; echo "exit=$?"
exit=0
```

## 2 The tool listing

```
$ ls -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/bench.sh
-rwxr-xr-x@ 1 oobi  staff  1755 Sep  8 20:51 /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/bench.sh
```

```
$ wc -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/bench.sh
      67 /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/bench.sh
```

The script takes the form dev/bench.sh NAME CMD.  It runs CMD once
untimed as a warm-up, then RUNS timed runs with RUNS at 5 by default.  It
times with perf_counter_ns around subprocess.run, and it sends the child
stdout and stderr to /dev/null.  It prints exactly one line.  The script
writes no file.

## 3 Commands, verbatim

Every command below ran through the runner script
/Users/oobi/Documents/lanyard-m0/spikes/s2/s2-run.zsh, which was invoked
as `zsh /Users/oobi/Documents/lanyard-m0/spikes/s2/s2-run.zsh`.  The
runner holds these lines in this order:

```
ls -l $PIN/dev/bench.sh
wc -l $IN
uptime
zsh $PIN/dev/bench.sh kanon-check-m1-corpus "$CMD"
uptime
python3 -P /Users/oobi/Documents/lanyard-m0/spikes/s2/s2-median.py "$CMD" 5
uptime
```

with PIN=/Users/oobi/Documents/kan-rust-lang-kanon-pin,
BIN=$PIN/_build/default/bin/kanon.exe, IN=$PIN/test/corpus/m1-corpus.kan
and CMD="$BIN check $IN".  Fully expanded, the two measured legs are:

```
zsh /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/bench.sh kanon-check-m1-corpus "/Users/oobi/Documents/kan-rust-lang-kanon-pin/_build/default/bin/kanon.exe check /Users/oobi/Documents/kan-rust-lang-kanon-pin/test/corpus/m1-corpus.kan"
```

```
python3 -P /Users/oobi/Documents/lanyard-m0/spikes/s2/s2-median.py "/Users/oobi/Documents/kan-rust-lang-kanon-pin/_build/default/bin/kanon.exe check /Users/oobi/Documents/kan-rust-lang-kanon-pin/test/corpus/m1-corpus.kan" 5
```

The python probe runs one untimed warm-up and then five timed runs.  It
starts the same command through /bin/zsh -f -c, with stdin, stdout and
stderr on /dev/null, and it times with time.perf_counter around
subprocess.run.  Its source is
/Users/oobi/Documents/lanyard-m0/spikes/s2/s2-median.py.

## 4 The printed lines

The pin tool printed one BENCH line.  Verbatim:

```
BENCH kanon-check-m1-corpus median_ms=16.249 min_ms=15.603 max_ms=17.209 runs=5
```

No BENCH-ERROR line was printed.  The leg exited 0, printed as
`bench_exit=0`.

The python probe printed:

```
PY-MEDIAN kanon-check-m1-corpus median_ms=15.861 min_ms=15.258 max_ms=17.209 runs=5 warm_exit=0 codes=[0, 0, 0, 0, 0]
PY-SAMPLES 17.209 16.202 15.506 15.861 15.258
```

## 5 The two medians and the agreement figure

| leg | tool | median ms | min ms | max ms | runs | warm-up |
| --- | --- | --- | --- | --- | --- | --- |
| A | pin dev/bench.sh | 16.249 | 15.603 | 17.209 | 5 | 1 untimed |
| B | python3 -P perf_counter probe | 15.861 | 15.258 | 17.209 | 5 | 1 untimed |

The absolute difference is 0.388 ms.  Against the python median it is
2.45 percent.  Against the mean of the two medians, 16.055 ms, it is 2.42
percent.  The arithmetic:

```
$ python3 -P -c "b=16.249; p=15.861; print('diff_ms=%.3f'%(b-p)); print('pct_vs_py=%.2f'%((b-p)/p*100)); print('pct_vs_mean=%.2f'%((b-p)/((b+p)/2)*100)); print('mean=%.4f'%((b+p)/2))"
diff_ms=0.388
pct_vs_py=2.45
pct_vs_mean=2.42
mean=16.0550
```

2.45 percent is below the 5 percent line of M0-PLAN.md section 2 row S2.
The two instruments agree.  There is no finding here and no requirement
to write dev/bench.py new for the pin method.

## 6 Load averages

```
$ uptime   (before the bench.sh leg)
 7:04  27 users, load averages: 14.90 20.42 16.73
$ uptime   (after the bench.sh leg, before the python leg)
 7:04  27 users, load averages: 14.90 20.42 16.73
$ uptime   (after the python leg)
 7:04  27 users, load averages: 14.90 20.42 16.73
```

The one minute load average is 14.90 before and 14.90 after.  The whole
window took less than one sampling period of the load average, so the
three readings are equal.  The window gate pair also read `load averages:
19.32 22.92 16.98` at 07:02 before the first gate run.

NOISY: YES, earned by the one minute load average 14.90, which is above
the 4 line.  The numbers are kept and reported, and nothing binds on
them.

## 7 Bytes left on disk

```
$ du -sk /Users/oobi/Documents/lanyard-m0/spikes/s2
8	/Users/oobi/Documents/lanyard-m0/spikes/s2
```

8 KiB, which is the runner script s2-run.zsh at 639 bytes and the python
probe s2-median.py at 874 bytes.  Both are source, not build output.  This
spike compiled nothing and it built nothing, so it left no build output to
delete.  No file above 50 MB exists under the scratch tree of this spike.

```
$ df -g /System/Volumes/Data | tail -1
/dev/disk3s5       460  353        29    93% 6693588 308034080    2%   /System/Volumes/Data
```

29 GiB free, at the floor and not under it.

## 8 Decision S0-D5, the S2 timing tool

RECORDED, not ruled.  The user rules it.

Statement: the pin's dev/bench.sh stands as the Stage F timing
instrument.  Stage F may take dev/bench.py as a copy of the pin script
with the same method, and it does not need a new method.

Evidence: one BENCH line printed, `BENCH kanon-check-m1-corpus
median_ms=16.249 min_ms=15.603 max_ms=17.209 runs=5`, against a python3
perf_counter median of five at 15.861 ms over the identical command, a
difference of 0.388 ms, which is 2.45 percent and under the 5 percent
line.

Reason: M0-PLAN.md section 9 writes dev/bench.py new unless spike S2
shows the pin's dev/bench.sh agrees.  S2 shows agreement, so the "unless"
clause is met.  The pin script already carries the R-V8 method: one
untimed warm-up, five timed runs, a python perf_counter timer, and the
interpreter start-up outside every measurement.  What Stage F still adds
is the R3 reporting shape, which is F and m and the two medians of
section 9, and the load average line.  Those are outputs, not a timing
method, so they extend the pin script rather than replace it.

Consequence if the user rules the other way: dev/bench.py is written new
and this measurement stands as the acceptance test for it, since a new
tool must land inside 5 percent of both numbers above.

## 9 Gate S0-G5, BENCH

PASS, by shape.  The gate never passes or fails on a threshold in
milliseconds.

- One `BENCH NAME median_ms=... min_ms=... max_ms=... runs=5` line is
  held verbatim in section 4.  No BENCH-ERROR line was produced.
- The second median is 15.861 ms with run count 5, in sections 4 and 5.
- The percentage difference 2.45 percent is stated beside the 5 percent
  line, in section 5.
- The NOISY mark is in section 6 with the load average 14.90 that earned
  it.

## 10 Out of scope, as the brief writes it

No build of the pin and no build of a copy of the pin ran.  The pin
binary was read and executed, never written.  Nothing inside
/Users/oobi/Documents/kan-rust-lang-kanon-pin was written.  No binding
claim is made from either number: both are REPORTED at M0 and neither
binds at any milestone.  No other timing spike ran beside this one.
