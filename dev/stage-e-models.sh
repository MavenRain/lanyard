#!/bin/zsh
# Model schemas retain the applied foreign type and earlier stage checks.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-e-foreign-types.sh
_build/default/test/lan_models_emit.exe
python3 -P test/lan_models.py
print -r -- 'STAGE-E-MODELS OK'
