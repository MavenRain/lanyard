#!/bin/zsh
# Retain interpreted sessions, then compile and execute the native cases.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-session.sh
python3 -P test/lan_native_session.py
mkdir -p .gatework
session_work=$(mktemp -d "$PWD/.gatework/native-session.XXXXXX")
trap 'rm -rf -- "$session_work"' EXIT
trap 'rm -rf -- "$session_work"; exit 130' INT
trap 'rm -rf -- "$session_work"; exit 143' TERM HUP
session_target=${CARGO_TARGET_DIR:-$PWD/.gatework/native-session-target}
session_target=${session_target:A}
python3 -P test/lan_native_session.py --prepare "$session_work/crates" \
  --toasty "${LANYARD_TOASTY:-$PWD/../toasty}" \
  --topcoat "${LANYARD_TOPCOAT:-$PWD/../topcoat}" \
  --lock dev/validation/stage-m1-uri-text/native/Cargo.lock
gateledger run --ledger "$PWD/.gatework/gateledger" --dir "$session_work/crates" \
  --toolchain "${RUSTUP_TOOLCHAIN:-stable}" -- \
  cargocho build -- --offline --locked --bins \
  --manifest-path "$session_work/crates/Cargo.toml" --target-dir "$session_target" --jobs 2
python3 -P test/lan_native_session.py --check "$session_target/debug"
print -r -- 'STAGE-M1-NATIVE-SESSION OK'
