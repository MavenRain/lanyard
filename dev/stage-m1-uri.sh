#!/bin/zsh
# Retain the text gate before checking text-derived redirects.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-text.sh
_build/default/test/lan_uri.exe
python3 -P test/lan_uri.py
python3 -P test/lan_uri_mutations.py
print -r -- 'STAGE-M1-URI OK'
