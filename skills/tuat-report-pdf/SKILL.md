---
name: tuat-report-pdf
description: "TUATレポートの report.md を正本にしたまま Typst で提出用 PDF まで作る。変換スクリプトを挟んで本文と PDF の乖離を防ぎ、MS 明朝／MS ゴシックで組む。『PDFまで作って』『PDF化して』『Typstで組んで』『レポートのPDF作り直して』『フォントをMS明朝で』等で使う。Codex に DOCX/PDF を委ねる経路（tuat-report-writing）の代わりに Claude 側で完結させる時の手順。本文生成は tuat-report。"
---

# TUAT レポート PDF 化（Typst 経路・Claude 側）

## 概要

`report.md` を**正本**とし、変換スクリプト `md_to_typst.py` で Typst ソースを起こして `typst compile` する。`shared/codex-execution.md`（Codex が DOCX 経由で PDF を作る経路）と対になる、Claude 側の実行手順。

**Typst を直接書かない。** 中間レポートで正本 `report.md` と提出 PDF が乖離し、提出版が正になってしまう保守負債が実際に生じた。変換を挟めば本文を直すだけで PDF が追従する。

## 使い分け

| 状況 | 経路 |
|---|---|
| ユーザーが「PDFまであなたに」と言った | この経路（Typst） |
| DOCX 提出が要る、Word の校閲機能を使う | `tuat-report-writing`（Codex / OOXML） |
| 本文をまだ書いていない | 先に `tuat-report` |

## 前提

- `typst`（`brew install typst`）
- 図を作るなら作業フォルダの `.venv` に matplotlib（`requirements.txt` 経由）
- MS 明朝／MS ゴシックを使うなら Office 導入済みであること → `references/fonts.md`

## 手順

1. **本文を確定させる。** `report.md` が正本。以降、`report.typ` を手で編集しない（変換のたびに消える）。
2. **フォントを用意する。** 初回のみ。`references/fonts.md` の導入手順。
3. **変換スクリプトを作業フォルダに置いて調整する。** `assets/md_to_typst.py` を写し、冒頭の `EQUATIONS`（数式の対応表）と `PREAMBLE` 内の表紙（科目名・テーマ・担当教員・提出日・学籍番号・氏名）をそのレポートに合わせる。
4. **図を作る。** `make_figures.py`。図中の日本語は本文と字種を揃える（本文が明朝なら図はゴシック）。
5. **組む。** `python md_to_typst.py && typst compile report.typ <学籍番号>_<課題名>.pdf`
6. **検算する。** 下の「提出前の検算」を全部通す。
7. **梱包する。** 再現に要るファイルだけを zip に入れ、**展開した副本だけで** ビルド・検証・PDF 再生成が通ることを確かめる。

## 変換で要る工夫

いずれも `assets/md_to_typst.py` に実装済み。写して使うなら中身を読んでから直す。

- **数式**：LaTeX から Typst 構文へ、`\tag{n}` の番号をキーにした対応表で写す。`#set math.equation(numbering: "(1)")` の自動採番と文書順が一致するかを変換時に検査し、ずれたら終了する。番号を手で書かないので採番ミスが起きない。
- **表**：`#figure(kind: table)` にして `figure.caption(position: top)` でキャプションを上に置く。`#show figure: set block(breakable: true)` を併せると、長い表でキャプションだけが前ページに取り残されない。
- **図幅**：PNG の IHDR を読んで縦横比で振り分ける（横長の2枚組は 96%、単独図は 76%）。Pillow に依存しない。
- **エスケープ**：Typst マークアップの特殊文字 `\#$*_`<>@[]~` を退避する。特に `α_build` の `_`、参考文献の `[1]`、`#define` の `#` が壊れやすい。インラインコードと太字だけは退避対象から外す。
- **改ページ**：章頭で `#pagebreak(weak: true)`。ただし付録は参考文献に続けて置く（数行のために1ページ使わない）。

## フォント

既定は次の組合せ。理由と導入手順と落とし穴は `references/fonts.md`。

| 用途 | フォント |
|---|---|
| 本文の和文 | MS 明朝 |
| 見出し・表紙・図・コード内の和文 | MS ゴシック |
| 欧文 | Times New Roman |
| 数式と `⌈ ⌉ ⌊ ⌋` | New Computer Modern Math |

**MS 明朝は固定ピッチなので、欧文まで任せると地の文がタイプライター体になる。**必ず欧文用フォントを先頭に置く。Word の日本語文書の既定は欧文が Century、和文誌のテンプレートは Times New Roman。どちらもユーザーに選ばせる。

## 提出前の検算

「できた」と書く前に全部通す。出力を本文に貼る。

1. **フォント検算** — `pdffonts <pdf>` の一覧に、意図したフォントだけが並ぶこと。**知らない名前が出ていたら代替フォントに落ちている**（特に `SIL-Hei-*` は簡体字中国語、`Osaka` は macOS の代替）。`scripts/pdf_font_census.py` でどの文字がどのフォントで描かれたか数えられる。
2. **字形の欠け** — `scripts/font_coverage.py` で、本文に出る文字が指定フォントに全部あるか調べる。無い文字は代替に落ちるので、代替先を明示するか字面を変える。
3. **図の警告** — `make_figures.py` を実行して `Glyph ... missing` の警告が出ないこと。
4. **キャプションの分離・端物ページ** — 各ページの末尾行が「表n」「図n」で終わっていないか、3行以下のページが無いかを機械的に見る（表の継続は誤検出するので目視で確認する）。
5. **自己完結性** — zip を清潔なディレクトリに展開し、そこだけでテストが通ること。
6. **PDF の再現性** — 展開した副本で `md_to_typst.py` → `typst compile` を回し、`pdftotext` の出力が提出 PDF と一致すること。**これが通らないなら、正本と提出物が既に乖離している。**

## 同梱物

zip には再現に要るものだけ入れる。入れないもの：`.venv`、`__pycache__`、`*.dSYM`、ビルド済みバイナリ、生成した巨大入力、`.fontcache`、`plan.md` や監査依頼などの作業メモ、PDF 本体。

フォントファイルは同梱しない。README にフォントの条件を書き、導入されていない環境では代替に切り替わること（内容は変わらないこと）を明記する。

## 資産

- `assets/md_to_typst.py` — 変換スクリプトの実装例。写して調整する。
- `scripts/pdf_font_census.py` — PDF 内でどのフォントがどの文字を描いたかを数える。代替フォント混入の特定に使う。
- `scripts/font_coverage.py` — 指定フォントに字形が無い文字を本文から洗い出す。
- `references/fonts.md` — MS フォントの導入、埋め込み可否の確認、3つの落とし穴。

## 科目フォルダへの追記

処理し終えたら、固定値・ファイル名規則・締切・効いた工夫を科目ごとのメモに残し、次回はそれを読んでから着手する。`tuat-report` スキルと併用しているなら `shared/courses/<科目名>/<回>.md` が置き場所。
