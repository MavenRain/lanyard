#!/bin/zsh
# Preserve HTTP behavior before testing the serve process boundary.
set -eu
chpwd_functions=()
unfunction chpwd 2>/dev/null || true
cd ${0:A:h}/..
zsh dev/stage-m1-http.sh
python3 -P test/lan_serve.py
mkdir -p .gatework
serve_work=$(mktemp -d "$PWD/.gatework/serve.XXXXXX")
trap 'rm -rf -- "$serve_work"' EXIT
trap 'rm -rf -- "$serve_work"; exit 130' INT
trap 'rm -rf -- "$serve_work"; exit 143' TERM HUP
serve_target=${CARGO_TARGET_DIR:-$PWD/.gatework/http-target}
serve_target=${serve_target:A}
python3 -P dev/prepare-crate.py --output "$serve_work/seed" \
  --source test/fixtures/todo-session.lan --listen 127.0.0.1:0 \
  --toasty "${LANYARD_TOASTY:-$PWD/../toasty}" \
  --topcoat "${LANYARD_TOPCOAT:-$PWD/../topcoat}" \
  --lock dev/validation/stage-m1-http/Cargo.lock
gateledger run --ledger "$PWD/.gatework/gateledger" --dir "$PWD" \
  --toolchain "${RUSTUP_TOOLCHAIN:-stable}" -- \
  python3 -P test/lan_serve_native.py --seed "$serve_work/seed" --target "$serve_target"
zsh dev/house.sh
print -r -- 'STAGE-M1-SERVE OK'
