#!/bin/zsh
# Preserve repetition checks before checking directional text trimming.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-text-repeat.sh
_build/default/test/lan_text_trim.exe
python3 -P test/lan_text_trim.py
python3 -P test/lan_text_trim.py --mutations
zsh dev/house.sh
print -r -- 'STAGE-M1-TEXT-TRIM OK'
