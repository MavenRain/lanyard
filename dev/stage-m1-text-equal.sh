#!/bin/zsh
# Retain decimal parsing before checking exact text comparison.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
stage_tmp=$(mktemp -d "${TMPDIR:-/tmp}/lanyard-text-equal.XXXXXX")
trap 'rm -rf -- "$stage_tmp"' EXIT
git init --quiet "$stage_tmp"
export TMPDIR="$stage_tmp"
zsh dev/stage-m1-text-nat.sh
_build/default/test/lan_text_equal.exe
python3 -P test/lan_text_equal.py
python3 -P test/lan_text_equal_database.py --interpreter
python3 -P test/lan_text_equal.py --mutations
print -r -- 'STAGE-M1-TEXT-EQUAL OK'
