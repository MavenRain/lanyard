#!/bin/zsh
# Preserve boundary matching before checking replacement semantics.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-text-boundaries.sh
_build/default/test/lan_text_replace.exe
python3 -P test/lan_text_replace.py
python3 -P test/lan_text_replace.py --mutations
zsh dev/house.sh
print -r -- 'STAGE-M1-TEXT-REPLACE OK'
