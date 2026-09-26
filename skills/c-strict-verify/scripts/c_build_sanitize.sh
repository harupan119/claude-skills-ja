#!/usr/bin/env sh
set -eu

# AddressSanitizer + UndefinedBehaviorSanitizer 付きでビルドする。
# -Wall -Wextra では検出できない実行時の未定義動作（範囲外アクセス、符号付き
# 整数オーバーフロー、ゼロ除算、解放後使用）を、入出力照合の実行中に止める。
# 出力は <ソース名>.san。c_run_io_diff.sh / c_batch_check.sh にそのまま渡せる。

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <file1.c> [file2.c ...]" >&2
  exit 1
fi

CC_CMD="${CC:-cc}"
# -fno-sanitize-recover=all: UBSan は既定では報告して実行を続けるため、
# 検出した時点で非0終了させないと照合結果が [OK] のまま通ってしまう。
SAN_FLAGS="${SAN_FLAGS:--fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -g -O1}"
CFLAGS="${CFLAGS:--Wall -Wextra -Werror}"

for src in "$@"; do
  case "$src" in
    *.c) ;;
    *)
      echo "skip (not .c): $src" >&2
      continue
      ;;
  esac

  out="${src%.c}.san"
  echo "[BUILD:SAN] $src -> $out"
  # shellcheck disable=SC2086
  "$CC_CMD" $CFLAGS $SAN_FLAGS "$src" -o "$out"
done
