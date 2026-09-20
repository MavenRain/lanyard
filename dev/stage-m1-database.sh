#!/bin/zsh
# Retain serve behavior before checking optional persistent SQLite storage.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-serve.sh
python3 -P test/lan_database.py
database_target=${CARGO_TARGET_DIR:-$PWD/.gatework/http-target}
database_target=${database_target:A}
gateledger run --ledger "$PWD/.gatework/gateledger" --dir "$PWD" \
  --toolchain "${RUSTUP_TOOLCHAIN:-stable}" -- \
  python3 -P test/lan_database_native.py --target "$database_target" \
  --toasty "${LANYARD_TOASTY:-$PWD/../toasty}" \
  --topcoat "${LANYARD_TOPCOAT:-$PWD/../topcoat}"
zsh dev/house.sh
print -r -- 'STAGE-M1-DATABASE OK'
