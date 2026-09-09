# SPIKE-SEND, the Send assertion under Arc

Spike S9 of M0-PLAN.md section 2, wave Rustc.  Date: 2026-09-09.

Fact: no probe made this measurement.  Probe 3b failed under `Rc<str>`
and nothing ran the passing shape.  This spike runs the passing shape.

Pass line: the Arc form exits 0 with no diagnostic, printed beside the
probe 3b transcript that exits 1.  RESULT: PASS.

Toolchain: `rustc 1.98.1 (48a229cea 2026-09-01)`, printed by
`rustup run 1.98 rustc --version`.

## 1 The two probe sources

Both files are 17 lines.  Command and output:

```
wc -l /Users/oobi/Documents/lanyard-m0/spikes/s9/send_arc.rs /Users/oobi/Documents/lanyard-m0/spikes/s9/send_rc.rs
      17 /Users/oobi/Documents/lanyard-m0/spikes/s9/send_arc.rs
      17 /Users/oobi/Documents/lanyard-m0/spikes/s9/send_rc.rs
      34 total
```

The two files differ in two lines only, the import and the binder type.
Everything else is byte for byte the same, so the compile result is the
reference kind and nothing else.

### 1.1 The Arc form, /Users/oobi/Documents/lanyard-m0/spikes/s9/send_arc.rs

```rust
use std::future::Future;
use std::sync::Arc;

fn assert_send<F: Future + Send>(_f: F) {}

async fn tick() -> u64 {
    1
}

async fn body() -> Result<u64, ()> {
    let name: Arc<str> = Arc::from("lanyard");
    let n = tick().await;
    let extra = u64::try_from(name.len()).unwrap_or(0);
    Ok(n + extra)
}

fn main() { assert_send(body()); }
```

### 1.2 The Rc form, probe 3b, /Users/oobi/Documents/lanyard-m0/spikes/s9/send_rc.rs

```rust
use std::future::Future;
use std::rc::Rc;

fn assert_send<F: Future + Send>(_f: F) {}

async fn tick() -> u64 {
    1
}

async fn body() -> Result<u64, ()> {
    let name: Rc<str> = Rc::from("lanyard");
    let n = tick().await;
    let extra = u64::try_from(name.len()).unwrap_or(0);
    Ok(n + extra)
}

fn main() { assert_send(body()); }
```

Both files hold the binder across the `.await` at line 12, and both
apply `fn assert_send<F: Future + Send>(_f: F)` to the future at line
17.  That is the shape M0-PLAN.md section 7 names and the shape probe
3b failed.

## 2 The two compile lines, verbatim

```
rustup run 1.98 rustc --edition 2024 --emit=metadata --out-dir /Users/oobi/Documents/lanyard-m0/spikes/s9 /Users/oobi/Documents/lanyard-m0/spikes/s9/send_arc.rs
rustup run 1.98 rustc --edition 2024 --emit=metadata --out-dir /Users/oobi/Documents/lanyard-m0/spikes/s9 /Users/oobi/Documents/lanyard-m0/spikes/s9/send_rc.rs
```

The runner that printed the transcript is
/Users/oobi/Documents/lanyard-m0/spikes/s9/run.sh, run as
`zsh /Users/oobi/Documents/lanyard-m0/spikes/s9/run.sh`.  Nothing past
`--emit=metadata` ran.  No cargo ran, no tokio and no crate.

## 3 The two exit codes

| form | file | exit code | diagnostic |
| --- | --- | --- | --- |
| Arc | send_arc.rs | 0 | none, stdout empty and stderr empty |
| Rc | send_rc.rs | 1 | one error, quoted in section 4 |

Printed transcript:

```
== ARC compile ==
arc exit=0
-- arc stdout --
-- arc stderr --
== RC compile ==
rc exit=1
```

