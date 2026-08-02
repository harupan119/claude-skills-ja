# claude-skills-ja

日本語で使う Claude Code / Codex 用のスキル。

| スキル | 用途 |
|---|---|
| [humanizer-ja-pro](skills/humanizer-ja-pro) | AI が書いた日本語から AI 臭を抜く。口語・学術・ビジネスの3レジスタで書き換え方針を切り替える |
| [tuat-report-pdf](skills/tuat-report-pdf) | Markdown を正本にしたまま Typst で日本語 PDF を組む。MS 明朝・MS ゴシックの落とし穴つき |

## 導入

`~/.claude/skills/`（Claude Code）または `~/.codex/skills/`（Codex）に置くか、symlink を張る。

```bash
git clone https://github.com/harupan119/claude-skills-ja.git
ln -s "$PWD/claude-skills-ja/skills/humanizer-ja-pro" ~/.claude/skills/humanizer-ja-pro
ln -s "$PWD/claude-skills-ja/skills/tuat-report-pdf"  ~/.claude/skills/tuat-report-pdf
```

---

## humanizer-ja-pro

AI が書いた日本語は、消すべきものが**レジスタによって違う**。口語で「体温を入れる」書き換えを学術文書にやると、だ・である調が壊れて逆に不自然になる。そこで検出と書き換えを分け、**検出ルールは共通、書き換え方針だけモード別**にしてある。

| モード | 対象 | 文体 |
|---|---|---|
| casual | ブログ・note・SNS・日記 | ですます／タメ口 |
| academic | 大学レポート・論文・実験考察 | だ・である／無人称 |
| business | 就活 ES・ビジネスメール・申請書 | ですます／敬体 |

検出は3層構成。記号の残骸（全角ダッシュ・絵文字・太字の乱用）、語彙の偏り（「これにより」「〜することができる」など）、思考構造の型（否定並列、曖昧な権威づけ、体験と固有名の不在）を順に見る。誤検出ガードを持っていて、ダッシュ1個や硬い語彙だけでは AI と断定しない。

`references/ai-score-rubric.md` で AI 度を採点できる。提出前に強い tell が残っていないかを確認する用途。

**声紋ファイルは同梱していない。** 書き手本人の私的な文章から作るもので、個人情報として扱うべきものだから。作り方と雛形は `modes/casual/voice-print-ja.template.md` にある。無くても一般的な口語の humanize までは動く。

## tuat-report-pdf

日本語のレポートを Markdown で書いて PDF にする時、**Typst のソースを直接書かない**ための構成。変換スクリプトを挟んで `report.md` から機械的に組む。

理由は、本文と提出物が別々に育つと必ず乖離するため。実際に手で PDF を直し始めた結果、Markdown 側が古くなり提出版が正本になってしまった経験から、変換を挟む形にした。

日本語 PDF 特有の落とし穴を `references/fonts.md` にまとめてある。実際に踏んだもの。

- **番号付き数式の中の日本語が、簡体字中国語フォントで描かれる。** 数式は本文と別のフォント列で組まれるため、指定しないと処理系任せの代替に落ちる。
- **`⌈ ⌉` と `⌊ ⌋` が同じ角括弧に化ける。** どの和文・欧文フォントにも字形が無い。天井と床を対比させる文で踏むと、対比そのものが読者に見えなくなる。
- **MS ゴシックを matplotlib に使うと文字が消える。** 7〜22 ppem の埋め込みビットマップを持ち、その範囲では Agg がアウトラインを描かない。図の文字はちょうどこの範囲に入るので、タイトルだけ残って軸ラベルと凡例が真っ白になる。

いずれも `pdffonts` に想定外のフォント名が並ぶことで気づける。検出用のスクリプトを2本同梱している。

```bash
# PDF 内でどのフォントが何の文字を描いたか数える（代替フォント混入の特定）
python3 skills/tuat-report-pdf/scripts/pdf_font_census.py report.pdf \
  --expect "MS-Mincho,MS-Gothic,TimesNewRoman,Menlo,NewCMMath"

# 指定フォントに字形が無い文字を本文から洗い出す（組む前に潰す）
python3 skills/tuat-report-pdf/scripts/font_coverage.py report.md \
  --font "~/Library/Fonts/msmincho.ttc:MS Mincho" --skip-code
```

TUAT（東京農工大）のレポートを想定して書いているが、フォントと変換の部分は日本語の PDF 一般に使える。

### 必要なもの

- [Typst](https://typst.app/)（`brew install typst`）
- 図を作るなら matplotlib
- `pdf_font_census.py` は pdfminer.six、`font_coverage.py` は fontTools（matplotlib の依存に含まれる）

## ライセンス

MIT。[LICENSE](LICENSE) を参照。

`humanizer-ja-pro` は先行する複数のスキルから着想を得ている。出典・ライセンス・複製の有無の検証結果は [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) に記した。
