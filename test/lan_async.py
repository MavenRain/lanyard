"""Observe async output, real suspension, error propagation and Send bounds."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
TIMEOUT = 600


def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, text=True,
                          capture_output=True, timeout=TIMEOUT)


def require(condition, message):
    if not condition:
        print(f"LAN-ASYNC FAIL: {message}", file=sys.stderr)
        sys.exit(1)


def function(name):
    return "f_" + name.encode().hex()


DOUBLES = r'''
mod toasty {
    use std::sync::atomic::{AtomicU32, Ordering};
    pub static STARTED: AtomicU32 = AtomicU32::new(0);
    pub static FINISHED: AtomicU32 = AtomicU32::new(0);
    pub static ORDER: AtomicU32 = AtomicU32::new(0);
    pub struct Db(u32);
    #[derive(Debug)]
    pub struct Error(u32);
    impl std::fmt::Display for Error {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            write!(f, "database {}", self.0)
        }
    }
    impl std::error::Error for Error {}
    enum Phase { Start, Waiting }
    struct Push<'a> { db: &'a Db, phase: Phase }
    impl std::future::Future for Push<'_> {
        type Output = Result<(), Error>;
        fn poll(self: std::pin::Pin<&mut Self>, cx: &mut std::task::Context<'_>)
            -> std::task::Poll<Self::Output> {
            let this = self.get_mut();
            match this.phase {
                Phase::Start => {
                    STARTED.fetch_add(1, Ordering::SeqCst);
                    let previous = ORDER.load(Ordering::SeqCst);
                    ORDER.store(previous * 10 + this.db.0, Ordering::SeqCst);
                    this.phase = Phase::Waiting;
                    cx.waker().wake_by_ref();
                    std::task::Poll::Pending
                }
                Phase::Waiting => {
                    FINISHED.fetch_add(1, Ordering::SeqCst);
                    std::task::Poll::Ready(if this.db.0 == 9 { Err(Error(9)) } else { Ok(()) })
                }
            }
        }
    }
    impl Db {
        pub fn new(id: u32) -> Self { Self(id) }
        pub async fn push_schema(&self) -> Result<(), Error> {
            Push { db: self, phase: Phase::Start }.await
        }
    }
    pub fn counts() -> (u32, u32, u32) {
        (STARTED.load(Ordering::SeqCst), FINISHED.load(Ordering::SeqCst), ORDER.load(Ordering::SeqCst))
    }
    pub fn reset() {
        STARTED.store(0, Ordering::SeqCst);
        FINISHED.store(0, Ordering::SeqCst);
        ORDER.store(0, Ordering::SeqCst);
    }
}
mod topcoat {
    pub mod router {
        pub struct Uri(String);
        impl Uri { pub fn new(value: &str) -> Self { Self(value.to_owned()) } }
        impl std::fmt::Display for Uri {
            fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result { f.write_str(&self.0) }
        }
        pub mod error {
            pub struct SeeOther(String);
            impl SeeOther { pub fn location(&self) -> &str { &self.0 } }
            pub fn see_other(uri: impl AsRef<str>) -> SeeOther { SeeOther(uri.as_ref().to_owned()) }
        }
    }
}
fn assert_send<F: std::future::Future + Send>(future: F) -> F { future }
fn drive<F: std::future::Future + Send>(future: F) -> Result<F::Output, Error> {
    let mut future = std::pin::pin!(assert_send(future));
    let mut cx = std::task::Context::from_waker(std::task::Waker::noop());
    std::iter::repeat_with(|| future.as_mut().poll(&mut cx)).take(16)
        .find_map(|poll| match poll {
            std::task::Poll::Ready(value) => Some(value),
            std::task::Poll::Pending => None,
        }).ok_or(Error::Arithmetic)
}
'''


def harness():
    return '\nfn main() -> Result<(), Error> {\n' + '\n'.join([
        'let db = Arc::new(toasty::Db::new(1));',
        f'let future = assert_send({function("push")}(Arc::clone(&db)));',
        'println!("{:?}", toasty::counts());',
        'let mut future = Box::pin(future);',
        'let mut cx = std::task::Context::from_waker(std::task::Waker::noop());',
        'println!("{}", std::future::Future::poll(future.as_mut(), &mut cx).is_pending());',
        'println!("{:?}", toasty::counts());',
        'drop(future);',
        'println!("{}", Arc::strong_count(&db));',
        'toasty::reset();',
        f'drive({function("twice")}(Arc::clone(&db)))??;',
        'println!("{:?}", toasty::counts());',
        'println!("{}", Arc::strong_count(&db));',
        'toasty::reset();',
        'let second = Arc::new(toasty::Db::new(2));',
        f'drive({function("sequential")}(Arc::clone(&db), Arc::clone(&second)))??;',
        'println!("{:?}", toasty::counts());',
        'toasty::reset();',
        'let bad = Arc::new(toasty::Db::new(9));',
        f'let failure = drive({function("sequential")}(Arc::clone(&bad), Arc::clone(&second)))?;',
        'println!("{}", failure.map(|()| "ok".to_owned()).unwrap_or_else(|error| error.to_string()));',
        'println!("{:?}", toasty::counts());',
        'println!("{}", Arc::strong_count(&bad));',
        f'let failure = drive({function("forward")}(Arc::clone(&bad)))?;',
        'println!("{}", failure.err().and_then(|error| std::error::Error::source(&error).map(ToString::to_string)).unwrap_or_default());',
        'toasty::reset();',
        'let uri = Arc::new(topcoat::router::Uri::new("/after-await"));',
        f'println!("{{}}", drive({function("keep")}(Arc::clone(&db), Arc::clone(&uri)))??.location());',
        'println!("{}", Arc::strong_count(&uri));',
        'println!("{:?}", toasty::counts());',
        'toasty::reset();',
        f'drive({function("choose")}(Arc::new(T73756d28756e69742c756e697429::V1(())), Arc::clone(&bad)))??;',
        'println!("{:?}", toasty::counts());',
        f'drive({function("choose")}(Arc::new(T73756d28756e69742c756e697429::V0(())), Arc::clone(&db)))??;',
        'println!("{:?}", toasty::counts());',
        f'println!("{{:?}}", {function("pure")}(Arc::new(Nat::decimal("4")?))?);',
        'Ok(())',
    ]) + '\n}\n'


def main():
    emitted = run(DRIVER, "emit", "--target", ROOT / "test/fixtures/async.lan")
    require(emitted.returncode == 0 and not emitted.stderr, emitted.stderr or "emission failed")
    require(emitted.stdout.encode() == (ROOT / "test/goldens/async.rs").read_bytes(), "async golden differs")
    forbidden = (r"\b(?:unsafe|unwrap|expect|panic|assert|assert_eq|debug_assert|unreachable|todo)\w*"
                 r"|\b(?:loop|while|return|break|continue|as|Rc|pub)\b|\bfor\s+\w+\s+in\b|\w\[")
    require(not re.search(forbidden, emitted.stdout), "forbidden generated Rust construct")
    version = run("rustup", "run", "1.98", "rustc", "--version")
    require(version.returncode == 0 and version.stdout.startswith("rustc 1.98.1 "), "pinned rustc missing")
    expected = ["(0, 0, 0)", "true", "(1, 0, 1)", "1", "(2, 2, 11)", "1",
                "(2, 2, 12)", "database 9", "(1, 1, 9)", "1", "database 9",
                "/after-await", "1", "(1, 1, 1)", "(0, 0, 0)", "(1, 1, 1)", "Nat([5])"]
    with tempfile.TemporaryDirectory(prefix="lanyard-async-") as directory:
        rust, binary = Path(directory) / "main.rs", Path(directory) / "main"

        def compile_source(source):
            rust.write_text(source + DOUBLES + harness())
            return run("rustup", "run", "1.98", "rustc", "--edition=2024", rust, "-o", binary)

        def execute(source):
            compiled = compile_source(source)
            require(compiled.returncode == 0, compiled.stderr or "compile failed")
            executed = run(binary)
            require(executed.returncode == 0 and not executed.stderr, executed.stderr or "execution failed")
            return executed.stdout.splitlines()

        observed = execute(emitted.stdout)
        require(observed == expected, f"async observations differ: {observed}")
        anchor = "push_schema().await?"
        require(emitted.stdout.count(anchor) == 1, "foreign await anchor differs")
        require(execute(emitted.stdout.replace(anchor, "push_schema().await.map_or((), |_| ())")) != expected,
                "swallowed error mutant survived")
        rejected = compile_source(emitted.stdout.replace(anchor, "push_schema()?"))
        require(rejected.returncode != 0 and "Try" in rejected.stderr, "missing await mutant survived")
        anchor = f'let v2 = {function("push")}(Arc::clone(&(a0))).await?; {function("push")}(Arc::clone(&(a1))).await?'
        require(emitted.stdout.count(anchor) == 1, "sequence anchor differs")
        reverse = anchor.replace("a0", "TEMP").replace("a1", "a0").replace("TEMP", "a1")
        require(execute(emitted.stdout.replace(anchor, reverse)) != expected, "reordered effects mutant survived")
        rejected = compile_source(emitted.stdout.replace("use std::sync::Arc;", "use std::rc::Rc as Arc;"))
        require(rejected.returncode != 0 and "cannot be sent between threads safely" in rejected.stderr,
                "non-Send mutant survived")
        refused = run(DRIVER, "emit", "--native", ROOT / "test/fixtures/async.lan")
        require(refused.returncode == 1 and not refused.stdout and "foreign type Db" in refused.stderr,
                "native foreign refusal differs")
    print(f"LAN-ASYNC OK observations={len(expected)} mutants=4 native-refusals=1 compiler={version.stdout.strip()}")


if __name__ == "__main__":
    main()
