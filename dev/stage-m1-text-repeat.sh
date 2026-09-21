#!/bin/zsh
# Preserve replacement checks before checking text repetition.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-text-replace.sh
_build/default/test/lan_text_repeat.exe
python3 -P test/lan_text_repeat.py
python3 -P test/lan_text_repeat.py --mutations
zsh dev/house.sh
print -r -- 'STAGE-M1-TEXT-REPEAT OK'
