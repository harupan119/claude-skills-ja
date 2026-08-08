---
name: notion-markdown
description: Notion用のMarkdownを書く、または既存の.mdをNotionページに送る。ユーザーが「mdをNotionに送って」「Notionページにして」「Notion用に書いて」「Notionに取り込める形にして」のように、Markdown本文をNotionページ化したいときに使う。Notionの拡張Markdownは方言で、素のMarkdownをそのまま送ると数式・太字・表が崩れるため、送信前に必ずこのスキルの検査を通す。図の挿入は `notion-figure-insert`、PDF事前分割は `notion-pdf-split`。統括は `notion-router`。
---

# notion-markdown — Notion の方言に合わせて Markdown を送る

Notion MCP が受け取る Markdown は**方言**であり、素の Markdown をそのまま送ると崩れる。
このスキルは2つの入り口を持つ。

| 状況 | 進め方 |
|---|---|
| これから Notion 用に本文を書く | 「記法」の節に従って最初から Notion 方言で書く |
| 既存の `.md` を Notion に送る | `scripts/md2notion.py` で変換・検査してから送る |

どちらの場合も、**送信前に `lint` を通して MANUAL 項目をゼロにする**のが要件。

## 前提

- MCP: `mcp__notion__*`（`mcp__claude_ai_Notion__*` は接続していないことがある。失敗したら `mcp__notion__*` を使う）
- ヘルパー: `scripts/md2notion.py`（依存なし。`lint` / `convert` / `split`）

## 記法

Notion 方言で特に間違えやすいものだけを挙げる。全一覧は `reference/syntax.md`。

| 要素 | 正しい書き方 | 素のMarkdownとの違い |
|---|---|---|
| インライン数式 | `` $`\mu`$ `` | バッククォートで囲む。`$\mu$` は数式にならない |
| ブロック数式 | `$$` を**独立行**に置き、中身を挟む | `$$...$$` を1行に書くと認識されない |
| 見出し | H1〜H3 のみ | H4 以降はただの段落になり階層が消える |
| 表の区切り行 | `|---|---|` | `|:--:|` は区切りと認識されずデータ行として表に混入する |
| トグル | `<details color="blue_bg"><summary>見出し</summary>` + タブインデントした中身 + `</details>` | — |
| コールアウト | `<callout icon="⚠️" color="red_bg">` + タブインデントした中身 + `</callout>` | — |

### 崩れる書き方（機械変換できないので人が直す）

1. **太字の内側に数式を入れない**
   Notion は数式を先に切り出すため `**` の位置がずれる。
   ```
   NG:  **5% 有意水準で $`H_0`$ を棄却する**
   OK:  **5% 有意水準で帰無仮説を棄却する**
   OK:  $`H_0`$ **を棄却する**          ← 数式を太字の外に出す
   ```
   太字の「外」にある数式（`**(b)** $`x`$ より`）は壊れないので直す必要はない。

2. **見出しに数式を入れない**
   ```
   NG:  ## 問21 $`N`$ と $`N-1`$
   OK:  ## 問21 N と N−1
   ```

3. **`\text{}` の中に数式を入れ子にしない**
   KaTeX 単体では通るが Notion のパーサが壊す。
   ```
   NG:  \text{（$x$ によらない項）}
   OK:  \text{（}x\ \text{によらない項）}
   ```

## ワークフロー：既存の .md を送る

### 1. 検査する

```bash
python3 scripts/md2notion.py lint <input.md>
```
`[auto]` は次の `convert` で直る。`[MANUAL]` は**人が原文を直す**（機械変換すると意味が変わるため自動化しない）。
原本を書き換えたくない場合は、変換後のファイルに対して直す。

### 2. 変換する

```bash
python3 scripts/md2notion.py convert <input.md> -o <out.md>
```
やること: インライン数式 → `` $`…`$ ``／ブロック数式の `$$` を独立行へ／表の区切り行を `---` に／
H4 以降を含む場合は見出し階層を H1〜H3 に詰める／先頭 H1 をページタイトルとして抜き出す。

出力末尾に残 MANUAL 件数が出る。**ゼロになるまで送らない。**

### 3. 送信先を決める

既存の科目・プロジェクトページの下にぶら下げるのが基本。
ローカルフォルダに `▶ Notion.webloc` があればそこにリンク先が入っている:
```bash
plutil -p "<フォルダ>/▶ Notion.webloc"
```
ページ配下にインラインDB（`DB_◯◯`）があれば、その中に作るのが既存構造に沿う。
`mcp__notion__API-retrieve-page-markdown` で親を読み、`<database url="...">` の URL 末尾32桁が database_id。

### 4. ページを作る

```
mcp__notion__API-post-page(
  parent     = {"type":"database_id","database_id":"<id>"},
  properties = {"名前":{"title":[{"type":"text","text":{"content":"<タイトル>"}}]}},
  icon       = {"type":"emoji","emoji":"📝"}
)
```
DB のタイトルプロパティ名は日本語（`名前`）のことがある。`API-retrieve-a-database` で確認する。

### 5. 本文を流し込む

**日本語は `\uXXXX` にエスケープせず、そのまま書く。** エスケープするとペイロードが6倍に膨らみ、
1リクエストの上限を超えて途中で切れる（実測: JSON 68KB で切断）。

12,000文字を超えるなら分割する:
```bash
python3 scripts/md2notion.py split <out.md> --outdir <dir>
```
- part01 → `API-update-page-markdown(type="replace_content", replace_content={"new_str": "..."})`
- part02 以降 → `API-update-page-markdown(type="insert_content", insert_content={"position":{"type":"end"}, "content": "..."})`

`insert_content` は deprecated 扱いだが末尾追記には現状これが確実。

### 6. 読み返して検証する

`API-update-page-markdown` の戻り値がページ全体の markdown なので、そのまま確認できる。
特に見るところ:
- 表に `---` や `:--:` の行が紛れていないか（紛れていたら `<table header-row="true">` を付けて区切り行を削除）
- `**` が数式の外にずれていないか
- `$$` が独立行になっているか

崩れていたら `type="update_content"` の find-and-replace でピンポイントに直す:
```
update_content = {"content_updates": [{"old_str": "...", "new_str": "..."}]}
```

## 注意点

- **既存ページへの追記は `insert_content`、全面差し替えは `replace_content`。** 途中で人が編集した可能性がある
  ページに `replace_content` を撃つとその編集ごと消える。長い流し込みの最中にユーザーが手を入れることがあるので、
  分割送信では2回目以降を必ず `insert_content` にする。
- `convert` は先頭 H1 を本文から抜いてページタイトルに回す。本文に残したいときは `--keep-title`。
- 見出しを詰めたくない（すでに Notion 用に階層設計済み）ときは `--no-shift`。
- ローカル原本は変換しない。変換結果は scratchpad に出し、原本は素の Markdown のまま残す
  （Obsidian や Zettlr で読むのは原本のほう）。
- Notion 側のページ内リンクは URL で書く。相対パス（`../_過去問/`）はローカル専用なので、
  Notion に送る本文では「別ページ『◯◯』」のように名前で参照するか、URL に置き換える。
