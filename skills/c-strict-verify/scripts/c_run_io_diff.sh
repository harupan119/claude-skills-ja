#!/usr/bin/env sh
set -eu

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <exe> <input.txt> <expected.txt>" >&2
  exit 1
fi

exe="$1"
infile="$2"
expected="$3"

tmp_out="$(mktemp)"
trap 'rm -f "$tmp_out"' EXIT

"$exe" < "$infile" > "$tmp_out"
if diff -u "$expected" "$tmp_out"; then
  echo "[OK] $infile"
else
  echo "[NG] $infile" >&2
  exit 1
fi
