# Notion 拡張 Markdown 記法リファレンス

`mcp__notion__API-update-page-markdown` / `API-retrieve-page-markdown` が読み書きする方言。
実在ページから読み出した記法をもとにまとめている（推測ではなく実測）。

## 数式

```markdown
インライン: 入力サイズ $`n`$ が大きくなると…

ブロック:
$$
O(1) < O(\log n) < O(n) < O(n\log n) < O(n^2)
$$
```

- インラインは **`$` + バッククォート**で囲む。`$n$` のままだと数式にならずリテラル表示になる。
- ブロックは `$$` を**それだけの行**に置く。`$$x=1$$` や `**(a)** $$` は認識されない。
- `\text{}` の中に `$...$` を入れ子にしない（KaTeX は通すが Notion のパーサが壊す）。
- `\begin{cases}...\end{cases}`、`\dfrac`、`\mathrm`、`\lvert` などは通る。

## 見出し

```markdown
# H1
## H2
### H3
```

H3 まで。H4 以降は段落に落ちて階層が消えるので、送る前に詰める。
ページタイトルは本文の外（ページのプロパティ）にあるので、本文先頭に H1 でタイトルを書くと重複する。

## 表

```markdown
| 年度 | 形式 |
|---|---|
| 2025 | 対面90分 |
```

- 区切り行は `---` のみ。`:--:` `:---` `---:` は区切りと認識されず、データ行として表に混入する。
- 読み出すと `<table header-row="true"><tr><td>…</td></tr></table>` の形になる。
- セル内の `**太字**` はそのまま残る（レンダリングされないことがあるので、表では装飾に頼らない）。

## トグル

```markdown
<details color="blue_bg">
<summary>回答：計算量の大小関係は暗記必須？</summary>
	**結論：** 順番を丸暗記するより増え方を理解する。
	### 中の見出しも使える
	$$
	O(1) < O(\log n)
	$$
</details>
```

中身は**タブ**でインデントする。数式ブロックも入れられる。

## コールアウト

```markdown
<callout icon="💡" color="yellow_bg">
	**暗記の目安：** この順番は即答できるようにする。
</callout>
```

`color` に使える値の例: `yellow_bg` / `blue_bg` / `red_bg` / `gray_bg`。

## リスト・チェックボックス

```markdown
- 箇条書き
1. 番号付き
- [ ] 未チェック
- [x] チェック済み
```

チェックボックスは to-do ブロックになる。番号付きリストは連番が振り直されるので、
「8項目」と本文で言及している場合は番号のずれに注意する。

## エスケープ

読み出すと `>` が `\>`、`<` が `\<` にエスケープされて返る。書く側は素のまま `>` でよい。

## 画像

```markdown
![説明](https://lh3.googleusercontent.com/d/<FILE_ID>)
```

Notion API に直接アップロードする手段はない。Google Drive 等でホストして external URL で参照する。
`https://drive.google.com/uc?export=view&id=…` は Notion の画像プロキシから読めないことがあるので
`https://lh3.googleusercontent.com/d/<FILE_ID>` を使う（詳細は `notion-figure-insert` スキル）。

## データベース参照

ページ本文にインライン DB があると、読み出しでこう返る:

```markdown
<database url="https://app.notion.com/p/3420de9159b5805e82f6c2f414601554" inline="true"
  data-source-url="collection://3420de91-59b5-80f8-87a4-000b271fa240">DB_数理統計学</database>
```

- `url` 末尾の32桁が **database_id**（`API-retrieve-a-database` / `API-post-page` の parent に使う）。
- `data-source-url` の `collection://` の ID は `API-query-data-source` に渡しても
  `invalid_request_url` になることがある（サーバの API バージョン依存）。DB の中身を列挙したいときは
  `API-post-search` でタイトル検索して parent が該当 database_id のページを拾うほうが確実。

## API 上の制約

| 制約 | 実測・対処 |
|---|---|
| 1リクエストのサイズ | JSON 68KB 付近で切断。日本語をエスケープせず素で書き、12,000文字ごとに分割する |
| 末尾追記 | `type="insert_content"`, `insert_content={"position":{"type":"end"},"content":"…"}` |
| 全面差し替え | `type="replace_content"`, `replace_content={"new_str":"…"}`（人の編集も消えるので注意） |
| 部分修正 | `type="update_content"`, `update_content={"content_updates":[{"old_str":"…","new_str":"…"}]}` 最大100件 |
| 戻り値 | いずれもページ全体の markdown が返るので、そのまま検証に使える |
