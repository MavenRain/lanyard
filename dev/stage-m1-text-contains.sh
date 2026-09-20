#!/bin/zsh
# Preserve text byte lengths before checking substring search.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-text-length.sh
_build/default/test/lan_text_contains.exe
python3 -P test/lan_text_contains.py
python3 -P test/lan_text_contains.py --mutations
zsh dev/house.sh
print -r -- 'STAGE-M1-TEXT-CONTAINS OK'
