#!/bin/zsh
# Retain native sessions before exercising the loopback HTTP adapter.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-native-session.sh
python3 -P test/lan_http.py
mkdir -p .gatework
http_work=$(mktemp -d "$PWD/.gatework/http.XXXXXX")
trap 'rm -rf -- "$http_work"' EXIT
trap 'rm -rf -- "$http_work"; exit 130' INT
trap 'rm -rf -- "$http_work"; exit 143' TERM HUP
http_target=${CARGO_TARGET_DIR:-$PWD/.gatework/http-target}
http_target=${http_target:A}
python3 -P test/lan_http.py --prepare "$http_work/crates" \
  --toasty "${LANYARD_TOASTY:-$PWD/../toasty}" \
  --topcoat "${LANYARD_TOPCOAT:-$PWD/../topcoat}" \
  --lock dev/validation/stage-m1-http/Cargo.lock
gateledger run --ledger "$PWD/.gatework/gateledger" --dir "$http_work/crates" \
  --toolchain "${RUSTUP_TOOLCHAIN:-stable}" -- \
  cargocho build -- --offline --locked --bins \
  --manifest-path "$http_work/crates/Cargo.toml" --target-dir "$http_target" --jobs 2
python3 -P test/lan_http.py --check "$http_target/debug"
print -r -- 'STAGE-M1-HTTP OK'
