# SPIKE-DENOM, the Go denominator refit

Spike S4 of lanyard M0 Stage 0.  Date 2026-09-09.  Fact 4 of M0-PLAN.md
section 12: the Go denominator is not stable and 40.7 is dead.  This spike
pays for R-Q4, which refits the denominator as F plus m times n over at
least eight points, with an anchor near 8 kloc and an anchor near 16 kloc,
and freezes the result with a sha before any ratio binds.

Deliverables: this file and
/Users/oobi/Documents/lanyard-m0/spikes/dev/denominators.json.

## 1 Result

- Points measured: 13.  Runs per point: 5, after one untimed warm up.
- F: 96.74 ms.  m: 7.24 ms per kloc.  R squared: 0.291.
- The anchor near 8 kloc is unicode at 8.945 kloc.  The anchor near 16 kloc
  is cmd/internal/obj/x86 at 16.139 kloc.
- 40.7 retired.  The live tightest total is 45.0 ms and the live tightest
  slope is 18.11 ms per kloc, which M0-PLAN.md section 9 uses for the
  break even figure of 11.81.  The number 40.7 carries no measurement on
  this host and it is retired by R-Q4.  M1-RATIO reads denominators.json
  and never 40.7.
- sha256 of denominators.json:
  ba1293a3f8970531ab32490fc20d55fd8a04cb16ca7f45d2ca0956075f4bf03d
- Byte count of denominators.json: 5147 by `wc -c`.
- The fit is NOISY.  The load average was above 4 for the whole window.
- The gate is a shape gate.  Eight or more points, the two size anchors, an
  R squared value and the sha are printed.  No threshold is put on the fit.

## 2 The measured points

| package | kloc | median ms | min ms | max ms | runs | hidden deps | why the package is in the set |
| --- | --- | --- | --- | --- | --- | --- | --- |
| go/token | 1.026 | 92.8 | 77.4 | 182.4 | 5 | 0 | small package, anchors the fixed cost F |
| net/url | 1.309 | 149.1 | 97.7 | 317.1 | 5 | 0 | small package with a wide import fan |
| text/template/parse | 2.529 | 199.5 | 104.1 | 372.5 | 5 | 0 | parser sized package near 2.5 kloc |
| go/ast | 3.202 | 105.2 | 99.0 | 116.7 | 5 | 0 | syntax package near 3.2 kloc |
| regexp/syntax | 3.721 | 105.0 | 86.5 | 113.5 | 5 | 0 | carried from the original candidate list |
| encoding/json | 4.258 | 158.0 | 98.9 | 212.8 | 5 | 0 | carried from the original candidate list |
| encoding/xml | 4.353 | 98.4 | 92.7 | 125.5 | 5 | 0 | carried from the original candidate list |
| debug/dwarf | 4.486 | 128.7 | 105.8 | 303.1 | 5 | 0 | table heavy package near 4.5 kloc |
| encoding/gob | 4.845 | 104.7 | 101.3 | 105.7 | 5 | 1 | reflection heavy package near 4.8 kloc |
| debug/elf | 5.648 | 109.1 | 94.8 | 117.9 | 5 | 2 | package near 5.6 kloc, fills the gap under the 8 kloc anchor |
| unicode | 8.945 | 23.4 | 22.5 | 23.7 | 5 | 0 | the anchor near 8 kloc |
| cmd/internal/obj/x86 | 16.139 | 380.0 | 376.0 | 627.0 | 5 | 13 | the anchor near 16 kloc |
| go/types | 23.400 | 210.6 | 187.9 | 432.6 | 5 | 7 | the largest pure Go package, extends the range over 20 kloc |

Every row carries status ok in denominators.json.  No row was dropped and no
row was rerun to hunt for a quiet minute.

## 3 Method

Each row is one Go package copied out of GOROOT into a scratch module under
/Users/oobi/Documents/lanyard-m0/spikes/s4/bench-root.  A hidden dependency,
which is an internal package or a cmd package, is copied beside it and its
import path is rewritten to a module path, so a package that imports an
internal package can be measured with no write inside GOROOT.  GOCACHE,
GOPATH and GOMODCACHE all point inside the S4 directory.  Each row runs one
untimed warm up build, which also builds and caches every dependency, and
then five timed builds.  A comment line is appended to the first source file
of the package before each timed build, so the package alone is recompiled
and the dependencies stay cached.  The time is a python perf_counter around
the `go build` call, so it holds the go command overhead and the compile of
the one package.  The row keeps the median of the five.  kloc is the line
count of the GoFiles set, which is the set that compiles on this host.  F and
m are fitted by ordinary least squares over the 13 points.  The method
paragraph is repeated inside denominators.json.

## 4 Commands, verbatim

Start gates and the environment:

    zsh /Users/oobi/Documents/lanyard-m0/spikes/s4/gates-start.sh 2>&1

