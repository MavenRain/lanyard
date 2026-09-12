"""Byte-exact model emission and compiled ownership/range/suspension controls."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "_build/default/bin/lanyard.exe"


def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, text=True,
                          capture_output=True, timeout=120)


def require(condition, message):
    if not condition:
        print(f"LAN-MODELS FAIL: {message}", file=sys.stderr)
        sys.exit(1)


# The local derive registers #[key] only. The separate pinned probe exercises
# the real derive, query generation and storage against in-memory SQLite.
DERIVE = '''extern crate proc_macro;
#[proc_macro_derive(Model, attributes(key))]
pub fn model(_input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    proc_macro::TokenStream::new()
}
'''
DOUBLE = r'''
#[macro_export]
macro_rules! create {
    ($model:ident { $($field:ident: $value:expr),* }) => {
        toasty::Pending::new($model { $($field: $value),* })
    };
}
mod toasty {
    pub use model_derive::Model;
    pub use crate::create;
    use std::sync::{Arc, atomic::{AtomicUsize, Ordering}};
    #[derive(Clone, Copy)]
    pub enum Mode { Pass, Fail, Negative }
    #[derive(Clone)]
    pub struct Db { calls: Arc<AtomicUsize>, mode: Mode }
    impl Db {
        pub fn new(mode: Mode) -> Self { Self { calls: Arc::new(AtomicUsize::new(0)), mode } }
        pub fn count(&self) -> usize { self.calls.load(Ordering::SeqCst) }
        pub fn value(&self, value: i64) -> i64 {
            match self.mode { Mode::Pass | Mode::Fail => value, Mode::Negative => -1 }
        }
        pub async fn step(&mut self) -> Result<(), Error> {
            enum Step { Start, Finish }
            let mut step = Step::Start;
            std::future::poll_fn(move |cx| match step {
                Step::Start => { step = Step::Finish; cx.waker().wake_by_ref(); std::task::Poll::Pending }
                Step::Finish => std::task::Poll::Ready(()),
            }).await;
            self.calls.fetch_add(1, Ordering::SeqCst);
            match self.mode { Mode::Pass | Mode::Negative => Ok(()), Mode::Fail => Err(Error) }
        }
    }
    #[derive(Debug)]
    pub struct Error;
    impl std::fmt::Display for Error {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result { f.write_str("database failed") }
    }
    impl std::error::Error for Error {}
    pub struct Pending<T>(T);
    impl<T> Pending<T> {
        pub fn new(value: T) -> Self { Self(value) }
        pub async fn exec(self, db: &mut Db) -> Result<T, Error> { db.step().await?; Ok(self.0) }
    }
}
impl LanModel436f756e746572 {
    async fn get_by_id(db: &mut toasty::Db, id: &i64) -> Result<Self, toasty::Error> {
        db.step().await?; Ok(Self { id: *id, f_76616c7565: db.value(42) })
    }
}
impl LanModel53696e676c65 {
    async fn get_by_id(db: &mut toasty::Db, id: &i64) -> Result<Self, toasty::Error> {
        db.step().await?; Ok(Self { id: *id, f_76616c7565: db.value(99) })
    }
}
struct Wake;
impl std::task::Wake for Wake { fn wake(self: Arc<Self>) {} }
fn execute<F: std::future::Future + Send>(future: F) -> Result<F::Output, Error> {
    let mut future = std::pin::pin!(future);
    let waker = std::task::Waker::from(Arc::new(Wake));
    let mut cx = std::task::Context::from_waker(&waker);
    match future.as_mut().poll(&mut cx) {
        std::task::Poll::Ready(value) => Ok(value),
        std::task::Poll::Pending => match future.as_mut().poll(&mut cx) {
            std::task::Poll::Ready(value) => Ok(value),
            std::task::Poll::Pending => Err(Error::Arithmetic),
        },
    }
}
fn report(name: &str, passed: bool) -> Result<(), Error> {
    if passed { println!("{name} OK"); Ok(()) } else { Err(Error::Arithmetic) }
}
fn main() -> Result<(), Error> {
    report("zero", lan_model_to_i64(&lan_model_from_i64(0)?)? == 0)?;
    report("maximum", lan_model_to_i64(&lan_model_from_i64(i64::MAX)?)? == i64::MAX)?;
    report("overflow", matches!(lan_model_to_i64(&Nat::decimal("9223372036854775808")?), Err(Error::ModelRange)))?;
    report("negative", matches!(lan_model_from_i64(-1), Err(Error::ModelRange)))?;
    let db = Arc::new(toasty::Db::new(toasty::Mode::Pass));
    let future = f_637265617465(Arc::clone(&db));
    report("lazy", db.count() == 0)?;
    let row = execute(future)??;
    report("create", lan_model_to_i64(&row.f0)? == 7 && lan_model_to_i64(&row.f1)? == 42)?;
    report("once", db.count() == 1)?;
    let row = execute(f_6c6f6f6b7570(Arc::new(Nat::decimal("8")?), Arc::clone(&db)))??;
    report("lookup", lan_model_to_i64(&row.f0)? == 8 && lan_model_to_i64(&row.f1)? == 42)?;
    let row = Arc::new(T70726f64756374286e61742c6e617429 { f0: Nat::decimal("99")?, f1: Nat::decimal("10")? });
    let made = execute(f_63726561746553696e676c65(Arc::clone(&row), Arc::clone(&db)))??;
    report("field-order", lan_model_to_i64(&made.f0)? == 99 && lan_model_to_i64(&made.f1)? == 10)?;
    report("shared", Arc::strong_count(&row) == 1 && Arc::strong_count(&db) == 1)?;
    let fail = Arc::new(toasty::Db::new(toasty::Mode::Fail));
    report("error", matches!(execute(f_637265617465(fail))?, Err(Error::Database(_))))?;
    let negative = Arc::new(toasty::Db::new(toasty::Mode::Negative));
    report("negative-field", matches!(execute(f_6c6f6f6b757053696e676c65(Arc::new(Nat::decimal("10")?), negative))?, Err(Error::ModelRange)))?;
    let before = db.count();
    report("key-overflow", matches!(execute(f_6c6f6f6b7570(Arc::new(Nat::decimal("9223372036854775808")?), Arc::clone(&db)))?, Err(Error::ModelRange)))?;
    report("no-effect", db.count() == before)?;
    Ok(())
}
'''


def main():
    emitted = run(CLI, "emit", "--target", "test/fixtures/models.lan")
    require(emitted.returncode == 0 and not emitted.stderr, emitted.stderr)
    require(emitted.stdout.encode() == (ROOT / "test/goldens/models.rs").read_bytes(), "golden differs")
    forbidden = (r"\b(?:unsafe|loop|while|as)\b|\b(?:unwrap|expect)\s*\("
                 r"|\b(?:panic|assert|assert_eq|debug_assert|unreachable|todo)\w*\s*!"
                 r"|\bfor\s+\w+\s+in\b")
    require(re.search(forbidden, emitted.stdout) is None, "forbidden generated Rust")
    native = run(CLI, "emit", "--native", "test/fixtures/models.lan")
    native_refusals = 0
    require(native.returncode == 1 and not native.stdout and "foreign type Db" in native.stderr,
            "native model call did not refuse")
    # The native arm erases model declarations and applies no model rule.
    require(not re.search(r"model (?:field|schema|requires|metadata|argument)", native.stderr),
            "native refusal named a model rule")
    native_refusals += 1
    version = run("rustup", "run", "1.98", "rustc", "--version")
    require(version.returncode == 0 and version.stdout.startswith("rustc 1.98.1 "), "pinned rustc missing")
    expected = [f"{name} OK" for name in (
        "zero", "maximum", "overflow", "negative", "lazy", "create", "once", "lookup",
        "field-order", "shared", "error", "negative-field", "key-overflow", "no-effect")]
    with tempfile.TemporaryDirectory(prefix="lanyard-models-") as work:
        work = Path(work)
        derive = work / "derive.rs"
        derive.write_text(DERIVE)
        library = work / "libmodel_derive.dylib" if sys.platform == "darwin" else work / "libmodel_derive.so"
        built = run("rustup", "run", "1.98", "rustc", "--crate-name", "model_derive",
                    "--crate-type", "proc-macro", derive, "-o", library)
        require(built.returncode == 0, built.stderr)

        def compile_source(source):
            rust = work / "main.rs"
            binary = work / "models"
            rust.write_text(source + DOUBLE)
            compiled = run("rustup", "run", "1.98", "rustc", "--edition=2024", "--extern",
                           f"model_derive={library}", rust, "-o", binary)
            return compiled, binary

        compiled, binary = compile_source(emitted.stdout)
        require(compiled.returncode == 0, compiled.stderr)
        executed = run(binary)
        require(executed.returncode == 0 and executed.stdout.splitlines() == expected,
                executed.stderr or executed.stdout)
        mutations = [
            ("negative guard", "if value < 0", "if value < i64::MIN"),
            ("overflow guard", "number.checked_mul(256).and_then(|number| number.checked_add(i64::from(*byte)))",
             "Some(number.wrapping_mul(256).wrapping_add(i64::from(*byte)))"),
            ("result field", "lan_model_from_i64(__lan_row.id)", "lan_model_from_i64(__lan_row.f_76616c7565)"),
            ("missing await", ".exec(&mut __lan_db).await?", ".exec(&mut __lan_db)?"),
        ]
        killed = 0
        for name, before, after in mutations:
            require(before in emitted.stdout, f"mutation target missing: {name}")
            compiled, binary = compile_source(emitted.stdout.replace(before, after))
            if name == "missing await":
                unpolled = "the `?` operator can only be applied to values that implement `Try`"
                require(compiled.returncode != 0 and unpolled in compiled.stderr,
                        f"mutation survived: {name}")
            else:
                require(compiled.returncode == 0, compiled.stderr)
                executed = run(binary)
                require(executed.returncode != 0, f"mutation survived: {name}")
            killed += 1
    print(f"LAN-MODELS OK observations={len(expected)} mutants={killed} native-refusals={native_refusals} compiler={version.stdout.strip()}")


if __name__ == "__main__":
    main()