The Arc leg wrote a 0 byte stdout file and a 0 byte stderr file, by
`ls -l` on the spike directory, so the Arc form compiles with no
diagnostic of any kind.  It emitted one metadata file,
`libsend_arc.rmeta`.  The Rc leg aborted, so it emitted no metadata
file.

## 4 The Rc diagnostic, verbatim

```
error: future cannot be sent between threads safely
  --> /Users/oobi/Documents/lanyard-m0/spikes/s9/send_rc.rs:17:25
   |
17 | fn main() { assert_send(body()); }
   |                         ^^^^^^ future returned by `body` is not `Send`
   |
   = help: within `impl Future<Output = Result<u64, ()>>`, the trait `Send` is not implemented for `Rc<str>`
note: future is not `Send` as this value is used across an await
  --> /Users/oobi/Documents/lanyard-m0/spikes/s9/send_rc.rs:12:20
   |
11 |     let name: Rc<str> = Rc::from("lanyard");
   |         ---- has type `Rc<str>` which is not `Send`
12 |     let n = tick().await;
   |                    ^^^^^ await occurs here, with `name` maybe used later
note: required by a bound in `assert_send`
  --> /Users/oobi/Documents/lanyard-m0/spikes/s9/send_rc.rs:4:28
   |
 4 | fn assert_send<F: Future + Send>(_f: F) {}
   |                            ^^^^ required by this bound in `assert_send`

error: aborting due to 1 previous error
```

The Send bound the diagnostic names is `Send` in
`fn assert_send<F: Future + Send>(_f: F)` at send_rc.rs:4:28, quoted by
the third note, "required by a bound in `assert_send`".  The unmet
obligation is `Send` for `Rc<str>` inside
`impl Future<Output = Result<u64, ()>>`, held across the await at
send_rc.rs:12:20.

This transcript reproduces probe 3b on the same toolchain.  The verdict
recorded probe 3b as exit 1 with the same first line and the same help
line, and this run prints them again.

## 5 What the pair shows

The passing shape now exists.  One reference kind changes, and the
`Future + Send` obligation goes from unmet to met.  R-Q7 lowers every
Many binder to `Arc<T>` and a string to `Arc<str>` or `String`, so the
M0 emitted crate carries the helper and one application, and the M1-SEND
leg applies the helper to every route, page, layout and component body.
This spike measures.  It rules nothing, and R-Q7 stays ruled.

## 6 Housekeeping

Load averages, from `uptime` around the measured leg:

```
== uptime before ==
 6:57  27 users, load averages: 28.47 17.44 12.55
== uptime after ==
 6:57  27 users, load averages: 29.87 17.92 12.75
```

Load before 28.47, load after 29.87.  The plan marks a timing spike
NOISY above load average 4, so this window is NOISY.  S9 reports two
exit codes and one diagnostic, not a time, so the load average records
the window and changes no number here.

Build outputs deleted once the exit codes were recorded:
`rm -f /Users/oobi/Documents/lanyard-m0/spikes/s9/*.rmeta` removed
`libsend_arc.rmeta`.  The Rc leg produced no metadata file.  A later
`ls -l` on the directory prints no `.rmeta` file.

Bytes left on disk under /Users/oobi/Documents/lanyard-m0/spikes/s9:
`du -sk` prints 16, so 16 KB, and 0 bytes of that is build output.  The
16 KB is the two 17 line sources, the runner, and four small transcript
files.

```
du -sk /Users/oobi/Documents/lanyard-m0/spikes/s9
16	/Users/oobi/Documents/lanyard-m0/spikes/s9
df -g /System/Volumes/Data
/dev/disk3s5       460  353        29    93% 6686565 309318120    2%   /System/Volumes/Data
```

Gate S0-G12 SEND: PASS.  Both probe sources are here, both
`rustup run 1.98 rustc --edition 2024 --emit=metadata` lines are here,
the Arc form exits 0 with no diagnostic, and the Rc transcript exits 1
with its diagnostic verbatim.
