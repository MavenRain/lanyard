#!/bin/zsh
# Check the catalog with the kernel, including adversarial target rows.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
ROOT=${0:A:h}/..
python3 -P $ROOT/dev/gen-target.py --check
$ROOT/_build/default/test/lan_surface.exe
print -r -- 'R0-TARGET OK'
