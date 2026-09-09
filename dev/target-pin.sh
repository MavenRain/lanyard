#!/bin/zsh
# Explicit source-root options support mutation copies without writing upstream.
set -eu
exec python3 -P ${0:A:h}/target-pin.py "$@"
