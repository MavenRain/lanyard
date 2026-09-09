#!/bin/zsh
# The Stage C battery retains the target pin and carried kernel checks.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
ROOT=${0:A:h}/..
cd $ROOT
zsh dev/stage-b.sh
zsh dev/r0-target.sh
_build/default/test/sl_surface.exe
_build/default/test/main.exe test
_build/default/bin/lanyard.exe check examples/m0-todo.lan
python3 -P test/lanyard_cli.py
print -r -- 'STAGE-C OK'
