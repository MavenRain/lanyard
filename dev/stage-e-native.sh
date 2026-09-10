#!/bin/zsh
# The native printer slice retains every Stage D leg.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-d.sh
_build/default/test/lan_emit.exe
python3 -P test/lan_native.py
print -r -- 'STAGE-E-NATIVE OK'
