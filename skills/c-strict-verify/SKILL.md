---
name: c-strict-verify
description: C言語のコードを厳格コンパイル（-Wall -Wextra -Werror）→サンプル入出力の一致確認→サニタイザ（ASan/UBSan）と -O2 での再照合→判定スクリプト実行の順で検証する。『Cのコード見て』『コンパイル通して』『サンプル入出力が合うか確認して』『check.sh を回して』のように、*.c の実装・レビュー・検証を頼まれたときに使う。課題・演習・競技プログラミング形式の一括テストが対象。
---

# c-strict-verify — C コードを厳格に通して検証する

実装を読む前にコンパイルを通し、通ってから入出力を照合し、最後に判定スクリプトを回す。**この順序を崩さない**のが要点で、逆順にやると「出力が違う」の原因がロジックなのか未定義動作なのか切り分けられなくなる。

## 手順

| # | やること | コマンド |
|---|---|---|
| 1 | 対象ファイルの発見 | `rg --files -g '*.c' -g '*.h' -g '*.sh'` |
| 2 | 実装を読む（**編集より先**）| `nl -ba <file>` |
| 3 | 厳格コンパイル | `scripts/c_build_strict.sh` |
| 4 | サンプル入出力の照合 | `scripts/c_run_io_diff.sh` / `c_batch_check.sh` |
| 5 | サニタイザ付きで同じ照合 | `scripts/c_build_sanitize.sh` → `<name>.san` で 4 を再実行 |
| 6 | 最適化レベル違いで同じ照合 | `OUT_SUFFIX=.O2 CFLAGS="... -O2"` で 4 を再実行 |
| 7 | 判定スクリプト | `./check.sh <binary>` |
| 8 | 報告 | 下の「報告の規律」に従う |

## 1. 読む

編集の前に必ず読む。確認するのは**アルゴリズムの前提**であって、文法ではない。

- 未完成のロジック（`TODO`、return 漏れ、確保結果を検査しない `malloc`、境界を見ない入力）
- 前提条件（二分探索なら**入力がソート済みであること**、添字が0始まりか1始まりか、見つからない場合の戻り値）
- 使用APIに対応するヘッダ（`string.h`、`limits.h` など）

前提条件は明文化されていないことが多い。**読み取った前提は報告に書く。**

## 2. 実装・修正

- 既存の入出力フォーマットを**1文字も変えない**。判定スクリプトは文字列一致で見ている
- 見つからない場合・エラーの場合の戻り値は、暗黙の値に頼らず明示する
- 探索・整列系は、入力の前提をコメントに残す

## 3. 厳格コンパイル

```bash
scripts/c_build_strict.sh q1.c q2.c q3.c
```

`-Wall -Wextra -Werror` で通す。**警告を残したまま次に進まない。** C は警告が出ている状態で「動いて見える」ことが普通にあり、その状態で入出力を照合しても切り分けにならない。

- 出力バイナリ名は既定でソースの拡張子なし
- コンパイラは `CC=clang` / `CC=gcc` で切り替え

## 4. サンプル入出力の照合

1件だけなら `c_run_io_diff.sh`、連番のテストなら `c_batch_check.sh`。

```bash
# 単体: バイナリ / 入力 / 期待出力
scripts/c_run_io_diff.sh ./q1 in1.txt out1.txt

# 一括: バイナリ / 入力の接頭辞 / 期待出力の接頭辞 / 件数 / 拡張子
scripts/c_batch_check.sh ./q1 in1- out1- 2 txt
```

`[OK] / [NG]` で一覧が出る。**NG が出たら3に戻る**（実装を直したら必ずコンパイルからやり直す）。

## 5. サニタイザ付きで同じ照合を回す

**`-Wall -Wextra -Werror` を通っても、未定義動作が無いことにはならない。** 警告はコンパイル時に分かるものしか拾わず、範囲外アクセス・符号付き整数のオーバーフロー・ゼロ除算・解放後使用の多くは実行してみるまで出ない。しかも未定義動作を踏んだプログラムは、手元のサンプルでは期待どおりの出力を返すことが普通にある。

```bash
scripts/c_build_sanitize.sh q1.c          # q1.san ができる
scripts/c_batch_check.sh ./q1.san in1- out1- 2 txt
scripts/c_run_io_diff.sh ./q1.san in1.txt out1.txt   # NG の詳細（runtime error の行番号）はこちらで見る
```

