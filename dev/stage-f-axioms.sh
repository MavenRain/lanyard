#!/bin/zsh
# Classified disclosure retains the complete Todo gate.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-e-todo.sh
python3 -P test/lan_axioms.py
_build/default/test/lan_axioms_report.exe
python3 -P test/lan_axioms_mutations.py
_build/default/bin/lanyard.exe axioms corpus/m0/todo.lan
print -r -- 'STAGE-F-AXIOMS OK'
