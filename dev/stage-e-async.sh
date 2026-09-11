#!/bin/zsh
# Async target printing retains every synchronous foreign and native leg.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-e-foreign.sh
_build/default/test/lan_async_emit.exe
python3 -P test/lan_async.py
print -r -- 'STAGE-E-ASYNC OK'
