#!/bin/zsh
# Preserve the cumulative update gate before checking ordered model lists.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-update.sh
_build/default/test/lan_all.exe
python3 -P test/lan_all.py
python3 -P test/lan_all_mutations.py
print -r -- 'STAGE-M1-ALL OK'