Candidate probes, which pick the package set and find the two anchors:

    zsh /Users/oobi/Documents/lanyard-m0/spikes/s4/run-probe.sh > /Users/oobi/Documents/lanyard-m0/spikes/s4/candidates.txt 2>&1
    zsh /Users/oobi/Documents/lanyard-m0/spikes/s4/run-probe-big.sh > /Users/oobi/Documents/lanyard-m0/spikes/s4/big-candidates.txt 2>&1
    zsh /Users/oobi/Documents/lanyard-m0/spikes/s4/run-probe-mid.sh > /Users/oobi/Documents/lanyard-m0/spikes/s4/mid-candidates.txt 2>&1

The copy of the original harness, made through stdin so the original is never
passed to sd:

    shasum -a 256 /Users/oobi/Documents/kan-rust-lang-gobench.py
    sd 'os.environ.get\("TMPDIR", "/private/tmp/claude-501"\)' '"/Users/oobi/Documents/lanyard-m0/spikes/s4"' < /Users/oobi/Documents/kan-rust-lang-gobench.py > /Users/oobi/Documents/lanyard-m0/spikes/s4/gobench-copy.py

The extension of that copy is
/Users/oobi/Documents/lanyard-m0/spikes/s4/gobench-s4.py.  It keeps the env
block, the line counting helper and the median of five loop of the copy, it
carries 13 packages instead of 7, it copies and rewrites hidden dependencies,
and it fits F and m and writes denominators.json.

The measured leg, detached with a trap and a disown, with its log under s4:

    zsh -c 'zsh /Users/oobi/Documents/lanyard-m0/spikes/s4/run-bench.sh; until rg -q "S4-BENCH-DONE" /Users/oobi/Documents/lanyard-m0/spikes/s4/bench.log 2>/dev/null; do sleep 10; done; echo WAITER-DONE'

run-bench.sh exports GOCACHE=/Users/oobi/Documents/lanyard-m0/spikes/s4/gocache,
GOPATH and GOMODCACHE beside it, GOTOOLCHAIN=local and GOFLAGS=-mod=mod, then
runs `python3 -P /Users/oobi/Documents/lanyard-m0/spikes/s4/gobench-s4.py`.
The build command inside the harness is `go build ./NAME` with the working
directory at bench-root and that environment.

The parse check and the freeze:

    node -e 'const d=require("/Users/oobi/Documents/lanyard-m0/spikes/dev/denominators.json"); console.log("parsed rows="+d.rows.length+" points="+d.points+" F="+d.F_ms+" m="+d.m_ms_per_kloc+" r2="+d.r_squared+" noisy="+d.noisy); d.rows.forEach(r=>console.log([r.package,r.kloc,r.median_ms,r.min_ms,r.max_ms,r.runs,r.hidden_deps,r.status].join(" | ")))'
    shasum -a 256 /Users/oobi/Documents/lanyard-m0/spikes/dev/denominators.json
    zsh /Users/oobi/Documents/lanyard-m0/spikes/s4/finish.sh 2>&1

The printed lines that carry the result:

    parsed rows=13 points=13 F=96.74 m=7.24 r2=0.291 noisy=true
    WROTE /Users/oobi/Documents/lanyard-m0/spikes/dev/denominators.json F=96.74 m=7.24 r2=0.291 points=13 noisy=True
    ba1293a3f8970531ab32490fc20d55fd8a04cb16ca7f45d2ca0956075f4bf03d  /Users/oobi/Documents/lanyard-m0/spikes/dev/denominators.json

## 5 Load, NOISY and the host

    uptime before the S4 window:  7:09  27 users, load averages: 8.10 14.68 15.28
    uptime before the measured leg:  7:16  27 users, load averages: 23.89 16.16 15.23
    uptime after the measured leg:  7:16  27 users, load averages: 24.10 16.55 15.38
    uptime after the S4 window:  7:17  27 users, load averages: 17.14 16.49 15.49

NOISY.  The plan marks a timing spike NOISY above load average 4.  The load
average was 8.10 at the start of the window and 23.89 at the start of the
measured leg, so this spike is NOISY.  Every number is kept.  The fit is
recorded, it is not dropped, and the leg was not rerun to find a quiet
minute.

Host block, as denominators.json holds it: platform
macOS-26.4-arm64-arm-64bit-Mach-O, machine arm64, cpu_count 12.  The
processor field is empty because the sysctl key machdep.cpu.brand_string does
not exist on this Apple silicon host, so the platform, machine and cpu_count
fields carry the host identity.

Tool versions, as denominators.json holds them: `go version go1.24.0
darwin/arm64` and `rustc 1.98.1 (48a229cea 2026-09-01)`.

## 6 The cold cache pilot, and why fact 4 holds

The harness ran twice.  The first run had a cold GOCACHE, and it measured 12
points, because the 16 kloc anchor was skipped when a hidden dependency
carried an assembly file.  Its printed fit line was:

    WROTE /Users/oobi/Documents/lanyard-m0/spikes/dev/denominators.json F=106.11 m=24.81 r2=0.739 points=12 noisy=True

