#!/usr/bin/env sh
set -eu

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <file1.c> [file2.c ...]" >&2
  exit 1
fi

CC_CMD="${CC:-cc}"
CFLAGS="${CFLAGS:--Wall -Wextra -Werror}"
# 最適化レベル違いのバイナリを並べて作るときに使う（例: OUT_SUFFIX=.O2）
OUT_SUFFIX="${OUT_SUFFIX:-}"

for src in "$@"; do
  case "$src" in
    *.c) ;;
    *)
      echo "skip (not .c): $src" >&2
      continue
      ;;
  esac

  out="${src%.c}${OUT_SUFFIX}"
  echo "[BUILD] $src -> $out"
  # shellcheck disable=SC2086
  "$CC_CMD" $CFLAGS "$src" -o "$out"
done
