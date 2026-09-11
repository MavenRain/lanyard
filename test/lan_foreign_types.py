"""Check applied foreign layouts, moves, sharing, suspension and refusal paths."""
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "_build/default/bin/lanyard.exe"


def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, text=True,
                          capture_output=True, timeout=600)


def require(condition, message):
    if not condition:
        print(f"LAN-FOREIGN-TYPES FAIL: {message}", file=sys.stderr)
        sys.exit(1)


def function(name):
    return "f_" + name.encode().hex()


def replace_once(text, before, after):
    require(text.count(before) == 1, f"mutation or double anchor differs: {before}")
    return text.replace(before, after, 1)


def doubles():
    # Reuse the async gate's suspending database double. Neither new wrapper
    # implements Clone, so an accidental copy fails at compilation.
    deferred = r'''
    pub struct Deferred<T>(Option<Box<T>>);
    impl<T> From<T> for Deferred<T> {
        fn from(value: T) -> Self { Self(Some(Box::new(value))) }
    }
    impl<T> Default for Deferred<T> { fn default() -> Self { Self(None) } }
    impl<T> Deferred<T> {
        pub fn is_unloaded(&self) -> bool { self.0.is_none() }
        pub fn loaded(&self) -> Option<&T> { self.0.as_deref() }
    }
'''
    form = r'''
        pub mod content {
            pub struct Form<T>(T);
            impl<T> From<T> for Form<T> { fn from(value: T) -> Self { Self(value) } }
            impl<T> std::ops::Deref for Form<T> {
                type Target = T;
                fn deref(&self) -> &T { &self.0 }
            }
        }
'''
    async_doubles = runpy.run_path(str(ROOT / "test/lan_async.py"))["DOUBLES"]
    text = replace_once(async_doubles, "pub struct Db(u32);", "pub struct Db(u32);" + deferred)
    return replace_once(text, "pub struct Uri(String);", "pub struct Uri(String);" + form)


def harness():
    return '\nfn main() -> Result<(), Error> {\n' + '\n'.join([
        'let form = topcoat::router::content::Form::from(topcoat::router::Uri::new("/form"));',
        f'println!("{{}}", &*{function("moveForm")}(form)?);',
        'let deferred = toasty::Deferred::from(topcoat::router::Uri::new("/deferred"));',
        f'println!("{{}}", {function("moveDeferred")}(deferred)?.loaded().ok_or(Error::Arithmetic)?);',
        f'println!("{{}}", {function("moveDeferred")}(toasty::Deferred::default())?.is_unloaded());',
        'let nested = topcoat::router::content::Form::from(toasty::Deferred::from(topcoat::router::Uri::new("/nested")));',
        f'println!("{{}}", {function("moveNested")}(nested)?.loaded().ok_or(Error::Arithmetic)?);',
        'let reverse = toasty::Deferred::from(topcoat::router::content::Form::from(topcoat::router::Uri::new("/reverse")));',
        f'println!("{{}}", &**{function("moveReverse")}(reverse)?.loaded().ok_or(Error::Arithmetic)?);',
        'let pair = T70726f64756374286e61742c6e617429 { f0: Nat::decimal("7")?, f1: Nat::decimal("11")? };',
        f'let pair = {function("movePair")}(topcoat::router::content::Form::from(pair))?;',
        'println!("{:?} {:?}", pair.f0, pair.f1);',
        'let bytes = T6e6f6d696e616c28353a427974657329::V1(Box::new((Nat::decimal("65")?, T6e6f6d696e616c28353a427974657329::V0)));',
        f'let bytes = {function("moveBytes")}(toasty::Deferred::from(bytes))?;',
        'println!("{:?}", bytes.loaded().ok_or(Error::Arithmetic)?);',
        'let value = Arc::new(topcoat::router::content::Form::from(topcoat::router::Uri::new("/shared")));',
        f'{function("reuse")}(Arc::clone(&value))?;',
        'println!("{}", Arc::strong_count(&value));',
        'let db = Arc::new(toasty::Db::new(1));',
        f'let mut future = Box::pin(assert_send({function("keep")}(Arc::clone(&db), Arc::clone(&value))));',
        'println!("{:?} {}", toasty::counts(), Arc::strong_count(&value));',
        'let mut cx = std::task::Context::from_waker(std::task::Waker::noop());',
        'println!("{}", std::future::Future::poll(future.as_mut(), &mut cx).is_pending());',
        'println!("{:?} {}", toasty::counts(), Arc::strong_count(&value));',
        'drive(future)??;',
        'println!("{:?} {}", toasty::counts(), Arc::strong_count(&value));',
        'let owned = toasty::Deferred::from(topcoat::router::Uri::new("/owned-await"));',
        f'println!("{{}}", drive({function("keepOwned")}(Arc::clone(&db), owned))??.loaded().ok_or(Error::Arithmetic)?);',
        'let bad = Arc::new(toasty::Db::new(9));',
        f'println!("{{}}", drive({function("keep")}(bad, Arc::clone(&value)))?.is_err());',
        'println!("{}", Arc::strong_count(&value));',
        'Ok(())',
    ]) + '\n}\n'


