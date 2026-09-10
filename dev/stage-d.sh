#!/bin/zsh
# Rust IR, ownership, metadata and carried regression checks.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-c.sh
_build/default/test/lan_erase.exe
python3 -P test/lan_erase_cli.py
python3 -P test/lan_erase_mutations.py
print -r -- 'STAGE-D OK'