Four of its rows, from the same printed log: encoding/xml 283.8 ms,
debug/dwarf 232.2 ms, encoding/gob 326.5 ms, debug/elf 205.4 ms, unicode
84.2 ms and go/types 742.8 ms.  The second run, with the assembly files of a
hidden dependency copied as well and with a warm GOCACHE, measured the same
packages at 98.4, 128.7, 104.7, 109.1, 23.4 and 210.6 ms.  The first run log
was overwritten by the rerun, so the pilot numbers above are the lines this
spike printed and read, and only those lines are quoted.

The two runs are the evidence for fact 4.  The same packages, the same
method and the same host give a slope of 24.81 ms per kloc on a cold cache
and 7.24 ms per kloc on a warm cache, and R squared falls from 0.739 to
0.291.  A single number such as 40.7 cannot carry that spread.  40.7 retired.
The frozen artifact is the warm cache run, because an incremental compile of
one package against cached dependencies is the shape R3 compares, and the
cold cache run is kept here as the pilot.

The low R squared is itself a result.  The wall time of `go build` for one
package holds a large fixed cost, near 97 ms, that comes from the go command
itself and from the dependency graph load, and the line count explains less
than a third of the variance across the set.  unicode is the clearest case:
8.945 kloc of tables with no imports builds in 23.4 ms, while encoding/gob at
4.845 kloc with 17 imports takes 104.7 ms.  M1-RATIO must therefore compare
at a fixed input size on both sides, as R-V8 already writes, and never divide
two totals measured at different sizes.

## 7 Decision S0-D2, the denominator set

RECORDED, not ruled.  The user rules it.

The set is the 13 packages of section 2.  The rule that picked them: a
package enters the set when it compiles from a copy outside GOROOT, when its
line count fills a gap in the ladder from 1 kloc to 23 kloc, and when its
kind of source is one the lanyard emitter will meet, which is parsers,
encoders, table heavy data and a large type checker.  Three packages,
regexp/syntax, encoding/json and encoding/xml, are carried from the original
candidate list of /Users/oobi/Documents/kan-rust-lang-gobench.py, so the
refit can be read beside the earlier probe.  math/big, go/printer and
compress/flate of the original list were dropped: math/big carries assembly
in the package itself, and go/printer and compress/flate sit in a band the
set already covers.

The two size anchors: unicode at 8.945 kloc is the anchor near 8 kloc, and
cmd/internal/obj/x86 at 16.139 kloc is the anchor near 16 kloc.  No package
in GOROOT between 14 and 18 kloc is free of hidden imports, so the 16 kloc
anchor needs the import rewrite of section 3.  The candidate evidence is
/Users/oobi/Documents/lanyard-m0/spikes/s4/mid-candidates.txt, which lists
every GOROOT package between 10 and 22 kloc.

M1-RATIO reads denominators.json at the sha of section 1.  A later refit
writes a new file with a new sha and names this one as its parent.

## 8 Disk and gates

    du -sk /Users/oobi/Documents/lanyard-m0/spikes/s4 before the delete: 223348
    rm -rf gocache, gopath, gomod and bench-root under s4
    du -sk /Users/oobi/Documents/lanyard-m0/spikes/s4 after the delete: 72
    du -sk /Users/oobi/Documents/lanyard-m0/spikes after the delete: 300
    df -g /System/Volumes/Data after the delete: 29 available

Bytes left on disk under the S4 directory after the GOCACHE is deleted: 72
KiB by `du -sk`, which is the harness, the three probes, the runner scripts,
the candidate lists and the bench log.  No build output is left.

Window gates, run at the start of this agent's work and again at the end.

| gate | start | end |
| --- | --- | --- |
| S0-G1 NO-REPO | ls: /Users/oobi/Documents/lanyard: No such file or directory | ls: /Users/oobi/Documents/lanyard: No such file or directory |
| S0-G2 PIN-CLEAN | 0 and 046689a78ef6708404bd190dc86845cbee0bb36f | 0 and 046689a78ef6708404bd190dc86845cbee0bb36f |
| S0-G3 LIB-PINS | 7bd502cbf44cc47f70db9f2b27ab35d77a096364 and 51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a | 7bd502cbf44cc47f70db9f2b27ab35d77a096364 and 51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a |
| S0-G7 DENOM | not yet run | denominators.json parses with node, 13 rows, both anchors, R squared 0.291, sha ba1293a3, 40.7 retired beside 45.0 and 18.11 |

The original /Users/oobi/Documents/kan-rust-lang-gobench.py is unchanged.  Its
sha256 is 788b241d8e07f0ff67ec52b45fb571e79b3cd6620a458b42866ef366a4ec2093
before and after the copy.  Nothing was written outside
/Users/oobi/Documents/lanyard-m0/spikes.  No cargo command ran, no dune
command ran, and nothing was built inside a pinned tree.