def main():
    emitted = run(DRIVER, "emit", "--target", ROOT / "test/fixtures/foreign-types.lan")
    require(emitted.returncode == 0 and not emitted.stderr, emitted.stderr or "emission failed")
    require(emitted.stdout.encode() == (ROOT / "test/goldens/foreign-types.rs").read_bytes(), "golden differs")
    forbidden = (r"\b(?:unsafe|unwrap|expect|panic|assert|assert_eq|debug_assert|unreachable|todo)\w*"
                 r"|\b(?:loop|while|return|break|continue|as|Rc|pub)\b|\bfor\s+\w+\s+in\b|\w\[")
    require(not re.search(forbidden, emitted.stdout), "forbidden generated Rust construct")
    version = run("rustup", "run", "1.98", "rustc", "--version")
    require(version.returncode == 0 and version.stdout.startswith("rustc 1.98.1 "), "pinned rustc missing")
    expected = ["/form", "/deferred", "true", "/nested", "/reverse", "Nat([7]) Nat([11])",
                "V1((Nat([65]), V0))", "1", "(0, 0, 0) 2", "true", "(1, 0, 1) 2",
                "(1, 1, 1) 1", "/owned-await", "true", "1"]
    with tempfile.TemporaryDirectory(prefix="lanyard-foreign-types-") as directory:
        rust, binary = Path(directory) / "main.rs", Path(directory) / "main"

        def compile_source(source):
            rust.write_text(source + doubles() + harness())
            return run("rustup", "run", "1.98", "rustc", "--edition=2024", rust, "-o", binary)

        compiled = compile_source(emitted.stdout)
        require(compiled.returncode == 0, compiled.stderr or "compile failed")
        executed = run(binary)
        require(executed.returncode == 0 and not executed.stderr and executed.stdout.splitlines() == expected,
                executed.stderr or f"observations differ: {executed.stdout}")
        header = f'fn {function("moveDeferred")}(a0: toasty::Deferred<topcoat::router::Uri>) -> Result<toasty::Deferred<topcoat::router::Uri>, Error> {{\n    Ok(a0)'
        copied = replace_once(emitted.stdout, header, header.removesuffix("Ok(a0)") + "Ok(a0.clone())")
        rejected = compile_source(copied)
        require(rejected.returncode != 0 and "clone" in rejected.stderr, "owned-copy mutant survived")
        wrong = emitted.stdout.replace("Form<topcoat::router::Uri>", "Form<Nat>")
        require(wrong != emitted.stdout, "type substitution mutation anchor missing")
        rejected = compile_source(wrong)
        require(rejected.returncode != 0 and "mismatched types" in rejected.stderr, "wrong type argument mutant survived")
        lost = replace_once(emitted.stdout, header, header.removesuffix("Ok(a0)") + "Ok(toasty::Deferred::default())")
        compiled = compile_source(lost)
        require(compiled.returncode == 0, compiled.stderr or "lost value mutant did not compile")
        executed = run(binary)
        require(executed.returncode != 0, "lost payload mutant survived")
        refused = [
            ("shared-copy", "def copy : Form Uri -> Form Uri := fun (x : Form Uri) => x", "owned copy of a shared foreign value"),
            ("opaque-inner", "axiom Hidden : Type 0\ndef move : (1 x : Form Hidden) -> Form Hidden := fun (1 x : Form Hidden) => x", "foreign type Hidden"),
            ("aggregate", "def copy : Form Uri -> prod (Form Uri, Form Uri) := fun (x : Form Uri) => tuple (x, x)", "foreign aggregate layout"),
            ("runtime-argument", "axiom Vec : (0 T : Type 0) -> (1 n : Nat) -> Type 0\n"
             "def move : (1 x : Vec Nat 3) -> Vec Nat 3 := fun (1 x : Vec Nat 3) => x",
             "Rust emission: foreign type (Out SPi"),
            ("index-argument", "axiom Buf : (0 n : Nat) -> Type 0\n"
             "def move : (1 x : Buf 3) -> Buf 3 := fun (1 x : Buf 3) => x",
             "Rust emission: foreign type (Out SPi"),
        ]
        for name, source, diagnostic in refused:
            path = Path(directory) / f"{name}.lan"
            path.write_text(source + "\n")
            checked = run(DRIVER, "check", path)
            require(checked.returncode == 0, f"{name} did not check: {checked.stderr}")
            rejected = run(DRIVER, "emit", "--target", path)
            require(rejected.returncode == 1 and not rejected.stdout and diagnostic in rejected.stderr,
                    f"{name} refusal differs: {rejected.stderr}")
        rejected = run(DRIVER, "emit", "--native", ROOT / "test/fixtures/foreign-types.lan")
        require(rejected.returncode == 1 and not rejected.stdout and "foreign type Uri" in rejected.stderr,
                f"native refusal differs: {rejected.stderr}")
    print(f"LAN-FOREIGN-TYPES OK observations={len(expected)} mutants=3 refusals={len(refused)} compiler={version.stdout.strip()}")


if __name__ == "__main__":
    main()
