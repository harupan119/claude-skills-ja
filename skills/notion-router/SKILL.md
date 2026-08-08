---
name: notion-router
description: "Notion関連タスクの入り口となる統括スキル。『PDFをNotionに取り込みやすくして』『PDFの図をNotionに挿入して』『mdをNotionに送って』のように、PDF/Markdown/Notionが絡む依頼を受けたら、まずここで下位スキルの使い分けを確認する。下位スキル: notion-pdf-split（PDF事前分割）／notion-figure-insert（図の抽出・本文挿入）／notion-markdown（本文のMarkdown変換・ページ作成）。"
---

# notion-router — Notion 系スキルの振り分け

Notion関連の下位スキルをどう使い分けるかをまとめる上位スキル。実処理はそれぞれの下位スキルに委ねる。

## 使い分け

| やりたいこと | 呼ぶスキル |
|---|---|
| PDFが大きすぎる／表紙等が邪魔でNotionに取り込みにくいので、事前にページを間引く・分割する | `notion-pdf-split` |
| PDF中のグラフ・図表・写真を切り出して、対応するNotionページ本文の該当箇所に挿入する | `notion-figure-insert` |
| Markdown本文をNotionページにする（既存 `.md` の送信、またはNotion用に本文を書く） | `notion-markdown` |

3つは扱う対象が異なる（PDFファイル自体の前処理 vs 本文への画像挿入 vs 本文テキストのページ化）ので重なりはない。1つのタスクで複数必要になることもある（例: 巨大PDFを分割し、本文を`.md`で書いてページ化し、そこへ図を挿入する）が、その場合も呼び出し順を明示するだけで、統合処理は行わない。

典型的な順序は `notion-markdown`（本文をページ化） → `notion-figure-insert`（そのページへ図を挿入）。

## 各スキルの前提

- `notion-pdf-split`: ローカルPDFのみを扱う。Notion APIは呼ばない。`pypdf` が必要。
- `notion-figure-insert`: `mcp__notion__*`（ページ読み書き）と `mcp__google-multi__drive_*`（画像ホスティング用の中継、Notionに直接ファイルアップロードするAPIが無いため）を使う。poppler・ImageMagickが必要。
- `notion-markdown`: `mcp__notion__*` のみ。ヘルパー `scripts/md2notion.py` は標準ライブラリだけで動く。

## 新しいNotion系スキルを追加するとき

このスキルの表に一行追加する。既存スキルとの機能重複がないか（PDF加工 vs 本文編集 vs 検索 等、関心の軸で見る）を確認してから追加する。
