# M0 mutation log

## Stage 0

Date: 2026-09-09.  The three checks of the Stage 0 brief section 5 ran
from one runner,
/Users/oobi/Documents/lanyard-m0/spikes/mutants/run-mutants.sh, and the
whole transcript is at
/Users/oobi/Documents/lanyard-m0/spikes/mutants/mutants.log.  Every
mutant is a COPY under /Users/oobi/Documents/lanyard-m0/spikes/mutants/.
No stage file was mutated, no file inside
/Users/oobi/Documents/kan-rust-lang-kanon-pin was written and no file
inside /Users/oobi/Documents/topcoat was written.  Each original digest
is reprinted after its check.

`uptime` before the three checks and after them:

```
 7:59  27 users, load averages: 25.33 20.44 19.79
 7:59  27 users, load averages: 25.33 20.44 19.79
```

The three checks are not timing legs, so the load average does not mark
them NOISY.  It is recorded because every measured leg records it.

### S0-M1 anchor, KILLED

The check flips one byte in a copy of the S3 anchor input for site 4,
topcoat-router/src/href.rs, and reruns the S3 fingerprint command on the
copy.

Commands, verbatim:

```
cp /Users/oobi/Documents/lanyard-m0/spikes/s3/site4-topcoat-router-href-full.txt /Users/oobi/Documents/lanyard-m0/spikes/mutants/m1/site4-copy.txt
shasum -a 256 /Users/oobi/Documents/lanyard-m0/spikes/s3/site4-topcoat-router-href-full.txt
python3 -P  (byte 1000 of the copy, exclusive or with 0x01)
shasum -a 256 /Users/oobi/Documents/lanyard-m0/spikes/mutants/m1/site4-copy.txt
shasum -a 256 /Users/oobi/Documents/topcoat/crates/topcoat-router/src/href.rs
```

Printed evidence:

```
bf2347febd67b875c0fff040221ee2ef51af41a35d852a3c60f709cb0ed3527b  /Users/oobi/Documents/lanyard-m0/spikes/s3/site4-topcoat-router-href-full.txt
FLIP offset=1000 old=0x0a new=0x0b
f36b5a76e99452df8f87925814ce3d478ab9f0ec54b20b7545c7c263e65e79fd  /Users/oobi/Documents/lanyard-m0/spikes/mutants/m1/site4-copy.txt
bf2347febd67b875c0fff040221ee2ef51af41a35d852a3c60f709cb0ed3527b  /Users/oobi/Documents/lanyard-m0/spikes/s3/site4-topcoat-router-href-full.txt
bf2347febd67b875c0fff040221ee2ef51af41a35d852a3c60f709cb0ed3527b  /Users/oobi/Documents/topcoat/crates/topcoat-router/src/href.rs
```

Result: KILLED.  The S3 digest for site 4 is
bf2347febd67b875c0fff040221ee2ef51af41a35d852a3c60f709cb0ed3527b and the
mutant prints
f36b5a76e99452df8f87925814ce3d478ab9f0ec54b20b7545c7c263e65e79fd, so the
digest differs.  The byte offset that changed is 1000, from 0x0a to
0x0b.  The original file and the topcoat source both reprint the S3
digest after the flip, so neither moved.

### S0-M2 trusted lines, KILLED

The check copies the pin's dev/trusted-lines.sh with the twelve kernel
files and the one encoder file it reads into a scratch root that keeps
the same relative layout, because the script takes its root from its own
path.  Finding S1-F1 records that the bucket is twelve files and not the
eight the plan text names, so all twelve were copied.  A copy of only
eight would not reproduce the printed 3997.

Commands, verbatim:

```
cp /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/trusted-lines.sh /Users/oobi/Documents/lanyard-m0/spikes/mutants/m2/root/dev/trusted-lines.sh
cp /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/FILE.ml /Users/oobi/Documents/lanyard-m0/spikes/mutants/m2/root/lib/FILE.ml   (shape, term, rules, check, value, eval, conv, totality, positivity, global, order, bignum)
cp /Users/oobi/Documents/kan-rust-lang-kanon-pin/wasm/gc_encode.ml /Users/oobi/Documents/lanyard-m0/spikes/mutants/m2/root/wasm/gc_encode.ml
zsh /Users/oobi/Documents/lanyard-m0/spikes/mutants/m2/root/dev/trusted-lines.sh
(ten lines appended to the shape.ml copy, one per loop turn)
wc -l /Users/oobi/Documents/lanyard-m0/spikes/mutants/m2/root/lib/shape.ml
zsh /Users/oobi/Documents/lanyard-m0/spikes/mutants/m2/root/dev/trusted-lines.sh
shasum -a 256 /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/trusted-lines.sh /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/shape.ml
wc -l /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/shape.ml
```

