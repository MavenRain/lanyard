# SPIKE-ANCHOR

Spike S3, the anchor fingerprint, wave Counts.  Date: 2026-09-09.

Fact 3 of M0-PLAN.md section 12: the href anchor path.  The path half
already held before this spike, because attack 1 A7 corrected P2's
grammar/src href path to topcoat-router/src/href.rs.  This spike
reprints the path and closes the hash half.  It hashes the four anchor
sites of M0-PLAN.md section 5, one sha256 per site.

The anchor is re-derived before it is hashed, so each span is extracted
into the S3 scratch directory with `awk` first and the sha256 is taken
over the extracted file, never over the source file in place.

Nothing was written inside /Users/oobi/Documents/topcoat.  The tree was
read only for the whole of this spike.  The byte flip is mutation S0-M1
and it belongs to the judge, so this spike did not run it.

## 1 Pin

topcoat HEAD is 51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a.

Command:

```
git -C /Users/oobi/Documents/topcoat rev-parse HEAD
```

Printed:

```
51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a
```

The toasty pin was printed in the same gate leg.

Command:

```
git -C /Users/oobi/Documents/toasty rev-parse HEAD
```

Printed:

```
7bd502cbf44cc47f70db9f2b27ab35d77a096364
```

## 2 The anchor path

Command:

```
fd -g 'href*.rs' /Users/oobi/Documents/topcoat/crates
```

Printed:

```
/Users/oobi/Documents/topcoat/crates/topcoat-router/src/href.rs
```

One path printed.  The path half of fact 3 holds and attack 1 A7 is
right.

## 3 The four anchor sites

Every path below is under /Users/oobi/Documents/topcoat/crates/.  The
plan writes the two grammar sites as grammar/src/component/attr.rs and
grammar/src/component/item.rs.  Both resolve inside the topcoat-view
crate, and `fd` printed the full paths.

| site | path | span | source lines |
| --- | --- | --- | --- |
| 1 | topcoat-view/macro/src/lib.rs | 27-34 | 43 |
| 2 | topcoat-view/grammar/src/component/attr.rs | 6-15 | 69 |
| 3 | topcoat-view/grammar/src/component/item.rs | 21-64 | 109 |
| 4 | topcoat-router/src/href.rs | whole file, 1-1149 | 1149 |

Command that printed the source line counts:

```
wc -l /Users/oobi/Documents/topcoat/crates/topcoat-view/macro/src/lib.rs
wc -l /Users/oobi/Documents/topcoat/crates/topcoat-view/grammar/src/component/attr.rs
wc -l /Users/oobi/Documents/topcoat/crates/topcoat-view/grammar/src/component/item.rs
wc -l /Users/oobi/Documents/topcoat/crates/topcoat-router/src/href.rs
```

Printed:

```
      43 /Users/oobi/Documents/topcoat/crates/topcoat-view/macro/src/lib.rs
      69 /Users/oobi/Documents/topcoat/crates/topcoat-view/grammar/src/component/attr.rs
     109 /Users/oobi/Documents/topcoat/crates/topcoat-view/grammar/src/component/item.rs
    1149 /Users/oobi/Documents/topcoat/crates/topcoat-router/src/href.rs
```

M0-PLAN.md line 426 calls item.rs a 109-line file.  The count prints
109, so that citation holds.  The brief section 2 gives href.rs as
36,873 bytes and `wc -c` over the extracted whole-file copy prints
36873, so that citation holds as well.

## 4 Extraction commands

One command per site.  Each writes one file under
/Users/oobi/Documents/lanyard-m0/spikes/s3/.

Site 1:

```
awk 'NR>=27 && NR<=34' /Users/oobi/Documents/topcoat/crates/topcoat-view/macro/src/lib.rs > /Users/oobi/Documents/lanyard-m0/spikes/s3/site1-topcoat-view-macro-lib-27-34.txt
```

Site 2:

```
awk 'NR>=6 && NR<=15' /Users/oobi/Documents/topcoat/crates/topcoat-view/grammar/src/component/attr.rs > /Users/oobi/Documents/lanyard-m0/spikes/s3/site2-component-attr-6-15.txt
```

