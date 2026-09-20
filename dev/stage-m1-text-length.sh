#!/bin/zsh
# Preserve optional form fields and persistent HTTP before text byte lengths.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-form-has.sh
_build/default/test/lan_text_length.exe
python3 -P test/lan_text_length.py
python3 -P test/lan_text_length.py --native
zsh dev/house.sh
print -r -- 'STAGE-M1-TEXT-LENGTH OK'
