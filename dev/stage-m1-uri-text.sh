#!/bin/zsh
# Retain exact text comparison before checking request URI inspection.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
stage_tmp=$(mktemp -d "${TMPDIR:-/tmp}/lanyard-uri-text.XXXXXX")
trap 'rm -rf -- "$stage_tmp"' EXIT
git init --quiet "$stage_tmp"
export TMPDIR="$stage_tmp"
zsh dev/stage-m1-text-equal.sh
_build/default/test/lan_uri_text.exe
python3 -P test/lan_uri_text.py
python3 -P test/lan_uri_text_mutations.py
print -r -- 'STAGE-M1-URI-TEXT OK'
