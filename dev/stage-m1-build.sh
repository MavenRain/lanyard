#!/bin/zsh
# The Cargo driver retains the cumulative Stage F checks.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-f-gates.sh
python3 -P test/lan_build.py
print -r -- 'STAGE-M1-BUILD OK'
