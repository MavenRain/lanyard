#!/bin/zsh
# Connection schemas retain the scalar model and earlier stage checks.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-e-models.sh
_build/default/test/lan_connections_emit.exe
python3 -P test/lan_connections.py
print -r -- 'STAGE-E-CONNECTIONS OK'
