#!/bin/zsh
# Retain the form gate before checking text responses.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-form.sh
_build/default/test/lan_response.exe
python3 -P test/lan_response.py
python3 -P test/lan_response_mutations.py
print -r -- 'STAGE-M1-RESPONSE OK'
