#!/bin/zsh
# Retain the cumulative compiler checks and measure M0 once, at the end.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-f-axioms.sh
python3 -P test/lan_bench.py
python3 -P test/lan_trusted_inventory.py
python3 -P test/lan_m0_gates.py
python3 -P test/lan_m0_e2e.py
python3 -P test/lan_m0_gate_mutations.py
code=0
# The scratch log lives under .gatework, like the gate report directories, so
# the stage never depends on the system temp directory. The trap removes it
# when the stage exits.
mkdir -p .gatework
log=$(mktemp .gatework/stage-f-gates.XXXXXX)
trap 'rm -f $log' EXIT
# Save the gate stdout, then reprint every row in order. The verdict comes
# from report.json, because a replayed child row can carry gate marker text.
zsh dev/gates.sh M0 > $log || code=$?
cat $log
if [[ $code -ne 2 ]]; then
  print -r -- "STAGE-F-GATES FAIL: expected the unresolved M0 ruling, exit=$code"
  exit 1
fi
if ! python3 -P dev/m0-gates.py --verify-stage-log $log; then
  print -r -- 'STAGE-F-GATES FAIL: the M0 report does not hold the pending ruling'
  exit 1
fi
print -r -- 'STAGE-F-GATES OK m0=PENDING'
