# 原本ミラー

スキルの規則や基準値の根拠にした文献・辞書を、取得元とハッシュを固定して置く。規則を書き換えるときは、ここの原本を読んでから直す。二次情報（検索結果の要約や解説記事）から規則を起こさない。

## 構成

| パス | 内容 |
|---|---|
| `manifest.json` | 原本の一覧。取得元・ライセンス・確認状況・何の根拠に使ったか |
| `lock.json` | 取得日と各ファイルの SHA-256 |
| `mirror.py` | 取得スクリプト（標準ライブラリのみ）|
| `mirror/<id>/` | 再配布できる原本。git 管理する |
| `mirror/_local/<id>/` | ライセンス未確認・再配布不可の原本。`.gitignore` で除外。手元参照専用 |

```bash
python3 sources/mirror.py            # 全件取得
python3 sources/mirror.py --only ID  # 1件
python3 sources/mirror.py --verify   # 手元の複製が lock.json と一致するか
```

原本が差し替わっていた場合（ハッシュ不一致）、スクリプトは上書きせずに失敗する。差分を読み、スキル側の規則に影響があるか確かめてから `lock.json` の該当項目を消して取り直す。

## 何を公開リポジトリに入れるか

`redistributable: true` かつ `license_verified: true` のものだけを `mirror/` に置く。

- **ライセンスは原本そのもので確認する。** 検索結果や解説記事が「CC BY」と書いていても、それだけでは `license_verified` にしない。実例がある。JTF日本語標準スタイルガイドは第3.0版で CC BY 4.0 になったとする二次情報がある。一方、textlint-rule-preset-JTF-style は第2.0版を CC BY-SA として表示している。版によって条件が違う可能性があるため、PDF 本体の表示を読むまで未確認として扱う。
- **無料で読めることと、再配布してよいことは別である。** 大学の手引きや学会誌の解説は無償公開されていても、再配布の許諾があるとは限らない。条件が書かれていなければ `_local` に置く。
- **再掲 URL は一次配布ではない。** `sist02-2007` の URL は京都大学のサーバーに置かれた写しで、科学技術振興機構の配布元ではない。一次配布元を確認できたら差し替える。

## 現状（2026-09-26）

取得済みで公開しているのは textlint-ja の8リポジトリ（MIT。JTF 由来の規則記述は CC BY-SA）で、`skills/humanizer-ja-modes/references/style-metrics.md` の根拠になっている。

以下の5件は manifest に載せたが、作成時の環境でネットワークが GitHub とパッケージレジストリ以外を遮断していたため未取得である。取得後、本文を読んでからスキルに反映する。

| id | 反映先の候補 |
|---|---|
| `plos-mensh-kording-2017` | academic：段落は1主張、文脈→内容→結論の構成 |
| `jtf-style-guide-3` | style-metrics：送り仮名・漢字とかなの使い分け（textlint 未実装の項目）|
| `bunka-kobunsho-2022` | business / academic：用語の言い換え、文の長さと構造 |
| `sist02-2007` | report-expand：参考文献の書式 |
| `gopen-swan-1990` | academic：主題を文頭に、強調したい情報を文末に置く |

各件の「反映先の候補」は取得前の見立てであり、原本を読んだ結果で変わりうる。
