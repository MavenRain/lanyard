#!/bin/zsh
# Retain the URI gate before checking explicit form fields and request bodies.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-uri.sh
_build/default/test/lan_form.exe
python3 -P test/lan_form.py
python3 -P test/lan_form_mutations.py
print -r -- 'STAGE-M1-FORM OK'
