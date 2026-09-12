#!/bin/zsh
# Crate dependency selection retains every earlier stage check.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-e-crate.sh
python3 -P test/lan_reachable.py
print -r -- 'STAGE-E-REACHABLE OK'