- `-fsanitize=address,undefined -fno-sanitize-recover=all` で組む。UBSan は既定では報告だけして実行を続けるので、`-fno-sanitize-recover=all` を付けないと照合が `[OK]` のまま通る
- `c_batch_check.sh` は標準エラーを捨てる。`[NG]` が出たら `c_run_io_diff.sh` で単体実行し、`runtime error:` の行を読む
- リンク時に `libclang_rt.asan` などが見つからないと言われたら、そのコンパイラにサニタイザのランタイムが入っていない。`CC=gcc` に切り替えるか、UBSan だけに絞る（`SAN_FLAGS="-fsanitize=undefined -fno-sanitize-recover=all -g -O1"`）。どちらも通らなければ、5 を実施できなかったと報告に書く
- AddressSanitizer の実行時コストは平均で約1.7倍の時間・約3.4倍のメモリ（Serebryany et al. 2012）。サンプル入出力の規模なら問題にならないが、時間制限つきの判定スクリプトには通常ビルドを渡す

実際に確かめた例（gcc 13）：入力 `n` に対して `int x = INT_MAX; x += n;` を実行するコードは、厳格フラグでも警告ゼロで通り、通常ビルドは `n=3` で終了コード0のまま `-2147483646` を出力した。`.san` ビルドは `runtime error: signed integer overflow` で終了コード1になった。

## 6. 最適化レベルを変えて同じ照合を回す

未定義動作を含むコードは、`-O0` で動いて `-O2` で壊れることがある。コンパイラは「未定義動作は起きない」と仮定して最適化するので、オーバーフロー検査やヌル検査が丸ごと消される（Wang et al. 2013 はこの種のコードで160件の新規バグを報告している）。提出環境の最適化レベルが分からないなら、両方で照合する。

```bash
OUT_SUFFIX=.O2 CFLAGS="-Wall -Wextra -Werror -O2" scripts/c_build_strict.sh q1.c   # q1.O2 ができる
scripts/c_batch_check.sh ./q1.O2 in1- out1- 2 txt
```

`-O0` と `-O2` で結果が割れたら、ロジックより先に未定義動作を疑う。5 のサニタイザで場所を特定する。

## 7. 判定スクリプト

課題に `check.sh` が付いている場合は、自前の照合より**そちらを正とする**。

```bash
./check.sh ./q1
```

判定スクリプトが無い場合のみ、4〜6の一括チェックを最終確認とする。

## 報告の規律

- **指摘を先に、深刻度順に並べる。** 何をしたかの経過報告を先頭に置かない
- 指摘には必ずファイル名と行番号を付ける
- **実際に実行したコンパイル・テストのコマンドを書く。** 実行していないものを書かない
- サニタイザ・最適化レベル違いの照合を**やらなかった場合は、やらなかったと書く。** 「厳格コンパイルとサンプル照合が通った」は「未定義動作が無い」を意味しない
- 全部通った場合は、通ったことを明示したうえで**残った前提**を書く（例：「ソート済み入力を前提にしている。未ソートでは誤答する」）

通ったことの報告より、**残存リスクの報告のほうが価値が高い。**

## 同梱物

### scripts/

| ファイル | 役割 |
|---|---|
| `c_build_strict.sh` | 複数の `.c` を厳格フラグでコンパイル。`OUT_SUFFIX` で出力名に接尾辞を付ける |
| `c_build_sanitize.sh` | ASan + UBSan 付きでコンパイルし `<name>.san` を出す |
| `c_run_io_diff.sh` | 1バイナリ×1入力を実行し期待出力と比較 |
| `c_batch_check.sh` | 連番の入出力ペアを一括実行し `[OK]/[NG]` を集計 |

### references/

- `c-review-checklist.md` — 実装レビューと検証のチェックリスト（正当性・安全性・ビルド）

## 根拠文献

- Wang, Chen, Cheung, Jia, Zeldovich, Kaashoek. *Undefined Behavior: What Happened to My Code?* APSys 2012. 現行のコンパイラは未定義動作に起因する最適化を警告できず、GCC は `-O0` でも一部のヌル検査を除去する
- Wang, Zeldovich, Kaashoek, Solar-Lezama. *Towards Optimization-Safe Systems: Analyzing the Impact of Undefined Behavior.* SOSP 2013. `-O0` で動き `-O2` で壊れる「最適化不安定コード」を定義し、静的検査器 STACK で160件の新規バグを検出
- Serebryany, Bruening, Potapenko, Vyukov. *AddressSanitizer: A Fast Address Sanity Checker.* USENIX ATC 2012. 平均73%の速度低下・3.4倍のメモリで、ヒープ・スタック・グローバルの範囲外アクセスと解放後使用を発生時点で検出
