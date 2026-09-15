#!/bin/zsh
# Preserve the model listing gate before checking Todo title operations.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-all.sh
_build/default/test/lan_text_ops.exe
python3 -P test/lan_text_ops.py
python3 -P test/lan_text_ops_mutations.py
print -r -- 'STAGE-M1-TEXT OK'
