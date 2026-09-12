"""Byte-exact model emission and compiled scalar/ownership/range controls."""
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
impl LanModel466c6167 {
    async fn get_by_id(db: &mut toasty::Db, id: &i64) -> Result<Self, toasty::Error> {
        db.step().await?;
        Ok(Self { f_656e61626c6564: *id == 31, id: *id,
            f_636f756e74: db.value(*id - 30), f_6172636869766564: *id == 30 })
    }
}
impl LanModel546f646f {
    async fn get_by_id(db: &mut toasty::Db, id: &i64) -> Result<Self, toasty::Error> {
        db.step().await?;
        Ok(Self { f_7469746c65: String::from(if *id == 41 { "héllo🦀\0" } else { "hello" }),
            id: *id, f_636f6d706c65746564: *id == 41,
            f_6e6f7465: String::from(if *id == 41 { "other" } else { "note" }) })
    }
}
fn is_true(value: &T73756d28756e69742c756e697429) -> bool {
    match value {
        T73756d28756e69742c756e697429::V0(()) => false,
        T73756d28756e69742c756e697429::V1(()) => true,
    }
}
fn nat(number: &str) -> Result<Arc<Nat>, Error> { Nat::decimal(number).map(Arc::new) }
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
    let true_row = Arc::new(f_666c6167(nat("31")?, nat("1")?)?);
    let false_row = f_666c6167(nat("30")?, nat("0")?)?;
    report("bool-source-true", is_true(&true_row.f0) && !is_true(&true_row.f3))?;
    report("bool-source-false", !is_true(&false_row.f0) && is_true(&false_row.f3))?;
    let before = db.count();
    let future = f_637265617465466c6167(Arc::clone(&true_row), Arc::clone(&db));
    report("bool-lazy", db.count() == before)?;
    let made = execute(future)??;
    report("bool-create-true", is_true(&made.f0) && !is_true(&made.f3)
        && lan_model_to_i64(&made.f1)? == 31 && lan_model_to_i64(&made.f2)? == 1)?;
    report("bool-once", db.count() == before + 1)?;
    let made = execute(f_637265617465466c616756616c7565(nat("30")?, nat("0")?, Arc::clone(&db)))??;
    report("bool-create-false", !is_true(&made.f0) && is_true(&made.f3)
        && lan_model_to_i64(&made.f1)? == 30 && lan_model_to_i64(&made.f2)? == 0)?;
    let found = execute(f_6c6f6f6b7570466c6167(nat("31")?, Arc::clone(&db)))??;
    report("bool-lookup-true", is_true(&found.f0) && !is_true(&found.f3)
        && lan_model_to_i64(&found.f1)? == 31 && lan_model_to_i64(&found.f2)? == 1)?;
    let found = execute(f_6c6f6f6b7570466c6167(nat("30")?, Arc::clone(&db)))??;
    report("bool-lookup-false", !is_true(&found.f0) && is_true(&found.f3)
        && lan_model_to_i64(&found.f1)? == 30 && lan_model_to_i64(&found.f2)? == 0)?;
    report("bool-shared", Arc::strong_count(&true_row) == 1 && Arc::strong_count(&db) == 1)?;
    let fail = Arc::new(toasty::Db::new(toasty::Mode::Fail));
    report("bool-error", matches!(execute(f_637265617465466c6167(Arc::clone(&true_row), fail))?, Err(Error::Database(_))))?;
    let negative = Arc::new(toasty::Db::new(toasty::Mode::Negative));
    report("bool-negative-field", matches!(execute(f_6c6f6f6b7570466c6167(nat("31")?, negative))?, Err(Error::ModelRange)))?;
    let before = db.count();
    report("bool-overflow", matches!(execute(f_637265617465466c616756616c7565(nat("32")?, nat("9223372036854775808")?, Arc::clone(&db)))?, Err(Error::ModelRange)))?;
    report("bool-key-overflow", matches!(execute(f_6c6f6f6b7570466c6167(nat("9223372036854775808")?, Arc::clone(&db)))?, Err(Error::ModelRange)))?;
    report("bool-no-effect", db.count() == before)?;
    report("text-empty", lan_model_text_to_4279746573(&Bytes::V0)?.is_empty()
        && text_is(&lan_model_text_from_4279746573(String::new()), ""))?;
    let title = text_input("héllo🦀\0");
    report("text-utf8", lan_model_text_to_4279746573(&title)? == "héllo🦀\0"
        && text_is(&lan_model_text_from_4279746573(String::from("héllo🦀\0")), "héllo🦀\0"))?;
    report("text-byte-range", matches!(lan_model_text_to_4279746573(byte_input(&[256])?.as_ref()), Err(Error::ModelByteRange)))?;
    let huge = Bytes::V1(Box::new((Nat::decimal("340282366920938463463374607431768211455")?, Bytes::V0)));
    report("text-large-byte", matches!(lan_model_text_to_4279746573(&huge), Err(Error::ModelByteRange)))?;
    let invalid: &[&[u16]] = &[&[255], &[192, 175], &[195], &[237, 160, 128], &[244, 144, 128, 128]];
    let refused = invalid.iter().try_fold(true, |passed, bytes| {
        byte_input(bytes).map(|value| passed && matches!(lan_model_text_to_4279746573(&value), Err(Error::ModelUtf8)))
    })?;
    report("text-invalid-utf8", refused)?;
    report("text-errors", Error::ModelByteRange.to_string().contains("255")
        && Error::ModelUtf8.to_string().contains("UTF-8")
        && std::error::Error::source(&Error::ModelUtf8).is_none())?;
    let row = Arc::new(f_746f646f(nat("41")?, Arc::clone(&title), text_input("other"))?);
    let before = db.count();
    let future = f_637265617465546f646f(Arc::clone(&row), Arc::clone(&db));
    report("text-lazy", db.count() == before)?;
    let made = execute(future)??;
    report("text-create", text_is(&made.f0, "héllo🦀\0") && lan_model_to_i64(&made.f1)? == 41
        && is_true(&made.f2) && text_is(&made.f3, "other"))?;
    report("text-once", db.count() == before + 1)?;
    let made = execute(f_637265617465546f646f56616c7565(nat("40")?, Arc::clone(&db)))??;
    report("text-create-value", text_is(&made.f0, "hello") && lan_model_to_i64(&made.f1)? == 40
        && !is_true(&made.f2) && text_is(&made.f3, "note"))?;
    let found = execute(f_6c6f6f6b7570546f646f(nat("41")?, Arc::clone(&db)))??;
    report("text-lookup", text_is(&found.f0, "héllo🦀\0") && lan_model_to_i64(&found.f1)? == 41
        && is_true(&found.f2) && text_is(&found.f3, "other"))?;
    report("text-shared", Arc::strong_count(&row) == 1 && Arc::strong_count(&title) == 1)?;
    let fail = Arc::new(toasty::Db::new(toasty::Mode::Fail));
    report("text-error", matches!(execute(f_637265617465546f646f(Arc::clone(&row), fail))?, Err(Error::Database(_))))?;
    let before = db.count();
    let bad_title = Arc::new(f_746f646f(nat("42")?, byte_input(&[256])?, text_input("note"))?);
    report("text-bad-title", matches!(execute(f_637265617465546f646f(bad_title, Arc::clone(&db)))?, Err(Error::ModelByteRange)))?;
    let bad_note = Arc::new(f_746f646f(nat("43")?, text_input("title"), byte_input(&[255])?)?);
    report("text-bad-note", matches!(execute(f_637265617465546f646f(bad_note, Arc::clone(&db)))?, Err(Error::ModelUtf8)))?;
    report("text-no-effect", db.count() == before)?;
    let long = "abé".repeat(256);
    report("text-long", lan_model_text_to_4279746573(&text_input(&long))? == long
        && text_is(&lan_model_text_from_4279746573(long.clone()), &long))?;
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
        "field-order", "shared", "error", "negative-field", "key-overflow", "no-effect",
        "bool-source-true", "bool-source-false", "bool-lazy", "bool-create-true", "bool-once",
        "bool-create-false", "bool-lookup-true", "bool-lookup-false", "bool-shared", "bool-error",
        "bool-negative-field", "bool-overflow", "bool-key-overflow", "bool-no-effect",
        "text-empty", "text-utf8", "text-byte-range", "text-large-byte", "text-invalid-utf8",
        "text-errors", "text-lazy", "text-create", "text-once", "text-create-value", "text-lookup",
        "text-shared", "text-error", "text-bad-title", "text-bad-note", "text-no-effect", "text-long")]
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
            rust.write_text(source + DOUBLE + (ROOT / "test/models-text-oracle.rs").read_text())
            compiled = run("rustup", "run", "1.98", "rustc", "--edition=2024", "--extern",
                           f"model_derive={library}", rust, "-o", binary)
            return compiled, binary

        compiled, binary = compile_source(emitted.stdout)
        require(compiled.returncode == 0, compiled.stderr)
        executed = run(binary)
        require(executed.returncode == 0 and executed.stdout.splitlines() == expected,
                executed.stderr or executed.stdout)
        # Unused schemas still need both distinct recursive family declarations.
        declaration = work / "declaration.lan"
        declaration.write_text(
            "mu Octets : Type 0 := | empty : Octets | more (byte : Nat) (rest : Octets) : Octets\n"
            "mu Bytes : Type 0 := | bytesNil : Bytes | bytesCons (head : Nat) (tail : Bytes) : Bytes\n"
            "def Text : Type 0 := Octets\n"
            "model First with | title : Text | id : Nat end\n"
            "model Second with | id : Nat | value : Bytes | note : Text end\n")
        schema = run(CLI, "emit", "--target", declaration)
        require(schema.returncode == 0 and not schema.stderr,
                schema.stderr or f"declaration emit rc={schema.returncode}")
        schema_rust = work / "schema.rs"
        schema_rust.write_text(schema.stdout + "\nmod toasty { pub use model_derive::Model; }\n"
                              "fn main() -> Result<(), Error> { Ok(()) }\n")
        compiled = run("rustup", "run", "1.98", "rustc", "--edition=2024", "--extern",
                       f"model_derive={library}", schema_rust, "-o", work / "schema")
        require(compiled.returncode == 0, compiled.stderr)
        mutations = [
            ("negative guard", "if value < 0", "if value < i64::MIN"),
            ("overflow guard", "number.checked_mul(256).and_then(|number| number.checked_add(i64::from(*byte)))",
             "Some(number.wrapping_mul(256).wrapping_add(i64::from(*byte)))"),
            ("result field", "f0: lan_model_from_i64(__lan_row.id)", "f0: lan_model_from_i64(__lan_row.f_76616c7565)"),
            ("missing await", ".exec(&mut __lan_db).await?", ".exec(&mut __lan_db)?"),
            ("false write", "::V0(()) => false", "::V0(()) => true"),
            ("true write", "::V1(()) => true", "::V1(()) => false"),
            ("Bool read", "if __lan_row.f_656e61626c6564", "if !__lan_row.f_656e61626c6564"),
            ("Bool column", "if __lan_row.f_6172636869766564", "if __lan_row.f_656e61626c6564"),
            ("byte range", "[_, _, ..] => Err(Error::ModelByteRange)", "[byte, _, ..] => Ok(*byte)"),
            ("UTF-8 guard", "String::from_utf8(bytes).map_err(|_error| Error::ModelUtf8)",
             "Ok(String::from_utf8_lossy(&bytes).into_owned())"),
            ("text order", "value.bytes().rev().fold(", "value.bytes().fold("),
            ("text column", "lan_model_text_from_4279746573(__lan_row.f_7469746c65)",
             "lan_model_text_from_4279746573(__lan_row.f_6e6f7465.clone())"),
            ("zero byte", "[] => Ok(0)", "[] => Ok(1)"),
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
    print(f"LAN-MODELS OK observations={len(expected)} mutants={killed} native-refusals={native_refusals} declaration-compiles=1 compiler={version.stdout.strip()}")


if __name__ == "__main__":
    main()
