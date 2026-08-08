---
name: notion-figure-insert
description: PDFからグラフ・図表・写真を切り出し、対応するNotionページの本文に不足している図として挿入する。ユーザーが「PDFの図をNotionに挿入して」「グラフを切り出してページに貼って」「Notionに図が足りないから補って」のように、ローカルPDFの図版をNotionページへ反映させたいときに使う。Notion系の統括スキルは `notion-router`（使い分けはそちらの表を参照）。
---

# notion-figure-insert — PDF の図を切り出して Notion 本文に挿す

ローカルPDF（講義スライド・レジュメ・資料等）から画像として切り出せる図（グラフ・ベン図・写真・スクリーンショット等。数式や表はテキストで十分なので対象外）を特定し、
対応するNotionページ本文の該当セクションに挿入するスキル。

Notion APIには生ファイルの直接アップロード手段がないため、Google Drive（`google-multi` MCP）を画像ホスティングの中継点として使う。

## 前提

- ローカルツール: `pdftoppm` / `pdfimages` / `pdfinfo`（poppler）、`magick`（ImageMagick）。`which` で無ければユーザーに `brew install poppler imagemagick` を提案する。
- MCP: `mcp__notion__*`（ページ読み書き）、`mcp__google-multi__drive_*`（アップロード・共有）。`account` には google-multi MCP に登録したアカウントの別名を渡す（以下の例では `<account>`）。
- ヘルパー: `scripts/pdf_figures.sh`（render / list-images / extract-page / crop / trim のサブコマンド）。

## ワークフロー

### 1. PDFを確認し、図のあるページを特定する

```bash
bash scripts/pdf_figures.sh info "<pdf>"
bash scripts/pdf_figures.sh render "<pdf>" "<scratch_dir>" 150
```
生成された `page-NN.png` を Read で目視確認し、グラフ・図・写真のあるページをリストアップする。
数式だけ・文章だけのページは対象外。手書きメモ画像なども通常は本文の説明で足りるため除外してよい（ユーザー指示があれば含める）。

### 2. 挿入先のNotionページを特定する

- ユーザーがURLを指定していればそれを使う。ページIDはURL末尾の32桁16進文字列（ハイフンなし）。
- `mcp__notion__API-retrieve-page-markdown` で本文を取得し、**PDFの内容とページの主題が一致するか必ず確認する**。
  - 連番・回数管理されている資料（講義ノート、議事録、連載記事等）は、PDF側の番号とNotion側の番号がずれることがある（前回分の内容が次回PDFの前半に混入する等）。内容不一致に気づいたら挿入前に必ずユーザーに確認する。
  - 一致しない場合、親ページ配下の `child_database`（一覧DB）を `mcp__notion__API-get-block-children` → `mcp__notion__API-post-search`（DB名や「該当の回・号数 + タイトル」等で検索）で探し、アイコンやタイトルの番号から正しいページを特定する。
- 正しいページの markdown を取得したら、各図に対応するセクション見出し・説明文を特定する。

### 3. 不足している図を特定する

取得した markdown 内で、対応するセクション（例:「母集団と標本」の説明の直後、「全確率の公式」の説明の直後）に、
すでに `![...](...)` の画像記法が存在するかを確認する。無ければ「不足」と判断し、挿入対象にする。
1回のタスクで複数の図が不足していることが多いので、まとめてリストアップしてから一括で処理する。

### 4. 図を抽出する

まず埋め込み画像として持っているか確認する（高画質・軽量）:
```bash
bash scripts/pdf_figures.sh list-images "<pdf>"
```
対象ページの行に妥当なサイズ（数百px角以上）の `image` エントリがあれば:
```bash
bash scripts/pdf_figures.sh extract-page "<pdf>" <page> "<scratch_dir>"
```
複数出力される場合、目的の図に対応するファイルは概ね一番サイズが大きいもの。Readで確認する。

埋め込み画像が図とテキストを一体化して1枚に持っている場合（ページ全体のスクリーンショット的な画像）、
または該当図がベクター描画のみで埋め込みラスター画像が無い場合は、ステップ1で作った `page-NN.png` から
図の領域だけを `crop` で切り出す:
```bash
bash scripts/pdf_figures.sh crop "page-NN.png" "crop.png" "<WxH+X+Y>"
```
座標はReadでpage画像を見ながら目分量で決め、切り出し結果をReadで確認して微調整する。

### 5. 余白を整える

```bash
bash scripts/pdf_figures.sh trim "crop.png" "fig_final.png" 20
```
Readで最終画像を確認する。

### 6. Google Driveにアップロードして共有する

```
mcp__google-multi__drive_upload(account="<account>", localPath=<fig_final.png>, filename=<分かりやすい名前.png>, mimeType="image/png")
mcp__google-multi__drive_share(account="<account>", fileId=<id>, type="anyone", role="reader", sendNotification=false)
```
「リンクを知っている全員が閲覧可」になる点をユーザーに伝える（教材の図を外部アクセス可能なURLとして公開することになるため）。

### 7. Notionで直接表示できるURL形式に変換する

`https://drive.google.com/uc?export=view&id=<FILE_ID>` は Notion 側の画像プロキシから読み込めず
「この画像を読み込めませんでした」になることがある。必ず以下の形式を使う:

```
https://lh3.googleusercontent.com/d/<FILE_ID>
```

### 8. Notion本文に挿入する

`mcp__notion__API-update-page-markdown` を `type: update_content` で呼び、該当セクションの説明文の直後に
画像1行を挿入する `old_str`/`new_str` ペアを作る（`old_str` は本文中でユニークな1〜2文を含める）。

```
new_str 例:
"...本文の該当文。\n\n![図の説明](https://lh3.googleusercontent.com/d/<FILE_ID>)\n\n### 次の見出し"
```

複数の図がある場合は `content_updates` 配列にまとめて渡し、1回のAPI呼び出しで反映する。

### 9. 挿入結果を検証する

`mcp__notion__API-get-block-children` でページ直下のブロックを取得し、`type: "image"` のブロックが
期待した数だけ増えていること、`image.external.url` が期待したURLであることを確認する。
100件を超えるページでは `has_more`/`next_cursor` を辿って全件確認すること。
出力が大きい場合は tool-results に保存されたファイルを Bash + python で範囲読みする。

## 注意点

- Google Driveへのアップロード＋リンク公開は「リンクを知っている人のみ」だが、事実上外部共有に当たる。
  機微な内容（個人情報・非公開試験問題など）を含む図は、アップロード前に必ずユーザーに確認する。
- PDFとNotionページの回番号が食い違っていないか、挿入前に必ず内容で照合する。ズレていた場合は
  ユーザーに「別の回のページではないか」を確認してから進める（黙って推測で確定しない）。
- 画像は必ずトリミングして図本体だけにする。周囲の本文・数式まで写り込んだ「ページ丸ごと」の画像は
  Notion本文の説明と重複するため避ける。
- 1つのPDFに複数の図がある場合、まず全部リストアップしてから抽出・挿入をまとめて行うと手戻りが少ない。
