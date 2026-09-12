"""Check connection emission, async observations and independent mutations."""
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
        sys.exit(f"LAN-CONNECTIONS FAIL: {message}")


DERIVE = '''extern crate proc_macro;
#[proc_macro_derive(Model, attributes(key))]
pub fn model(_input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    proc_macro::TokenStream::new()
}
'''


def main():
    emitted = run(CLI, "emit", "--target", "test/fixtures/connections.lan")
    require(emitted.returncode == 0, emitted.stderr)
    require(emitted.stdout == (ROOT / "test/goldens/connections.rs").read_text(), "golden drift")
    native = run(CLI, "emit", "--native", "test/fixtures/connections.lan")
    require(native.returncode != 0 and not native.stdout and "Rust emission:" in native.stderr,
            "native connection was not refused")
    version = run("rustup", "run", "1.98", "rustc", "--version")
    require(version.returncode == 0 and version.stdout.startswith("rustc 1.98.1 "), "pinned rustc missing")
    harness = (ROOT / "test/connections-double.rs").read_text()
    oracle = (ROOT / "test/models-text-oracle.rs").read_text()
    expected = re.findall(r'report\("([a-z0-9-]+)"', harness)
    mutations = [
        ("wrong-models", "toasty::models!(LanModel436f756e746572, LanModel4175646974)",
         "toasty::models!(LanModel4175646974, LanModel436f756e746572)", "execution"),
        ("wrong-url", ".connect(&__lan_url).await?", '.connect("wrong").await?', "execution"),
        ("lost-await", ".connect(&__lan_url).await?", ".connect(&__lan_url)?", "compilation"),
        ("byte-wrap", "[_, _, ..] => Err(Error::ModelByteRange)", "[byte, _, ..] => Ok(*byte)", "execution"),
        ("lossy-url", "String::from_utf8(bytes).map_err(|_error| Error::ModelUtf8)",
         "Ok(String::from_utf8_lossy(&bytes).into_owned())", "execution"),
        ("inline-wrong-model", "toasty::models!(LanModel4175646974)",
         "toasty::models!(LanModel436f756e746572)", "execution"),
        ("inline-wrong-argument", " }; f_5f5f6c616e5f636f6e6e6563745f32(Arc::clone(&(a1)))",
         " }; f_5f5f6c616e5f636f6e6e6563745f32(Arc::clone(&(a0)))", "execution"),
    ]
    with tempfile.TemporaryDirectory(prefix="lanyard-connections-") as temporary:
        work = Path(temporary)
        derive = work / "derive.rs"
        derive.write_text(DERIVE)
        library = work / ("libmodel_derive.dylib" if sys.platform == "darwin" else "libmodel_derive.so")
        built = run("rustup", "run", "1.98", "rustc", "--crate-name", "model_derive",
                    "--crate-type", "proc-macro", derive, "-o", library)
        require(built.returncode == 0, built.stderr)

        def compile_source(source):
            rust = work / "probe.rs"
            binary = work / "probe"
            rust.write_text(source + harness + oracle)
            result = run("rustup", "run", "1.98", "rustc", "--edition=2024", "--extern",
                         f"model_derive={library}", "-Awarnings", rust, "-o", binary)
            return result, binary

        compiled, binary = compile_source(emitted.stdout)
        require(compiled.returncode == 0, compiled.stderr)
        observed = run(binary)
        require(observed.returncode == 0, observed.stdout + observed.stderr)
        require(observed.stdout.splitlines() == [f"{name} OK" for name in expected],
                f"observation set differs: {observed.stdout}")
        killed = 0
        for name, before, after, failure in mutations:
            require(before in emitted.stdout, f"mutation target absent: {name}")
            compiled, binary = compile_source(emitted.stdout.replace(before, after))
            if failure == "compilation":
                require(compiled.returncode != 0 and "Try" in compiled.stderr, f"mutation survived: {name}")
            else:
                require(compiled.returncode == 0, f"mutation did not compile: {name}\n{compiled.stderr}")
                observed = run(binary)
                require(observed.returncode != 0 and "FAIL" in observed.stderr, f"mutation survived: {name}")
            killed += 1
    print(f"LAN-CONNECTIONS OK observations={len(expected)} mutants={killed} native-refusals=1 compiler={version.stdout.strip()}")


if __name__ == "__main__":
    main()
