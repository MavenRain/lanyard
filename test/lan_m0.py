"""Observe model output, conversion and write errors, and atomic CLI refusals."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "_build/default/bin/lanyard.exe"
DERIVE = '''extern crate proc_macro;
#[proc_macro_derive(Model, attributes(key))]
pub fn model(_input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    proc_macro::TokenStream::new()
}
'''


def run(*args):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, text=True,
                          capture_output=True, timeout=120)


def require(condition, message):
    if not condition:
        sys.exit(f"LAN-M0 FAIL: {message}")


def main():
    fixture = (ROOT / "corpus/m0/todo.lan").read_text()
    prelude = fixture.split("def main :", 1)[0]
    observations, refusals, mutants = [], [], []
    with tempfile.TemporaryDirectory(prefix="lanyard-m0-") as temporary:
        work = Path(temporary)
        derive = work / "derive.rs"
        derive.write_text(DERIVE)
        library = work / ("libmodel_derive.dylib" if sys.platform == "darwin" else "libmodel_derive.so")
        built = run("rustup", "run", "1.98", "rustc", "--crate-name", "model_derive",
                    "--crate-type", "proc-macro", derive, "-o", library)
        require(built.returncode == 0, built.stderr)

        def emit(name, source, model="Todo"):
            path = work / f"{name}.lan"
            path.write_text(source)
            output = work / name
            result = run(CLI, "emit", "--crate", output, "--print-model", model, path)
            require(result.returncode == 0 and not result.stdout and not result.stderr,
                    f"{name}: {result.stderr}")
            return (output / "src/main.rs").read_text()

        def compile_source(name, source):
            rust = work / f"{name}.rs"
            rust.write_text(source + "\nmod toasty { pub use model_derive::Model; }\n")
            binary = work / f"{name}-program"
            result = run("rustup", "run", "1.98", "rustc", "--edition=2024", "--extern",
                         f"model_derive={library}", "-Dunused_must_use", rust, "-o", binary)
            require(result.returncode == 0, f"{name}: {result.stderr}")
            return binary

        def observe(name, value, expected, error=None, prefix=""):
            source = emit(name, prelude + prefix + f"def main : Todo := {value}\n")
            require(re.search(r"\b(?:unsafe|unwrap|expect|panic|assert|while|loop|as)\b", source) is None,
                    f"{name}: Rust house rules")
            binary = compile_source(name, source)
            result = run(binary)
            if error is None:
                require(result.returncode == 0 and result.stdout == expected and not result.stderr,
                        f"{name}: {result}")
            else:
                require(result.returncode != 0 and not result.stdout and error in result.stderr,
                        f"{name}: {result}")
            observations.append(name)
            return source, binary

        source, binary = observe("row", 'tuple (1, b"hi", inj 0 of 2 ())',
                                 'Todo { id: 1, title: "hi", completed: false }\n')
        observe("zero", 'tuple (0, b"", inj 1 of 2 ())',
                'Todo { id: 0, title: "", completed: true }\n')
        observe("max", 'tuple (9223372036854775807, b"ok", inj 1 of 2 ())',
                'Todo { id: 9223372036854775807, title: "ok", completed: true }\n')
        observe("escaped", r'tuple (7, b"a\n\"b\\c", inj 0 of 2 ())',
                'Todo { id: 7, title: "a\\n\\\"b\\\\c", completed: false }\n')
        observe("utf8", 'tuple (9, b"café", inj 0 of 2 ())',
                'Todo { id: 9, title: "café", completed: false }\n')
        observe("range", 'tuple (9223372036854775808, b"hi", inj 0 of 2 ())', "", "ModelRange")
        observe("byte", 'tuple (1, bytesCons 256 bytesNil, inj 0 of 2 ())', "", "ModelByteRange")
        observe("invalid-utf8", 'tuple (1, bytesCons 255 bytesNil, inj 0 of 2 ())', "", "ModelUtf8")
        alias = emit("alias", prelude + "def View : Type 0 := Todo\n"
                     'def main : View := tuple (2, b"alias", inj 0 of 2 ())\n')
        result = run(compile_source("alias", alias))
        require(result.returncode == 0 and not result.stderr
                and result.stdout == 'Todo { id: 2, title: "alias", completed: false }\n', "model alias")
        observations.append("alias")

        read_fd, write_fd = os.pipe()
        os.close(read_fd)
        with os.fdopen(write_fd, "wb") as closed_pipe:
            result = subprocess.run([str(binary)], stdout=closed_pipe, stderr=subprocess.PIPE,
                                    text=True, timeout=120)
        require(result.returncode != 0 and "Output(" in result.stderr and "BrokenPipe" in result.stderr,
                f"closed stdout did not return an output error: {result}")
        observations.append("broken-pipe")

        for name, program, model, diagnostic in (
            ("unknown", prelude + 'def main : Todo := tuple (1, b"hi", inj 0 of 2 ())',
             "Unknown", "printed model is unknown or not reachable"),
            ("unreached", prelude + 'model Note with\n| id : Nat\n| body : Bytes\nend\n\n'
             'def main : Todo := tuple (1, b"hi", inj 0 of 2 ())',
             "Note", "printed model is unknown or not reachable"),
            ("wrong-result", prelude + 'def main : Nat := let row : Todo := tuple (1, b"hi", inj 0 of 2 ()) in 1',
             "Todo", "entry point result differs from printed model"),
            ("arguments", prelude + 'def main : Todo -> Todo := fun (row : Todo) => row',
             "Todo", "entry point requires runtime arguments"),
            ("type-only", prelude + 'def main : Type 0 := Todo',
             "Todo", "missing runtime entry point"),
        ):
            path = work / f"{name}.lan"
            path.write_text(program)
            checked = run(CLI, "check", path)
            require(checked.returncode == 0, f"{name}: refusal fixture did not check")
            output = work / name
            result = run(CLI, "emit", "--crate", output, "--print-model", model, path)
            require(result.returncode == 1 and not result.stdout and diagnostic in result.stderr
                    and not output.exists() and not Path(str(output) + ".partial").exists(),
                    f"{name}: {result}")
            refusals.append(name)

        occupied = work / "row"
        saved = (occupied / "src/main.rs").read_bytes()
        result = run(CLI, "emit", "--crate", occupied, "--print-model", "Todo", ROOT / "corpus/m0/todo.lan")
        require(result.returncode == 64 and not result.stdout and "output path exists" in result.stderr
                and (occupied / "src/main.rs").read_bytes() == saved, "occupied output changed")
        refusals.append("occupied")
        for args in (("--print-model", "Todo"), ("--target", "--print-model", "Todo"),
                     ("--crate", work / "missing-model", "--print-model")):
            result = run(CLI, "emit", *args, ROOT / "corpus/m0/todo.lan")
            require(result.returncode == 64 and not result.stdout and "usage:" in result.stderr,
                    f"invalid output options: {result}")
            refusals.append("usage")

        write = "std::io::Write::write_all(&mut std::io::stdout().lock(), line.as_bytes()).map_err(LanMainError::Output)"
        for name, before, after in (("missing-output", write, "Ok(())"),
                                    ("false-tag", "::V0(()) => false", "::V0(()) => true")):
            require(source.count(before) == 1, f"{name}: mutation anchor differs")
            result = run(compile_source(name, source.replace(before, after)))
            require(result.returncode == 0 and not result.stderr
                    and result.stdout != 'Todo { id: 1, title: "hi", completed: false }\n',
                    f"{name}: mutant survived")
            mutants.append(name)
    print(f"LAN-M0 OK observations={len(observations)} refusals={len(refusals)} mutants={len(mutants)}")


if __name__ == "__main__":
    main()
