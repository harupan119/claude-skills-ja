# claude-skills-ja

日本語で使う Claude Code / Codex 用のスキル集。日本語の文章と日本語の組版まわりで、実際に踏んだ落とし穴を手順に落としてある。

## 一覧

| スキル | 用途 |
|---|---|
| **文章** | |
| [humanizer-ja-modes](skills/humanizer-ja-modes) | AI が書いた日本語から AI 臭を抜く。口語・学術・ビジネスの3レジスタで書き換え方針を切り替える |
| [report-expand](skills/report-expand) | レポートを水増しではなく実質的な内容追加で増量する。分割→並列生成→統合→AI臭チェック→字数検証 |
| **Notion** | |
| [notion-router](skills/notion-router) | Notion 系スキルの振り分け。まずここで使い分けを見る |
| [notion-markdown](skills/notion-markdown) | Notion の拡張 Markdown は方言。素の Markdown を送ると数式・太字・表が崩れるので、送信前に検査を通す |
| [notion-figure-insert](skills/notion-figure-insert) | PDF から図だけを切り出し、対応する Notion ページ本文の該当箇所に挿入する |
| [notion-pdf-split](skills/notion-pdf-split) | Notion に取り込む前に、PDF の先頭ページを落として分割する |
| **組版・検証** | |
| [typst-ja-pdf](skills/typst-ja-pdf) | Markdown を正本にしたまま Typst で日本語 PDF を組む。代替フォント混入の検算つき |
| [c-strict-verify](skills/c-strict-verify) | C コードを厳格コンパイル→サンプル入出力照合→判定スクリプトの順で検証する |

## 導入

`~/.claude/skills/`（Claude Code）または `~/.codex/skills/`（Codex）に置くか、symlink を張る。

```bash
git clone https://github.com/harupan119/claude-skills-ja.git
cd claude-skills-ja

# 使うものだけ張る
for s in humanizer-ja-modes typst-ja-pdf notion-router notion-markdown; do
  ln -s "$PWD/skills/$s" ~/.claude/skills/$s
done
```

## 設計方針

**必要になるまで読ませない。** 共通ルールを `SKILL.md` に置き、分岐する部分だけを子ファイルに分ける。`humanizer-ja-modes` は検出ルール（全モード共通）を本体に、書き換え方針（モード別）を `modes/` に置いてある。全部を1ファイルに書くと、casual の指示が academic の書き換えに漏れる。

**名前は「何をするか」で付ける。** `<領域>-<動作>` に揃えてある。スキル名は発動判定の材料であり、`/名前` で叩くコマンド名でもある。領域名だけを並べた命名は、一覧を見ても各スキルが何をするのか読めない。

**個人情報を持ち込まない。** 環境依存の値はプレースホルダにしてある（`account="<account>"` など）。`humanizer-ja-modes` の声紋ファイルは、書き手本人の私的な文章から作るものなので**同梱していない**。雛形だけ置いてある。

**出典を書く。** 先行実装から着想を得たものは [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) に、出典・ライセンス・複製の有無の検証結果まで記した。

公開時に環境固有の値をどう外しているかは [PUBLISHING.md](PUBLISHING.md) にある。

---

## humanizer-ja-modes

AI が書いた日本語は、消すべきものが**レジスタによって違う**。口語で「体温を入れる」書き換えを学術文書にやると、だ・である調が壊れて逆に不自然になる。そこで検出と書き換えを分け、**検出ルールは共通、書き換え方針だけモード別**にしてある。

| モード | 対象 | 文体 |
|---|---|---|
| casual | ブログ・note・SNS・日記 | ですます／タメ口 |
| academic | 大学レポート・論文・実験考察 | だ・である／無人称 |
| business | 就活 ES・ビジネスメール・申請書 | ですます／敬体 |

検出は3層構成。記号の残骸（全角ダッシュ・絵文字・太字の乱用）、語彙の偏り（「これにより」「〜することができる」など）、思考構造の型（否定並列、曖昧な権威づけ、体験と固有名の不在）を順に見る。誤検出ガードを持っていて、ダッシュ1個や硬い語彙だけでは AI と断定しない。

`references/ai-score-rubric.md` で AI 度を採点できる。提出前に強い tell が残っていないかを確認する用途。

**声紋ファイルは同梱していない。** 書き手本人の私的な文章から作るもので、個人情報として扱うべきものだから。作り方と雛形は `modes/casual/voice-print-ja.template.md` にある。無くても一般的な口語の humanize までは動く。

