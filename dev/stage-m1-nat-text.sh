#!/bin/zsh
# Retain the concat gate before checking natural-number text and Todo links.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-concat.sh
_build/default/test/lan_nat_text.exe
python3 -P test/lan_nat_text.py
python3 -P test/lan_nat_text_database.py --interpreter
python3 -P test/lan_nat_text.py --mutations
print -r -- 'STAGE-M1-NAT-TEXT OK'
