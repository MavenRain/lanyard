#!/bin/zsh
# Preserve the cumulative build gate before checking interpreted execution.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-build.sh
_build/default/test/lan_run.exe
python3 -P test/lan_run.py
python3 -P test/lan_run_mutations.py
print -r -- 'STAGE-M1-RUN OK'
