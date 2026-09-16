#!/bin/zsh
# Retain the response gate before checking HTML output.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-response.sh
_build/default/test/lan_html.exe
python3 -P test/lan_html.py
python3 -P test/lan_html_mutations.py
print -r -- 'STAGE-M1-HTML OK'
