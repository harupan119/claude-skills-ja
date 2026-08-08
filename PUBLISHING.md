# 公開版の保守メモ

このリポジトリのスキルは、作者の手元にある実運用版から**環境固有の値を外して**公開している。
手元版を直したあと公開版に反映するとき、毎回同じ箇所を外し直すことになるので、その一覧を残す。

## 命名規則

`<領域>-<動作>` の小文字ケバブケース。

- スキル名は**ディレクトリ名と frontmatter の `name` が一致**していること（Claude Code の制約）
- 領域名だけの命名は避ける。一覧で役割が読めなくなる
- マーケティング的な接尾辞（`-pro`、`-ultimate`）と、所属機関名・個人名は使わない

## 公開時に外している値

| スキル | 外すもの | 公開版での扱い |
|---|---|---|
| `notion-figure-insert` | google-multi MCP のアカウント別名 | `account="<account>"` |
| `report-expand` | 提出先固有の書式規約スキルへの依存 | 「提出先に書式規約がある場合は先に読む」と一般化 |
| `report-expand` | ローカルの学術文章原則ファイルのパス | 「あれば渡す（任意）」と一般化 |
| `c-strict-verify` | ソースファイル名に含まれる識別子 | `q1.c` などの汎用名 |
| `typst-ja-pdf` | 表紙の項目（所属・科目・担当者）| 「提出先が指定するもの」と一般化 |
| `typst-ja-pdf` | 出力ファイル名の規則 | `<出力名>.pdf` |
| `humanizer-ja-modes` | 特定の提出先を指す記述 | 「大学レポート・論文」と一般化 |

## 公開しないもの

- **声紋ファイル** `skills/humanizer-ja-modes/modes/casual/voice-print-ja.md`
  書き手本人の私的な文章から作るため、個人情報として扱う。`.gitignore` で除外している。
  雛形（`voice-print-ja.template.md`）だけ公開する。
- 特定の組織・学内システムに依存するスキル全般

## 更新するときの手順

1. 手元版を該当ディレクトリへコピーする（`.DS_Store` と `__pycache__` を除く）
2. 上の表の値を外す
3. 個人情報のスイープをかける（識別子・ローカルパス・組織名）
4. `name` とディレクトリ名の一致を確認する
5. Python とシェルスクリプトの構文チェックを通す
6. README の一覧とリンクを更新する

3〜5は次のコマンドでまとめて確認できる。

```bash
# 4. name とディレクトリ名の一致
cd skills && for d in */; do
  n=$(sed -n 's/^name: *//p' "${d}SKILL.md" | head -1 | tr -d '"')
  [ "$n" = "${d%/}" ] && echo "OK  ${d%/}" || echo "NG  dir=${d%/} name=$n"
done

# 5. 構文チェック
find skills -name "*.py" -print0 | xargs -0 python3 -m py_compile
for f in $(find skills -name "*.sh"); do bash -n "$f" || echo "NG $f"; done
```
