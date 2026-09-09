#!/bin/zsh
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
prep=${0:A:h}
root=${1:-$prep/..}
# SL round 2026-09-07: the switch is asked for by name, so no absolute
# path of one machine is written here.  The recorded location stays as
# the fallback when opam is absent or answers nothing.
switch_lib=$(opam var --switch zxcaml-p1 lib 2>/dev/null || true)
[[ -d $switch_lib ]] || switch_lib=/Users/oobi/.opam/zxcaml-p1/lib
export PATH=${switch_lib:h}/bin:$PATH
# The bytecode toplevel loads the zarith stub library by name.  The switch
# holds it beside its libraries, and ld.conf does not list that directory,
# so the search path comes from the same answer as the include above.
export CAML_LD_LIBRARY_PATH=$switch_lib/stublibs${CAML_LD_LIBRARY_PATH:+:$CAML_LD_LIBRARY_PATH}
ocaml -I "$switch_lib/zarith" \
  -I "$root/_build/default/lib/.kanon_kernel.objs/byte" \
  -I "$root/_build/default/lib" zarith.cma kanon_kernel.cma "$prep/one-paths.ml"
python3 -P - "$root" <<'PY'
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1])
driver = root / '_build/default/bin/lanyard.exe'
positives = ['identity', 'branches', 'fields', 'shadowing', 'recursive', 'unreachable-capture']
negatives = ['used-twice', 'unused', 'zero-only', 'many-consumer', 'missing-branch',
             'tuple-duplication', 'let-duplication', 'closure-duplication',
             'shadowed-unused', 'field-unused', 'annotation-only',
             'scrutinee-branch', 'recursive-leg', 'unreachable-closure', 'eager-alias',
             'unreachable-capture']
rows = []
for directory, names, code in [('fixtures', positives, 0), ('neg', negatives, 1)]:
    for name in names:
        source = root / 'test' / directory / ('one-' + name + '.kan')
        result = subprocess.run([str(driver), 'check', str(source)],
                                text=True, capture_output=True, timeout=30)
        expected = '' if code == 0 else 'quantity: ' + source.with_suffix('.err').read_text().strip()
        good = result.returncode == code and result.stderr.strip() == expected
        rows.append(good)
        print(f"ONE-PATH {name} {'OK' if good else 'FAIL'} exit={result.returncode} expected={code} stderr={result.stderr.strip()!r}")
print(f"ONE-PATHS {sum(rows)}/{len(rows)} {'OK' if all(rows) else 'FAIL'}")
sys.exit(0 if all(rows) else 1)
PY
