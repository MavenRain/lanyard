#!/bin/zsh
# Retain the natural-number formatting gate before checking decimal parsing.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
# Native ledger scopes need a Git root; mutant Dune projects need no parent
# Dune project. The system temporary directory provides both boundaries.
stage_tmp=$(mktemp -d "${TMPDIR:-/tmp}/lanyard-text-nat.XXXXXX")
trap 'rm -rf -- "$stage_tmp"' EXIT
git init --quiet "$stage_tmp"
export TMPDIR="$stage_tmp"
zsh dev/stage-m1-nat-text.sh
_build/default/test/lan_text_nat.exe
python3 -P test/lan_text_nat.py
python3 -P test/lan_text_nat_database.py --interpreter
python3 -P test/lan_text_nat.py --mutations
print -r -- 'STAGE-M1-TEXT-NAT OK'
