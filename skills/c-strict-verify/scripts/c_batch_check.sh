#!/usr/bin/env sh
set -eu

if [ "$#" -ne 5 ]; then
  echo "usage: $0 <exe> <input-prefix> <output-prefix> <count> <suffix>" >&2
  echo "example: $0 ./a.out in01-1- out01-1- 2 txt" >&2
  exit 1
fi

exe="$1"
in_prefix="$2"
out_prefix="$3"
count="$4"
suffix="$5"
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

ok=0
ng=0

for i in $(seq 1 "$count"); do
  infile="${in_prefix}${i}.${suffix}"
  outfile="${out_prefix}${i}.${suffix}"

  if "$script_dir/c_run_io_diff.sh" "$exe" "$infile" "$outfile" >/dev/null 2>&1; then
    printf '%s [OK]\n' "$infile"
    ok=$((ok + 1))
  else
    printf '%s [NG]\n' "$infile"
    ng=$((ng + 1))
  fi
done

echo "summary: OK=$ok NG=$ng"
[ "$ng" -eq 0 ]
