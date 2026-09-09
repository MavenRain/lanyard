#!/bin/zsh
# dev/trusted-lines.sh [ROOT]
# The TRUSTED-LINES leg of the gate battery, in its M0 Stage A form.
# Example:
#   zsh /Users/oobi/Documents/lanyard/dev/trusted-lines.sh
#
# The trust base of a checked file is the kernel.  The kernel is the
# twelve files this script reads:  shape.ml, term.ml, rules.ml, check.ml,
# value.ml, eval.ml, conv.ml, totality.ml, positivity.ml, global.ml,
# order.ml and bignum.ml.  M0 holds the kernel at 4,000 lines, so the
# base stays small enough for one reader to audit. (ruling round
# 2026-09-06 (c))
#
# SA-D4: the encoder half of the pin script read wasm/gc_encode.ml.  M0
# Stage A deletes the wasm tree at the fork point, so the encoder bound
# has no file and the leg drops it.  The M0 ceiling of the whole trusted
# base is the FORMULA below:  5481 is the twelve kernel files at 3997
# plus lib/erase.ml at 1484, and A_rir, A_emit and A_sig are the three
# allowances of the files Stage D, Stage E and Stage B write.  The three
# allowances are open user rulings (S0-D1, D-M0-3), so this leg prints
# the formula and NO total, and no agent guesses a number.
#
# The leg prints three lines and exits 0:
#   TRUSTED-LINES kernel=3997/4000
#   M0 ceiling: 5481 + A_rir + A_emit + A_sig
#   TRUSTED-LINES OK
#
# SA-D7: the root comes from this script's own path when no argument is
# given, so a copy of the repository under a scratch directory measures
# itself.  wc and awk do the reading;  grep, sed and find are never
# called.

set -u

# The user shell startup files add a chpwd hook that reads an unset
# parameter.  Under set -u that hook fails, so the hooks are cleared.
chpwd_functions=()
unfunction chpwd 2>/dev/null

root=${1:-${0:A:h}/..}

kernel_bound=4000

# The M0 ceiling of the trusted base, as a formula with no total.  The
# base is 3997 kernel lines plus lib/erase.ml at 1484.
ceiling_base=5481
ceiling_line="M0 ceiling: $ceiling_base + A_rir + A_emit + A_sig"

kernel_files=(
  $root/lib/shape.ml
  $root/lib/term.ml
  $root/lib/rules.ml
  $root/lib/check.ml
  $root/lib/value.ml
  $root/lib/eval.ml
  $root/lib/conv.ml
  $root/lib/totality.ml
  # M1 Stage G, brief 3.10 and SG-D12:  the two files the mu shape adds
  # join the believed list and the budget above does not move.
  $root/lib/positivity.ml
  $root/lib/global.ml
  # M1 Stage I, brief 3.10 and SI-D15:  the file that holds the
  # structural order and the certificate joins the believed list and the
  # budget above does not move.
  $root/lib/order.ml
  # Stage K SK-D1: the arbitrary precision host boundary is believed.
  $root/lib/bignum.ml
)

# wc -l over more than one file ends with a total row, which awk reads.
kernel_out=$(wc -l $kernel_files)
kernel_code=$?

if [[ $kernel_code -ne 0 ]]; then
  print -r -- "trusted-lines: a trusted file is missing under $root"
  print -r -- "TRUSTED-LINES FAIL"
  exit 1
fi

kernel=$(print -r -- "$kernel_out" | awk 'END { print $1 }')

line="TRUSTED-LINES kernel=$kernel/$kernel_bound"

# Stage B measures the generated module; S0-D1 leaves its allowance to the user.
if [[ -d $root/target ]]; then
  generated=$root/_build/default/target/target_generated.ml
  if [[ ! -f $generated ]]; then
    print -r -- "TRUSTED-LINES FAIL: build the Stage B generated module first"
    exit 1
  fi
  signature_lines=$(wc -l < $generated | tr -d ' ')
  print -r -- "TRUSTED-LINES signature=$signature_lines allowance=A_sig (pending user ruling)"
fi

if [[ $kernel -le $kernel_bound ]]; then
  print -r -- "$line"
  print -r -- "$ceiling_line"
  print -r -- "TRUSTED-LINES OK"
  exit 0
fi

print -r -- "$line"
print -r -- "$ceiling_line"
print -r -- "TRUSTED-LINES FAIL"
exit 1
