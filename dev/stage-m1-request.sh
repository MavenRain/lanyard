#!/bin/zsh
# Preserve the cumulative interpreter gate before checking scripted requests.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-run.sh
_build/default/test/lan_request.exe
python3 -P test/lan_request.py
python3 -P test/lan_request_mutations.py
print -r -- 'STAGE-M1-REQUEST OK'
