#!/bin/zsh
# Synchronous foreign printing retains every native Stage E leg.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-e-native.sh
_build/default/test/lan_foreign_emit.exe
python3 -P test/lan_foreign.py
print -r -- 'STAGE-E-FOREIGN OK'