Printed evidence:

```
-- copy run 1
TRUSTED-LINES kernel=3997/4000 encoder=246/600 OK
exit=0
-- append exactly ten lines to the shape.ml copy
      70 /Users/oobi/Documents/lanyard-m0/spikes/mutants/m2/root/lib/shape.ml
-- copy run 2
TRUSTED-LINES kernel=4007/4000 encoder=246/600 FAIL
exit=1
451b5fab5965ea62027239ab581074c6111cef38eb1754c8b32c29e0996e3b46  /Users/oobi/Documents/kan-rust-lang-kanon-pin/dev/trusted-lines.sh
dafd7741b4332dcab6faba9cb9afb131fb3654172e0d375b1edd1046e69f7f7b  /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/shape.ml
      60 /Users/oobi/Documents/kan-rust-lang-kanon-pin/lib/shape.ml
```

Result: KILLED.  The copy read 3997 before the append and 4007 after it,
so the rise is 4007 minus 3997, which is exactly ten.  The shape.ml copy
went from 60 lines to 70 lines, which is the same ten.  A rise of any
other size would be a blocker, because it would mean the bucket does not
read what the copy holds;  the rise is exactly ten, so no blocker fired.
The copy also crossed the 4000 bound, so run 2 printed FAIL and exited
1, which is the script working as written.  The pin file shape.ml still
prints 60 lines and both pin digests are reprinted above, so the pin did
not move.

### S0-M3 send, KILLED

The check copies the S9 probe into the mutants directory, puts `Rc<str>`
back in place of `Arc<str>`, and compiles the copy with the same rustc
line the S9 Arc form used.

Commands, verbatim:

```
cp /Users/oobi/Documents/lanyard-m0/spikes/s9/send_arc.rs /Users/oobi/Documents/lanyard-m0/spikes/mutants/m3/send_arc.rs
python3 -P  (std::sync::Arc to std::rc::Rc, Arc<str> to Rc<str>, Arc::from to Rc::from)
rustup run 1.98 rustc --edition 2024 --emit=metadata -o /Users/oobi/Documents/lanyard-m0/spikes/mutants/m3/arc.rmeta /Users/oobi/Documents/lanyard-m0/spikes/mutants/m3/send_arc.rs
rustup run 1.98 rustc --edition 2024 --emit=metadata -o /Users/oobi/Documents/lanyard-m0/spikes/mutants/m3/mutant.rmeta /Users/oobi/Documents/lanyard-m0/spikes/mutants/m3/send_arc_mutant.rs
rm -f /Users/oobi/Documents/lanyard-m0/spikes/mutants/m3/arc.rmeta /Users/oobi/Documents/lanyard-m0/spikes/mutants/m3/mutant.rmeta
```

Printed evidence:

```
MUTANT written, Arc occurrences left=0
arc exit=0
       0 /Users/oobi/Documents/lanyard-m0/spikes/mutants/m3/arc.err
mutant exit=1
error: future cannot be sent between threads safely
  --> /Users/oobi/Documents/lanyard-m0/spikes/mutants/m3/send_arc_mutant.rs:17:25
   |
17 | fn main() { assert_send(body()); }
   |                         ^^^^^^ future returned by `body` is not `Send`
   |
   = help: within `impl Future<Output = Result<u64, ()>>`, the trait `Send` is not implemented for `Rc<str>`
note: future is not `Send` as this value is used across an await
  --> /Users/oobi/Documents/lanyard-m0/spikes/mutants/m3/send_arc_mutant.rs:12:20
   |
11 |     let name: Rc<str> = Rc::from("lanyard");
   |         ---- has type `Rc<str>` which is not `Send`
12 |     let n = tick().await;
   |                    ^^^^^ await occurs here, with `name` maybe used later
note: required by a bound in `assert_send`
  --> /Users/oobi/Documents/lanyard-m0/spikes/mutants/m3/send_arc_mutant.rs:4:28
   |
 4 | fn assert_send<F: Future + Send>(_f: F) {}
   |                            ^^^^ required by this bound in `assert_send`

error: aborting due to 1 previous error
```

Result: KILLED.  The Arc copy exits 0 with an empty stderr, 0 bytes by
`wc -c`.  The Rc copy exits 1 on the Send bound with the diagnostic
above.  Both exit codes are printed.  The two metadata outputs were
deleted once the exit codes were recorded, so no build output stayed on
disk.

### Summary

