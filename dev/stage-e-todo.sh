#!/bin/zsh
# The M0 Todo golden and model output retain every preceding stage check.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-e-handlers.sh
python3 -P dev/emit-diff.py
python3 -P test/lan_m0.py
python3 -P test/lan_m0_mutations.py
print -r -- 'STAGE-E-TODO OK'
