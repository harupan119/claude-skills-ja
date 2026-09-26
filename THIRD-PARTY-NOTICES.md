# 第三者の著作物について

`skills/humanizer-ja-modes` は、先行する複数のスキルから**着想と方法**を得て日本語で書き直したものである。以下に出典とライセンスを記す。

## 影響を受けた先行実装

| リポジトリ | ライセンス | 著作権表示 |
|---|---|---|
| [blader/humanizer](https://github.com/blader/humanizer) | MIT | Copyright (c) 2025 Siqi Chen |
| [gonta223/humanizer-ja](https://github.com/gonta223/humanizer-ja) | MIT | Copyright (c) 2025 Siqi Chen (original: blader/humanizer) |
| [makotofalcon/humanizer-ja](https://github.com/makotofalcon/humanizer-ja) | MIT | Copyright (c) 2025 |
| [matsuikentaro1/humanizer_academic](https://github.com/matsuikentaro1/humanizer_academic) | MIT | Copyright (c) 2025 Kentaro Matsui |
| [jalaalrd/anti-ai-slop-writing](https://github.com/jalaalrd/anti-ai-slop-writing) | ライセンス表示なし | — |

参考にした資料として、[Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)（WikiProject AI Cleanup、CC BY-SA 4.0）がある。

## 複製の有無について

公開にあたり、上記各リポジトリの本文と `skills/humanizer-ja-modes` の全 Markdown を機械的に照合した。

**jalaalrd/anti-ai-slop-writing** はライセンスを表示しておらず、再配布は許諾されていない。同リポジトリの本文は全編が英語で、日本語文字を1文字も含まない。照合の結果、共通する英語語句は6種（`anti-ai-slop-writing`＝出典表記そのもの、`banned-words`、`description` / `name` / `references`＝Markdown フロントマターの一般語、`gpt-`）のみで、**5語以上連続して一致する箇所は0件**であった。したがって本リポジトリは同リポジトリの表現を複製しておらず、その再配布にはあたらない。着想と方法の水準での影響にとどまる。

**MIT ライセンスの4件**については、空白を除いた20文字の断片で照合したところ一致率は 0.4〜2.4% であった。一致した連なりの大半は URL および出典表記の行そのもの（例：`[blader/humanizer](https://github.com/blader/humanizer)`）で、URL を除いた最長の一致は22文字である。実質的な部分の複製にはあたらないと判断しているが、明示的に先行実装を統合元として挙げている以上、上表に著作権表示を掲げる。

MIT ライセンスの全文は各リポジトリの `LICENSE` を参照のこと。

## 誤りの指摘について

出典の記載漏れ、あるいは意図しない複製が含まれているとお考えの場合は、Issue で指摘してほしい。確認のうえ、削除または帰属の追記で対応する。

## textlint-ja のルール群と JTF日本語標準スタイルガイド

`skills/humanizer-ja-modes/references/style-metrics.md` と `scripts/ja_style_check.py` の基準値・規則は、以下を参照して日本語で書き直したものである。スクリプトは textlint のコードを含まず、規則を正規表現で独自に実装している。

| リポジトリ | ライセンス | 著作権表示 |
|---|---|---|
| [textlint-ja](https://github.com/textlint-ja) の各ルール（preset-ja-technical-writing、ja-no-redundant-expression、ja-no-weak-phrase、ja-no-abusage、no-double-negative-ja、no-doubled-joshi、no-dropping-the-ra）| MIT | Copyright (c) 2015-2016 azu |
| [textlint-rule-preset-JTF-style](https://github.com/textlint-ja/textlint-rule-preset-JTF-style) | MIT（コード）／CC BY-SA（規則の記述）| 規則の記述は「JTF日本語標準スタイルガイド2.0」(Japan Translation Federation, CC BY-SA, www.jtf.jp) を改変したもの |

参照した版は `sources/manifest.json` にコミットハッシュで固定し、原本の該当ファイルとライセンス文を `sources/mirror/` に複製して同梱している。複製は各ライセンスの条件（著作権表示とライセンス文の同梱）に従う。

`sources/mirror/textlint-rule-preset-JTF-style/README.md` は CC BY-SA の規則記述を含むため、このファイルに限り CC BY-SA の条件で再配布する。`style-metrics.md` では JTF の規則を項番とともに要約しており、規則の文言そのものは写していない。

## フォントについて

`skills/typst-ja-pdf` は MS 明朝・MS ゴシックを用いる手順を含むが、**フォントファイルは配布しない。**各自が導入済みの Microsoft Office から自分の環境に複製して使う前提である。Office のライセンスを持たない環境では、ヒラギノや源ノ明朝など手元のフォントに切り替わる。