## typst-ja-pdf

日本語の文書を Markdown で書いて PDF にする時、**Typst のソースを直接書かない**ための構成。変換スクリプトを挟んで `report.md` から機械的に組む。

理由は、本文と提出物が別々に育つと必ず乖離するため。実際に手で PDF を直し始めた結果、Markdown 側が古くなり提出版が正本になってしまった経験から、変換を挟む形にした。

日本語 PDF 特有の落とし穴を `references/fonts.md` にまとめてある。実際に踏んだもの。

- **番号付き数式の中の日本語が、簡体字中国語フォントで描かれる。** 数式は本文と別のフォント列で組まれるため、指定しないと処理系任せの代替に落ちる。
- **`⌈ ⌉` と `⌊ ⌋` が同じ角括弧に化ける。** どの和文・欧文フォントにも字形が無い。天井と床を対比させる文で踏むと、対比そのものが読者に見えなくなる。
- **MS ゴシックを matplotlib に使うと文字が消える。** 7〜22 ppem の埋め込みビットマップを持ち、その範囲では Agg がアウトラインを描かない。図の文字はちょうどこの範囲に入るので、タイトルだけ残って軸ラベルと凡例が真っ白になる。

いずれも `pdffonts` に想定外のフォント名が並ぶことで気づける。検出用のスクリプトを2本同梱している。

```bash
# PDF 内でどのフォントが何の文字を描いたか数える（代替フォント混入の特定）
python3 skills/typst-ja-pdf/scripts/pdf_font_census.py report.pdf \
  --expect "MS-Mincho,MS-Gothic,TimesNewRoman,Menlo,NewCMMath"

# 指定フォントに字形が無い文字を本文から洗い出す（組む前に潰す）
python3 skills/typst-ja-pdf/scripts/font_coverage.py report.md \
  --font "~/Library/Fonts/msmincho.ttc:MS Mincho" --skip-code
```

### 必要なもの

- [Typst](https://typst.app/)（`brew install typst`）
- 図を作るなら matplotlib
- `pdf_font_census.py` は pdfminer.six、`font_coverage.py` は fontTools（matplotlib の依存に含まれる）

## Notion 系（4スキル）

Notion まわりは関心ごとに4つに分けてある。入口は `notion-router` で、そこの表から選ぶ。

| 関心 | スキル |
|---|---|
| ファイルの前処理（PDFを削る・分ける）| `notion-pdf-split` |
| 本文テキストのページ化 | `notion-markdown` |
| 本文への画像挿入 | `notion-figure-insert` |

**`notion-markdown` が中心。** Notion の Markdown は方言で、素の Markdown をそのまま送ると数式・太字・表が崩れる。何がどう崩れるかと、送る前に通す検査を書いてある。

**`notion-figure-insert` は Notion API の制約を回避する手順。** Notion には生ファイルを直接アップロードする API が無いため、Google Drive を画像ホスティングの中継点として使う。この時 `https://drive.google.com/uc?export=view&id=...` 形式は Notion の画像プロキシから読めず「この画像を読み込めませんでした」になるので、`https://lh3.googleusercontent.com/d/<FILE_ID>` を使う。

## report-expand

既存のレポート本文を、**実質的な内容追加**で目標倍率まで増量する。文の引き延ばし・定型評価語の挿入はしない。

追加ブロックをサブエージェントで並列生成し、統合・整合・レビューを親セッションが担う。仕上げに `humanizer-ja-modes` の academic モードで AI 臭を抜き、字数を検証して終わる。

数値は元データにある値しか使わせない。サブエージェントに新しい数値を作らせないための制約を明記してある。

## c-strict-verify

C のコードを「読む→厳格コンパイル→入出力照合→判定スクリプト」の順で検証する。**順序を崩さない**のが要点で、警告を残したまま出力を比べても、原因がロジックなのか未定義動作なのか切り分けられない。

報告の規律まで含めてある。指摘を深刻度順に、ファイル名と行番号つきで、実際に実行したコマンドだけを書く。全部通った場合は残った前提（「ソート済み入力を前提にしている」など）を明示する。

## ライセンス

MIT。[LICENSE](LICENSE) を参照。

`humanizer-ja-modes` は先行する複数のスキルから着想を得ている。出典・ライセンス・複製の有無の検証結果は [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) に記した。
