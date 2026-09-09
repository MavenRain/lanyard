#!/bin/zsh
# The Stage B gate command. Later stages retain these checks when composing M0.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
ROOT=${0:A:h}/..
cd $ROOT
zsh dev/dunecho.sh build
python3 -P dev/gen-target.py --check
zsh dev/target-pin.sh
python3 -P test/target.py
_build/default/test/target_catalog.exe
zsh dev/kernel-carry.sh
zsh dev/r0-count.sh
zsh dev/trusted-lines.sh
zsh dev/house.sh
print -r -- 'STAGE-B OK'
