#!/bin/zsh
# Preserve the cumulative request gate before checking model deletion.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-request.sh
_build/default/test/lan_delete.exe
python3 -P test/lan_delete.py
python3 -P test/lan_delete_mutations.py
print -r -- 'STAGE-M1-DELETE OK'
