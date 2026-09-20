#!/bin/zsh
# Preserve persistent HTTP behavior before checking URI path and query adapters.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-database.sh
_build/default/test/lan_uri_parts.exe
python3 -P test/lan_uri_parts.py
mkdir -p .gatework
parts_work=$(mktemp -d "$PWD/.gatework/uri-parts.XXXXXX")
trap 'rm -rf -- "$parts_work"' EXIT
trap 'rm -rf -- "$parts_work"; exit 130' INT
trap 'rm -rf -- "$parts_work"; exit 143' TERM HUP
parts_target=${CARGO_TARGET_DIR:-$PWD/.gatework/http-target}
parts_target=${parts_target:A}
python3 -P test/lan_uri_parts.py --prepare "$parts_work/native" \
  --toasty "${LANYARD_TOASTY:-$PWD/../toasty}" \
  --topcoat "${LANYARD_TOPCOAT:-$PWD/../topcoat}" \
  --lock dev/validation/stage-m1-uri-text/native/Cargo.lock
gateledger run --ledger "$PWD/.gatework/gateledger" --dir "$parts_work/native" \
  --toolchain "${RUSTUP_TOOLCHAIN:-stable}" -- \
  cargocho build -- --offline --locked --bins \
  --manifest-path "$parts_work/native/Cargo.toml" --target-dir "$parts_target" --jobs 2
python3 -P test/lan_uri_parts.py --check "$parts_target/debug"
zsh dev/house.sh
print -r -- 'STAGE-M1-URI-PARTS OK'
