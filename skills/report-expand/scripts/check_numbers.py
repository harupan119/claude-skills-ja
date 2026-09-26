#!/usr/bin/env python3
"""増量後の本文に、元データに無い数値が紛れ込んでいないかを洗い出す。

    python3 check_numbers.py expanded.md --source original.md data.csv results.csv

本文（フェンスドコードを除く）から数値を抜き出し、どの source にも現れない
ものを行番号つきで出す。一致判定は値で行う（1,234 = 1234、0.50 = 0.5）。

ここで出た数値が即ち捏造というわけではない。source の値から計算した比や差、
章節番号・図表番号も出る。出たものは1件ずつ「どの実測値から導いたか」を
確認し、説明できないものを消す。検出0件を目標にするのではなく、
全件に出所を付けられることを目標にする。
"""
import argparse
import re
import sys
from decimal import Decimal, InvalidOperation

# 直前が英数字なら識別子の一部（q1, x86 など）とみなす。日本語の直後の数値は拾う
# （\w は日本語にも一致するので使わない）
_B = r"(?<![A-Za-z0-9_.])"
NUM = re.compile(_B + r"[-−]?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\d])|" + _B + r"[-−]?\d+(?:\.\d+)?")
# 章節番号・図表番号・式番号・見出し番号は数値の主張ではないので除く
STRUCTURAL = [
    re.compile(r"^\s*#+\s*[\d.]+"),                       # 見出し行頭の番号
    re.compile(r"(図|表|式|付録|章|節|Fig\.?|Table|Eq\.?)\s*[(（]?\d+(?:[.-]\d+)*[)）]?"),
    re.compile(r"\d+(?:\.\d+)+\s*(節|章|項)"),
    re.compile(r"第\s*\d+\s*(章|節|項|回)"),
    re.compile(r"\d+(?:\.\d+)*\s*の通り"),
]


def normalize(token):
    t = token.replace(",", "").replace("−", "-")
    try:
        return Decimal(t).normalize()
    except InvalidOperation:
        return None


def strip_code(text):
    return re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.DOTALL)


def numbers_in(text, skip_structural):
    found = []
    for lineno, line in enumerate(text.split("\n"), 1):
        masked = line
        if skip_structural:
            for pat in STRUCTURAL:
                masked = pat.sub(lambda m: " " * len(m.group(0)), masked)
        for m in NUM.finditer(masked):
            value = normalize(m.group(0))
            if value is not None:
                found.append((lineno, m.group(0), value, line.strip()))
    return found


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("report")
    p.add_argument("--source", nargs="+", required=True,
                   help="元の本文・CSV など、使ってよい数値の出所")
    p.add_argument("--ignore", nargs="*", default=[],
                   help="常に許可する値（例: 0 1 2 100）")
    args = p.parse_args()

    allowed = set()
    for path in args.source:
        with open(path, encoding="utf-8") as f:
            allowed |= {v for _, _, v, _ in numbers_in(f.read(), skip_structural=False)}
    allowed |= {normalize(x) for x in args.ignore}

    with open(args.report, encoding="utf-8") as f:
        body = strip_code(f.read())

    unknown = [n for n in numbers_in(body, skip_structural=True) if n[2] not in allowed]
    for lineno, raw, _, line in unknown:
        print(f"L{lineno}: {raw}\t{line[:80]}")
    print(f"出所不明の数値: {len(unknown)} 件", file=sys.stderr)
    sys.exit(1 if unknown else 0)


if __name__ == "__main__":
    main()
