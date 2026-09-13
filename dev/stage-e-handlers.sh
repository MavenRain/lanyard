#!/bin/zsh
# Finite handler specialization retains every preceding crate check.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-e-reachable.sh
python3 -P test/lan_handlers.py
print -r -- 'STAGE-E-HANDLERS OK'
