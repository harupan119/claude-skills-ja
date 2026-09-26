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

## 論文の原本について

`docs/papers/pdf/` には、再配布が許されるライセンス（CC BY 4.0 / CC BY-SA 4.0 / CC0 1.0）の論文8本を**無改変で**同梱している。各 PDF に適用されるのはそれぞれのライセンスであり、本リポジトリの MIT ライセンスではない。題名・著者・ライセンス・取得元は [docs/papers/README.md](docs/papers/README.md) と `docs/papers/manifest.json` に記した。

それ以外の論文（arXiv の既定ライセンス、CC BY-NC-ND、出版社の著作権下にあるもの）は同梱せず、取得元URLとハッシュのみを置いている。

## フォントについて

`skills/typst-ja-pdf` は MS 明朝・MS ゴシックを用いる手順を含むが、**フォントファイルは配布しない。**各自が導入済みの Microsoft Office から自分の環境に複製して使う前提である。Office のライセンスを持たない環境では、ヒラギノや源ノ明朝など手元のフォントに切り替わる。
