#!/bin/zsh
# Preserve request URI behavior before checking shared scripted sessions.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-uri-text.sh
_build/default/test/lan_session.exe
python3 -P test/lan_session.py
python3 -P test/lan_session_mutations.py
print -r -- 'STAGE-M1-SESSION OK'