Site 3:

```
awk 'NR>=21 && NR<=64' /Users/oobi/Documents/topcoat/crates/topcoat-view/grammar/src/component/item.rs > /Users/oobi/Documents/lanyard-m0/spikes/s3/site3-component-item-21-64.txt
```

Site 4, the whole file:

```
awk 'NR>=1' /Users/oobi/Documents/topcoat/crates/topcoat-router/src/href.rs > /Users/oobi/Documents/lanyard-m0/spikes/s3/site4-topcoat-router-href-full.txt
```

Extracted sizes.  Command:

```
wc -l -c /Users/oobi/Documents/lanyard-m0/spikes/s3/site1-topcoat-view-macro-lib-27-34.txt /Users/oobi/Documents/lanyard-m0/spikes/s3/site2-component-attr-6-15.txt /Users/oobi/Documents/lanyard-m0/spikes/s3/site3-component-item-21-64.txt /Users/oobi/Documents/lanyard-m0/spikes/s3/site4-topcoat-router-href-full.txt
```

Printed:

```
       8     340 site1-topcoat-view-macro-lib-27-34.txt
      10     380 site2-component-attr-6-15.txt
      44    1665 site3-component-item-21-64.txt
    1149   36873 site4-topcoat-router-href-full.txt
    1211   39258 total
```

The line counts 8, 10, 44 and 1149 are the spans the plan names, so
every extraction took the whole span and no more.

## 5 The four sha256 values

Command:

```
shasum -a 256 /Users/oobi/Documents/lanyard-m0/spikes/s3/site1-topcoat-view-macro-lib-27-34.txt
shasum -a 256 /Users/oobi/Documents/lanyard-m0/spikes/s3/site2-component-attr-6-15.txt
shasum -a 256 /Users/oobi/Documents/lanyard-m0/spikes/s3/site3-component-item-21-64.txt
shasum -a 256 /Users/oobi/Documents/lanyard-m0/spikes/s3/site4-topcoat-router-href-full.txt
```

Printed:

```
314e1e3d815d7b03a30f06e0c882797f42a73f25318dd945287e9da5e8150465  /Users/oobi/Documents/lanyard-m0/spikes/s3/site1-topcoat-view-macro-lib-27-34.txt
8153ebe800d72c3d3cbd9990417bf8136e20055d71c1d42d593707ef9a7f9e4d  /Users/oobi/Documents/lanyard-m0/spikes/s3/site2-component-attr-6-15.txt
160a7d3ae57ce2a0fbd79ce2d3d8782245ae54ecf7be42503fb3eeacbf070337  /Users/oobi/Documents/lanyard-m0/spikes/s3/site3-component-item-21-64.txt
bf2347febd67b875c0fff040221ee2ef51af41a35d852a3c60f709cb0ed3527b  /Users/oobi/Documents/lanyard-m0/spikes/s3/site4-topcoat-router-href-full.txt
```

Site fingerprints, one line per site, for the target/topcoat-51caa01.sig
ANCHOR leg to carry:

| site | path and span | sha256 |
| --- | --- | --- |
| 1 | topcoat-view/macro/src/lib.rs:27-34 | 314e1e3d815d7b03a30f06e0c882797f42a73f25318dd945287e9da5e8150465 |
| 2 | topcoat-view/grammar/src/component/attr.rs:6-15 | 8153ebe800d72c3d3cbd9990417bf8136e20055d71c1d42d593707ef9a7f9e4d |
| 3 | topcoat-view/grammar/src/component/item.rs:21-64 | 160a7d3ae57ce2a0fbd79ce2d3d8782245ae54ecf7be42503fb3eeacbf070337 |
| 4 | topcoat-router/src/href.rs, whole file | bf2347febd67b875c0fff040221ee2ef51af41a35d852a3c60f709cb0ed3527b |

Pass line: the anchor path printed, and four sha256 values printed, one
per site.  Both halves printed.

## 6 Span content check

The plan names what each span must hold.  Each extracted span was
printed and read.  No span disagrees with the plan, so this spike
records no finding and repairs nothing.

