#!/bin/zsh
# Retain the HTML gate before checking composed text.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-html.sh
_build/default/test/lan_concat.exe
python3 -P test/lan_concat.py
python3 -P test/lan_concat_mutations.py
print -r -- 'STAGE-M1-CONCAT OK'
