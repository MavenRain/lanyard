#!/bin/zsh
# Crate emission retains all connection and earlier stage checks.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-e-connections.sh
python3 -P test/lan_crate.py
print -r -- 'STAGE-E-CRATE OK'
