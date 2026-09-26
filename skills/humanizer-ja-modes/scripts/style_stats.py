#!/usr/bin/env python3
"""日本語本文の文体統計を出す。AI判定器ではない。

    python3 style_stats.py draft.md
    python3 style_stats.py draft.md --baseline mine/*.txt   # 本人の過去文と並べる

出すもの:
  - 文長（平均・標準偏差・変動係数）と、同程度の長さの文の連続
  - 読点の打ち方（1文あたりの読点数、「は、」「が、」「を、」などの頻度）
  - 文頭の接続詞・副詞の頻度
  - 文末の型の上位
  - 横棒 [—―–] と「これにより」の件数

読点の位置と機能語（助詞・助動詞・接続詞・副詞）の使用率は、日本語の書き手識別で
話題に依存しにくい特徴として使われてきたもので、Zaitsu & Jin (2023) は同じ特徴で
GPT-3.5/4 の文章と人間の論文を識別している。ここでは形態素解析をせず表層の文字列で
数えるため、値は近似である。単独の数値で AI かどうかを決めず、本人の過去文
（--baseline）との差を見る用途に使う。1,000字未満の本文では値が安定しない。
"""
import argparse
import re
import statistics
import sys
from collections import Counter

PARTICLE_COMMA = ["は、", "が、", "を、", "に、", "で、", "も、", "て、", "と、", "ので、", "から、"]
CONNECTIVES = [
    "また", "さらに", "加えて", "そして", "しかし", "しかしながら", "一方", "一方で", "ただし", "ただ",
    "なお", "つまり", "すなわち", "したがって", "そのため", "このため", "このように", "これにより",
    "以上より", "例えば", "特に", "まず", "次に", "最後に", "実際", "でも", "だから", "なので",
    "それで", "あと", "で", "まあ", "結局",
]
CONNECTIVES.sort(key=len, reverse=True)


def body_text(raw):
    raw = re.sub(r"```.*?```", "", raw, flags=re.DOTALL)
    lines = [l for l in raw.split("\n")
             if not re.match(r"^\s*(#|\||!\[|<!--)", l)]      # 見出し・表・画像・コメント
    text = "\n".join(lines)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)      # リンクは文字だけ残す
    return re.sub(r"[*_`>]", "", text)


def sentences(text):
    parts = re.split(r"(?<=[。！？!?])|\n{2,}", text)
    return [re.sub(r"\s+", "", p) for p in parts if re.sub(r"\s+", "", p)]


def stats(raw):
    text = body_text(raw)
    sents = sentences(text)
    chars = len(re.sub(r"\s", "", text))
    lens = [len(s) for s in sents]
    per_k = (lambda n: n * 1000 / chars) if chars else (lambda n: 0.0)
    starts = Counter()
    rest = []   # 文頭の接続詞を除いた残り。「さらに、」の「に、」を助詞+読点に数えないため
    for s in sents:
        for c in CONNECTIVES:
            if s.startswith(c + "、") or (len(c) >= 2 and s.startswith(c)):
                starts[c] += 1
                s = s[len(c):].lstrip("、")
                break
        rest.append(s)
    rest_text = "\n".join(rest)
    endings = Counter(re.sub(r"[。！？!?」）)]+$", "", s)[-3:] for s in sents if len(s) >= 4)
    # 長さが±20%以内の文が3つ以上続く箇所
    runs, run = 0, 1
    for a, b in zip(lens, lens[1:]):
        run = run + 1 if a and abs(b - a) / a <= 0.2 else 1
        if run == 3:
            runs += 1
    mean = statistics.mean(lens) if lens else 0.0
    sd = statistics.pstdev(lens) if len(lens) > 1 else 0.0
    return {
        "chars": chars,
        "sentences": len(sents),
        "len_mean": mean,
        "len_sd": sd,
        "len_cv": sd / mean if mean else 0.0,
        "even_runs": runs,
        "commas_per_sent": text.count("、") / len(sents) if sents else 0.0,
        "particle_comma": {p: per_k(rest_text.count(p)) for p in PARTICLE_COMMA},
        "starts": {k: per_k(v) for k, v in starts.items()},
        "endings": endings.most_common(5),
        "dashes": len(re.findall(r"[—―–]", text)),
        "koreniyori": text.count("これにより"),
    }


def show(label, st, base=None):
    print(f"== {label}")
    warn = "  ※1,000字未満。値は参考程度" if st["chars"] < 1000 else ""
    print(f"本文 {st['chars']}字 / {st['sentences']}文{warn}")

    def row(name, v, b=None, fmt="{:.2f}"):
        s = f"  {name:<18}" + fmt.format(v)
        if b is not None:
            s += "   (本人 " + fmt.format(b) + ")"
        print(s)

    b = base or {}
    row("文長 平均", st["len_mean"], b.get("len_mean"), "{:.1f}")
    row("文長 標準偏差", st["len_sd"], b.get("len_sd"), "{:.1f}")
    row("文長 変動係数", st["len_cv"], b.get("len_cv"))
    print(f"  {'同じ長さの3連続':<16}{st['even_runs']} 箇所")
    row("読点/文", st["commas_per_sent"], b.get("commas_per_sent"))
    print("  助詞+読点（1000字あたり）")
    for p, v in st["particle_comma"].items():
        bv = b.get("particle_comma", {}).get(p) if base else None
        if v or bv:
            row("  " + p, v, bv)
    print("  文頭の接続詞・副詞（1000字あたり）")
    keys = sorted(set(st["starts"]) | set(b.get("starts", {})),
                  key=lambda k: -st["starts"].get(k, 0))
    for k in keys[:10]:
        row("  " + k, st["starts"].get(k, 0.0), b.get("starts", {}).get(k, 0.0) if base else None)
    print("  文末の上位: " + " / ".join(f"…{e}×{n}" for e, n in st["endings"]))
    print(f"  横棒 [—―–]: {st['dashes']}   「これにより」: {st['koreniyori']}")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("files", nargs="+")
    p.add_argument("--baseline", nargs="*", default=[],
                   help="本人が素で書いた過去の文章（合算して比較対象にする）")
    args = p.parse_args()
    base = None
    if args.baseline:
        raw = "\n\n".join(open(f, encoding="utf-8").read() for f in args.baseline)
        base = stats(raw)
        show("baseline（本人）", base)
    for f in args.files:
        show(f, stats(open(f, encoding="utf-8").read()), base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
