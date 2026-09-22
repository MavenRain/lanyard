#!/bin/zsh
# Preserve directional trimming checks before checking ASCII case conversion.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-text-trim.sh
_build/default/test/lan_text_ascii.exe
python3 -P test/lan_text_ascii.py
python3 -P test/lan_text_ascii.py --mutations
zsh dev/house.sh
print -r -- 'STAGE-M1-TEXT-ASCII OK'
