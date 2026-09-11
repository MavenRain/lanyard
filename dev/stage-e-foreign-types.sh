#!/bin/zsh
# Applied foreign layouts retain all native, foreign and async checks.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-e-async.sh
_build/default/test/lan_foreign_types_emit.exe
python3 -P test/lan_foreign_types.py
print -r -- 'STAGE-E-FOREIGN-TYPES OK'
