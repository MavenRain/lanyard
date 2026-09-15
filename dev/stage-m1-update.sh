#!/bin/zsh
# Preserve the cumulative deletion gate before checking model updates.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-delete.sh
_build/default/test/lan_update.exe
python3 -P test/lan_update.py
python3 -P test/lan_update_mutations.py
print -r -- 'STAGE-M1-UPDATE OK'
