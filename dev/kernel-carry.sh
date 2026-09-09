#!/bin/zsh
# dev/kernel-carry.sh
# The KERNEL-CARRY leg (Stage A, gate SA-G6, brief section 3.3).
# Example:
#   zsh /Users/oobi/Documents/lanyard/dev/kernel-carry.sh
#
# The leg reads the D-M0-5 table of dev/KERNEL-CARRIED.md and re-diffs
# every row against the kanon commit the row names, which is the fork
# point 046689a78ef6708404bd190dc86845cbee0bb36f.  It prints one row per
# file, then the row count, then KERNEL-CARRY OK and exit 0, or the
# differing rows and KERNEL-CARRY FAIL and exit 1.
#
# A row fails when:
#   the file is gone;
#   the row names a commit that is not the fork point;
#   a VERBATIM row differs from the fork point by one byte;
#   a VERBATIM row carries a reason, which only an EDITED row takes;
#   an EDITED row is identical to the fork point;
#   an EDITED row gives no reason;
#   the state word is neither VERBATIM nor EDITED.
# The bucket leg fails when a file that dev/trusted-lines.sh reads has no
# row in the table, or when that bucket is not the twelve files of
# correction S1-F1, or when lib/erase.ml has no row.
#
# SA-D7 of the carried dev/carry-check.sh holds here too: the root comes
# from this script's own path, so a copy of the repository under a
# scratch directory checks itself.  git, rg, awk, diff and wc do the
# reading;  grep, sed and find are never called.

set -u

# The user shell startup files add a chpwd hook that reads an unset
# parameter.  Under set -u that hook fails, so the hooks are cleared.
chpwd_functions=()
unfunction chpwd 2>/dev/null

ROOT=${0:A:h}/..
LEDGER=$ROOT/dev/KERNEL-CARRIED.md
TRUSTED=$ROOT/dev/trusted-lines.sh
PIN=046689a78ef6708404bd190dc86845cbee0bb36f
BUCKET_SIZE=12

# The work directory sits under the repository root, not under the system
# temp directory, so the script needs no writable path outside the tree it
# checks.  .gitignore holds it.
WORK=$ROOT/.gatework/kernel-carry
rm -rf $WORK
mkdir -p $WORK

fail=0
rows=0
seen=""

if [[ ! -f $LEDGER ]]; then
  print -r -- "KERNEL-CARRY ledger MISSING $LEDGER"
  print -r -- "KERNEL-CARRY FAIL"
  exit 1
fi

rg -N '^\| lib/' -- $LEDGER > $WORK/rows

while IFS= read -r row; do
  file=$(print -r -- "$row" | awk -F'|' '{gsub(/^ +| +$/, "", $2); print $2}')
  commit=$(print -r -- "$row" | awk -F'|' '{gsub(/^ +| +$/, "", $3); print $3}')
  state=$(print -r -- "$row" | awk -F'|' '{gsub(/^ +| +$/, "", $4); print $4}')
  reason=$(print -r -- "$row" | awk -F'|' '{gsub(/^ +| +$/, "", $5); print $5}')
  rows=$((rows + 1))
  seen="$seen $file"

  if [[ ! -f $ROOT/$file ]]; then
    print -r -- "KERNEL-CARRY $file $commit $state MISSING FAIL"
    fail=1
    continue
  fi

  # The row names its own commit and the leg resolves it, so a row that
  # points away from the fork point cannot pass by naming another tree.
  got=$(git -C $ROOT rev-parse --verify --quiet "$commit^{commit}" 2>/dev/null)
  if [[ $got != $PIN ]]; then
    print -r -- "KERNEL-CARRY $file $commit resolved=$got expected=$PIN FAIL"
    fail=1
    continue
  fi

  if ! git -C $ROOT show $commit:$file > $WORK/orig 2>/dev/null; then
    print -r -- "KERNEL-CARRY $file $commit ORIGIN-MISSING FAIL"
    fail=1
    continue
  fi

  d=$(diff $WORK/orig $ROOT/$file | /usr/bin/wc -l | tr -d ' ')
  lines=$(/usr/bin/wc -l < $ROOT/$file | tr -d ' ')

  verdict=FAIL
  note=""
  case $state in
    VERBATIM)
      if [[ $d -eq 0 && $reason == '-' ]]; then
        verdict=OK
      fi
      if [[ $d -ne 0 ]]; then
        note="$note bytes-differ"
      fi
      if [[ $reason != '-' ]]; then
        note="$note reason-on-verbatim"
      fi
      ;;
    EDITED)
      if [[ $d -gt 0 && -n $reason && $reason != '-' ]]; then
        verdict=OK
      fi
      if [[ $d -eq 0 ]]; then
        note="$note no-edit-found"
      fi
      if [[ -z $reason || $reason == '-' ]]; then
        note="$note reason-missing"
      fi
      ;;
    *)
      note="$note unknown-state"
      ;;
  esac

  print -r -- "KERNEL-CARRY $file $commit $state diff=$d lines=$lines $verdict$note"
  if [[ $verdict != OK ]]; then
    fail=1
  fi
done < $WORK/rows

# The bucket leg.  Every file the TRUSTED-LINES kernel bucket reads needs
# a row here, so the kernel cannot grow a file that no row re-diffs.
if [[ ! -f $TRUSTED ]]; then
  print -r -- "KERNEL-CARRY bucket $TRUSTED MISSING FAIL"
  fail=1
else
  rg -N '^[[:space:]]*\$root/lib/[a-z_]+\.ml[[:space:]]*$' -- $TRUSTED \
    | awk '{ gsub(/^[ \t]+|[ \t]+$/, ""); sub(/^\$root\//, ""); print }' \
    > $WORK/bucket
  bucket=$(/usr/bin/wc -l < $WORK/bucket | tr -d ' ')

  if [[ $bucket -eq $BUCKET_SIZE ]]; then
    print -r -- "KERNEL-CARRY bucket files=$bucket expected=$BUCKET_SIZE OK"
  else
    print -r -- "KERNEL-CARRY bucket files=$bucket expected=$BUCKET_SIZE FAIL"
    fail=1
  fi

  while IFS= read -r member; do
    if [[ " $seen " != *" $member "* ]]; then
      print -r -- "KERNEL-CARRY bucket $member NO-ROW FAIL"
      fail=1
    fi
  done < $WORK/bucket
fi

# lib/erase.ml is the thirteenth trusted file of S0-D1 and it is not in
# the twelve file bucket, so the leg asks for its row by name.
if [[ " $seen " != *" lib/erase.ml "* ]]; then
  print -r -- "KERNEL-CARRY lib/erase.ml NO-ROW FAIL"
  fail=1
fi

rm -rf $WORK

print -r -- "KERNEL-CARRY rows=$rows"

if [[ $fail -eq 0 ]]; then
  print -r -- "KERNEL-CARRY OK"
  exit 0
fi
print -r -- "KERNEL-CARRY FAIL"
exit 1