Three checks ran and three mutants were KILLED.  No mutant survived, so
no blocker fired from section 5.  Bytes left under
/Users/oobi/Documents/lanyard-m0/spikes/mutants after the deletes: 276
KiB by `du -sk`, which is the twelve kernel copies, the encoder copy,
the script copy, the anchor copy, the two probes, the two runner scripts
and the transcript.  No build output above 50 MB is anywhere under
/Users/oobi/Documents/lanyard-m0.

## Stage A (2026-09-09)

The three checks of the Stage A brief section 6 ran from
/Users/oobi/Documents/lanyard-m0/fix2/part-a.sh on a COPY of the tree at
/Users/oobi/Documents/lanyard-m0/stage-a-mutants/sa-tree, removed after the
run.  No repository file was mutated.  The original digests are reprinted
after the three checks.  Transcript: /Users/oobi/Documents/lanyard-m0/sa-fix-a.log.

### SA-M1 kernel, KILLED

Command: cp -R of the tree, then one line appended to lib/check.ml of the
copy, then zsh COPY/dev/kernel-carry.sh.
Evidence: exit 1;  KERNEL-CARRY lib/check.ml 046689a VERBATIM diff=2 lines=539 FAIL bytes-differ;  KERNEL-CARRY FAIL

### SA-M2 census, KILLED

Command: in the copy, sd 'formers 2:' 'formers 3:' SPEC.md, then
zsh COPY/dev/r0-count.sh.
Evidence: exit 1;  2:< formers 3: Lan Ran 4:> formers 2: Lan Ran;  R0-COUNT FAIL

### SA-M3 carry, KILLED

Command: cp of spikes/dev/SPIKE-TRUSTED.md to stage-a-mutants/, byte 100 of
the copy xor 1 with python3 -P, then shasum -a 256 on both sides.
Evidence: source bebfabdfe63325da3e8458e41f1eb8c8e4acf95867ff43726a312bd9b33dc86c copy 0b702b61c855b7f8c9fffc341548ff28f9c5a186cb384c77cdac0d978053d5b8 UNEQUAL KILLED

Originals after the checks (sha256): originals: check.ml cdc3712bf5ed0fa49d8dae34ea946d85a195ea94b25235c821b155570010e335 SPEC.md 9b5f4ed7accb5617d678390bb6845a2c7ba4720e8e5521977ccacde922d390aa dev/spikes/SPIKE-TRUSTED.md bebfabdfe63325da3e8458e41f1eb8c8e4acf95867ff43726a312bd9b33dc86c

Three checks ran and three mutants were KILLED.  No mutant survived.

### Judge rerun (2026-09-09)

The judge reran the three checks from
/Users/oobi/Documents/lanyard-m0/judge/sa-judge-run.sh on a fresh COPY of the
tree at /Users/oobi/Documents/lanyard-m0/stage-a-mutants/sa-tree, removed
after the run, and on the file copy
/Users/oobi/Documents/lanyard-m0/stage-a-mutants/sa-m3-judge-trusted-copy.md.
No repository file was mutated.  Transcript:
/Users/oobi/Documents/lanyard-m0/judge/gates.log.

- SA-M1 KILLED.  Line one of lib/check.ml replaced in the copy (538 lines,
  diff 2 lines), then zsh COPY/dev/kernel-carry.sh printed `KERNEL-CARRY
  lib/check.ml 046689a VERBATIM diff=4 lines=538 FAIL bytes-differ` and
  `KERNEL-CARRY FAIL`, exit 1.
- SA-M2 KILLED.  `sd 'formers 2:' 'formers 3:' < SPEC.md > COPY/SPEC.md`,
  then zsh COPY/dev/r0-count.sh printed `1c1`, `< formers 3: Lan Ran`,
  `> formers 2: Lan Ran` and `R0-COUNT FAIL`, exit 1.
- SA-M3 KILLED.  Byte 100 of the copy xor 1 with python3 -P, then sha256 on
  both sides:  source
  bebfabdfe63325da3e8458e41f1eb8c8e4acf95867ff43726a312bd9b33dc86c, copy
  0b702b61c855b7f8c9fffc341548ff28f9c5a186cb384c77cdac0d978053d5b8,
  UNEQUAL, so the SA-G7 comparison fails.

Originals after the judge run (sha256):  lib/check.ml
cdc3712bf5ed0fa49d8dae34ea946d85a195ea94b25235c821b155570010e335;  SPEC.md
9b5f4ed7accb5617d678390bb6845a2c7ba4720e8e5521977ccacde922d390aa;
dev/spikes/SPIKE-TRUSTED.md
bebfabdfe63325da3e8458e41f1eb8c8e4acf95867ff43726a312bd9b33dc86c, equal to
the source.  `git diff --stat 046689a -- lib/check.ml SPEC.md` printed
nothing.  Three mutants KILLED, none survived.