Site 1, the `#[component]` entry.  The span holds the
`#[proc_macro_attribute]` line and the whole `pub fn component` body,
which calls `topcoat_view_grammar::component::Component::parse`.  The
span opens at the `#[doc = include_str!(..)]` line and closes at the
function's own closing brace, so it is a whole item.

Site 2, `ComponentAttr` and the `boxed` keyword.  The span holds
`custom_keyword!(boxed);`, the closing brace of the `kw` module, the
doc comment for the attribute, and the whole `pub struct ComponentAttr`
with its one field `boxed: Option<kw::boxed>`.

Site 3, the parse that rejects a non-async fn.  The span opens at
`impl Parse for ComponentItem`, holds `let item: ItemFn = input.parse()?;`
and the test `if item.sig.asyncness.is_none()`, and closes at the
`Ok(Self { item })` return with its two closing braces.  The word
`async` appears in the span, by `rg -n -c 'async'` printing 2.

Site 4, the href correction of attack 1 A7.  The span is the whole file
and it opens with the `use std::{ borrow::Cow, fmt::{self, Display,
Write}, ..` prelude.

## 7 Host

Load average before the measured leg:

```
uptime
 6:48  27 users, load averages: 15.64 10.25 8.44
```

Load average after the measured leg:

```
uptime
 6:49  27 users, load averages: 15.86 11.23 8.91
```

The load average is above 4, so a timing spike is NOISY today.  S3 is a
Counts spike and it prints no timing number, so NOISY does not change
any number here.  Both load averages are recorded because the stage
rule asks for them on every leg.

## 8 Bytes left on disk

Command:

```
du -sk /Users/oobi/Documents/lanyard-m0/spikes/s3
```

Printed:

```
52	/Users/oobi/Documents/lanyard-m0/spikes/s3
```

52 KiB left under the S3 scratch directory.  The four extracted spans
are the hashed inputs, so they stay as the evidence behind the four
sha256 values.  S3 ran no build, so it left no build output, no rustc
binary and no metadata file.

## 9 Gates

S0-G1 NO-REPO, start of the S3 window:

```
ls -d /Users/oobi/Documents/lanyard
ls: /Users/oobi/Documents/lanyard: No such file or directory
```

S0-G2 PIN-CLEAN, start of the S3 window:

```
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin status --porcelain | wc -l
       0
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin rev-parse HEAD
046689a78ef6708404bd190dc86845cbee0bb36f
```

S0-G3 LIB-PINS, start of the S3 window:

```
git -C /Users/oobi/Documents/toasty rev-parse HEAD
7bd502cbf44cc47f70db9f2b27ab35d77a096364
git -C /Users/oobi/Documents/topcoat rev-parse HEAD
51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a
```

S0-G6 ANCHOR is this file: the anchor path from `fd` in section 2, the
four sha256 values in section 5, and the extraction command that
produced each hashed input in section 4.

The end-of-window reprint of S0-G1, S0-G2 and S0-G3 is in section 10.

## 10 End of window

S0-G1 NO-REPO, end of the S3 window:

```
ls -d /Users/oobi/Documents/lanyard
ls: /Users/oobi/Documents/lanyard: No such file or directory
```

S0-G2 PIN-CLEAN, end of the S3 window:

```
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin status --porcelain | wc -l
       0
git -C /Users/oobi/Documents/kan-rust-lang-kanon-pin rev-parse HEAD
046689a78ef6708404bd190dc86845cbee0bb36f
```

S0-G3 LIB-PINS, end of the S3 window:

```
git -C /Users/oobi/Documents/toasty rev-parse HEAD
7bd502cbf44cc47f70db9f2b27ab35d77a096364
git -C /Users/oobi/Documents/topcoat rev-parse HEAD
51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a
```

The four end-of-window lines are printed above and they equal the four
start-of-window lines.

Blocker S0-B6 FIRED during this window.  `df -g /System/Volumes/Data`
printed 28 GiB available, which is under the 29 GiB the blocker names.
The number is reported and nothing was deleted.  S3 added 52 KiB and it
ran no build, so it is not the cause.
