"""Execute target output against strict API doubles and test print-rule semantics."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"
TEST = ROOT / "_build/default/test/lan_foreign_emit.exe"
TIMEOUT = 600


def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, text=True,
                          capture_output=True, timeout=TIMEOUT)


def require(condition, message):
    if not condition:
        print(f"LAN-FOREIGN FAIL: {message}", file=sys.stderr)
        sys.exit(1)


def function(name):
    return "f_" + name.encode().hex()


# These doubles require the same borrowed Cx input and owned redirect output as
# the pinned APIs. SeeOther deliberately has no Clone implementation. They make
# evaluation and clone counts observable, without a network or database.
DOUBLES = r'''
mod toasty {
    pub struct Db(u32);
    pub static COPIES: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);
    impl Db {
        pub fn new(id: u32) -> Self { Self(id) }
        pub fn id(&self) -> u32 { self.0 }
    }
    impl Clone for Db {
        fn clone(&self) -> Self {
            COPIES.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
            Self(self.0)
        }
    }
}
mod topcoat {
    pub mod context {
        pub struct Cx(crate::toasty::Db);
        impl Cx { pub fn new(db: crate::toasty::Db) -> Self { Self(db) } }
        pub trait FromContext { fn get(cx: &Cx) -> &Self; }
        impl FromContext for crate::toasty::Db { fn get(cx: &Cx) -> &Self { &cx.0 } }
        pub fn app_context<T: FromContext>(cx: &Cx) -> &T { T::get(cx) }
    }
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
fn tick(counter: &std::cell::Cell<u32>, value: u32) -> u32 {
    let next = counter.get() + 1;
    counter.set(next);
    value + next
}
'''


def main():
    emitted = run(DRIVER, "emit", "--target", ROOT / "test/fixtures/foreign.lan")
    require(emitted.returncode == 0 and not emitted.stderr, emitted.stderr or "emission failed")
    require(emitted.stdout.encode() == (ROOT / "test/goldens/foreign.rs").read_bytes(), "foreign golden differs")
    forbidden = (r"\b(?:unsafe|unwrap|expect|panic|assert|assert_eq|debug_assert|unreachable|todo)\w*"
                 r"|\b(?:loop|while|return|break|continue|as|Rc|pub)\b|\bfor\s+\w+\s+in\b|\w\[")
    require(not re.search(forbidden, emitted.stdout), "forbidden generated Rust construct")
    observation = run(TEST, "--observations")
    require(observation.returncode == 0 and not observation.stderr, observation.stderr or "template emission failed")
    version = run("rustup", "run", "1.98", "rustc", "--version")
    require(version.returncode == 0 and version.stdout.startswith("rustc 1.98.1 "), "pinned rustc missing")
    harness = '\nfn main() -> Result<(), Error> {\n' + '\n'.join([
        'let uri = Arc::new(topcoat::router::Uri::new("/todos?q=1"));',
        f'println!("{{}}", {function("redirect")}(Arc::clone(&uri))?.location());',
        f'println!("{{}}", {function("redirectLet")}(Arc::clone(&uri))?.location());',
        f'println!("{{}}", {function("forward")}(Arc::clone(&uri))?.location());',
        'println!("{}", Arc::strong_count(&uri));',
        f'println!("{{}}", {function("moveUri")}(topcoat::router::Uri::new("/owned"))?);',
        f'println!("{{}}", {function("moveRedirect")}({function("redirect")}(uri)?)?.location());',
        'let cx = Arc::new(topcoat::context::Cx::new(toasty::Db::new(41)));',
        f'println!("{{}}", {function("contextDb")}(Arc::clone(&cx))?.id());',
        'println!("{}", toasty::COPIES.load(std::sync::atomic::Ordering::SeqCst));',
        'println!("{}", Arc::strong_count(&cx));',
        'let counter = std::cell::Cell::new(0);',
        'println!("{:?}", template_order(&counter));',
        'println!("{}", counter.get());',
        'println!("{:?}", template_repeat(&counter));',
        'println!("{}", counter.get());',
        'Ok(())',
    ]) + '\n}\n'
    expected = ["/todos?q=1", "/todos?q=1", "/todos?q=1", "1", "/owned", "/todos?q=1",
                "41", "1", "1", "(13, 8)", "2", "(16, 16)", "3"]
    with tempfile.TemporaryDirectory(prefix="lanyard-foreign-") as directory:
        rust, binary = Path(directory) / "main.rs", Path(directory) / "main"

        def compile_source(source, templates=observation.stdout):
            rust.write_text(source + DOUBLES + templates + harness)
            return run("rustup", "run", "1.98", "rustc", "--edition=2024", rust, "-o", binary)

        def execute(source, templates=observation.stdout):
            compiled = compile_source(source, templates)
            require(compiled.returncode == 0, compiled.stderr or "compile failed")
            executed = run(binary)
            require(executed.returncode == 0 and not executed.stderr, executed.stderr or "execution failed")
            return executed.stdout.splitlines()

        require(execute(emitted.stdout) == expected, "target observations differ")
        before = "let __lan_arg_0 = tick(&counter, 7); let __lan_arg_1 = tick(&counter, 11);"
        after = "let __lan_arg_1 = tick(&counter, 11); let __lan_arg_0 = tick(&counter, 7);"
        require(before in observation.stdout, "order mutation anchor missing")
        require(execute(emitted.stdout, observation.stdout.replace(before, after, 1)) != expected,
                "argument order mutant survived")
        before = "(*(&*(__lan_arg_0)), *(&*(__lan_arg_0)))"
        after = "(tick(&counter, 13), tick(&counter, 13))"
        require(before in observation.stdout, "repeated argument mutation anchor missing")
        require(execute(emitted.stdout, observation.stdout.replace(before, after, 1)) != expected,
                "repeated evaluation mutant survived")
        before = "app_context::<toasty::Db>((&*(__lan_arg_0)))"
        after = "app_context::<toasty::Db>(__lan_arg_0)"
        require(before in emitted.stdout, "borrow mutation anchor missing")
        rejected = compile_source(emitted.stdout.replace(before, after, 1))
        require(rejected.returncode != 0 and "expected `&Cx`" in rejected.stderr,
                "missing borrow mutant did not fail the input type")
        refusals = [
            ("async-closure", "def closure : Db -> prod (Nat -> Nat) := fun (db : Db) => tuple (fun (n : Nat) => let done : prod () := Db.push_schema db in natAdd n 1)", "async closure"),
            ("clone", "def copy : SeeOther -> SeeOther := fun (x : SeeOther) => x", "owned copy of a shared foreign value"),
            ("applied", "def identity : Deferred Uri -> Deferred Uri := fun (x : Deferred Uri) => x", "Rust emission: foreign type (Out SPi"),
            ("aggregate", "def pair : Uri -> prod (Uri, Uri) := fun (x : Uri) => tuple (x, x)", "foreign aggregate layout"),
            ("schema", "model Row with | id : Nat end\ndef create : Row -> Db -> Row := fun (row : Row) (db : Db) => Row.create row db", "foreign schema Model.create"),
        ]
        for name, source, diagnostic in refusals:
            path = Path(directory) / f"{name}.lan"
            path.write_text(source + "\n")
            checked = run(DRIVER, "check", path)
            require(checked.returncode == 0, f"{name} did not check: {checked.stderr}")
            rejected = run(DRIVER, "emit", "--target", path)
            require(rejected.returncode == 1 and not rejected.stdout and diagnostic in rejected.stderr,
                    f"{name} refusal differs: {rejected.stderr}")
        for args in [("--target",), ("--target", "test/fixtures/b01-function-eta.kan"),
                     ("--target", "test/fixtures/foreign.lan", "extra")]:
            rejected = run(DRIVER, "emit", *args)
            require(rejected.returncode == 64 and not rejected.stdout, "target usage accepted")
        rejected = run(DRIVER, "emit", "--target", ROOT / "examples/m0-todo.lan")
        require(rejected.returncode == 1 and not rejected.stdout and "foreign aggregate layout" in rejected.stderr,
                f"Todo layout refusal differs: {rejected.stderr}")
    print(f"LAN-FOREIGN OK observations={len(expected)} mutants=3 refusals={len(refusals)} compiler={version.stdout.strip()}")


if __name__ == "__main__":
    main()
