#!/bin/zsh
# Preserve substring search before checking prefix and suffix matching.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-text-contains.sh
_build/default/test/lan_text_boundaries.exe
python3 -P test/lan_text_boundaries.py
python3 -P test/lan_text_boundaries.py --mutations
zsh dev/house.sh
print -r -- 'STAGE-M1-TEXT-BOUNDARIES OK'
