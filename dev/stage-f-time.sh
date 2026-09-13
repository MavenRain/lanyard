#!/bin/zsh
# Timing retains the complete classified-axioms gate.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-f-axioms.sh
python3 -P test/lan_bench.py
mkdir -p .gatework
work=$(mktemp -d .gatework/stage-f-time.XXXXXX)
python3 -P dev/bench.py --refit-go --output "$work/timings.json"
print -r -- "M0-TIME-RAW $work/timings.json"
print -r -- 'STAGE-F-TIME OK'
