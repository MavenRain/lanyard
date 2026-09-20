#!/bin/zsh
# Preserve URI component and persistent HTTP behavior before optional fields.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-uri-parts.sh
_build/default/test/lan_form_has.exe
python3 -P test/lan_form_has.py
mkdir -p .gatework
form_has_work=$(mktemp -d "$PWD/.gatework/form-has.XXXXXX")
trap 'rm -rf -- "$form_has_work"' EXIT
trap 'rm -rf -- "$form_has_work"; exit 130' INT
trap 'rm -rf -- "$form_has_work"; exit 143' TERM HUP
form_has_target=${CARGO_TARGET_DIR:-$PWD/.gatework/http-target}
form_has_target=${form_has_target:A}
python3 -P test/lan_form_has.py --prepare "$form_has_work/native" \
  --toasty "${LANYARD_TOASTY:-$PWD/../toasty}" \
  --topcoat "${LANYARD_TOPCOAT:-$PWD/../topcoat}" \
  --lock dev/validation/stage-m1-uri-text/native/Cargo.lock
gateledger run --ledger "$PWD/.gatework/gateledger" --dir "$form_has_work/native" \
  --toolchain "${RUSTUP_TOOLCHAIN:-stable}" -- \
  cargocho build -- --offline --locked --bins \
  --manifest-path "$form_has_work/native/Cargo.toml" --target-dir "$form_has_target" --jobs 2
python3 -P test/lan_form_has.py --check "$form_has_target/debug"
zsh dev/house.sh
print -r -- 'STAGE-M1-FORM-HAS OK'
