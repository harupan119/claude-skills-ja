#!/usr/bin/env python3
"""日本語本文の表記・文体を機械的に点検する（標準ライブラリのみ）。

基準値と規則の出典は textlint-ja のルール群と、その元になった JTF日本語標準スタイルガイド。
原本は sources/mirror/ にコミット固定で置いてある。対応表は references/style-metrics.md。

形態素解析をしないため、正規表現で近似している。拾えないもの（同一助詞の連続など）は
textlint 本体に任せる。ここで出るのは「読み直す箇所の候補」であり、機械的に全部直すものではない。

使い方:
  python3 ja_style_check.py report.md --mode academic
  python3 ja_style_check.py report.md --mode business --max-len 90 --allow-kanji 情報処理学会論文誌
  python3 ja_style_check.py report.md --prh sources/mirror/textlint-rule-ja-no-abusage/dict/prh.yml
"""
import argparse
import re
import sys
from collections import Counter

DASH = re.compile(r"[—―–]")
DOUBLE_NEG = re.compile(r"(ないでもない|ないことはない|ないことも(?:ない|ありません)|ないものではない|ないとは言い切れない|ないとは限らない|ないわけではない|なくはない|なくもない)")
REDUNDANT = [
    (re.compile(r"することが(?:でき|可能)"), "「することができる／可能」→「できる」"),
    (re.compile(r"であると(?:言え|いえ)"), "「であると言える」→「である」"),
    (re.compile(r"であると考えて(?:い|お)"), "「であると考えている」→「である」か「と考える」の片方"),
    # textlint-ja と同じく「処理を行う」と、カタカナ語・英字の目的語は除外する
    (re.compile(r"(?<![ァ-ヶーA-Za-z一-龥])(?!処理を)([一-龥]{2,})を(?:行|実行)[わいうえおっ]"), "「〜を行う」→「〜する」"),
]
WEAK = re.compile(r"かもしれ|かも。")
MISUSE = [
    (re.compile(r"([ぁ-ん一-龥])ずら(?:い|く|かっ)"), "「〜ずらい」→「〜づらい」"),
    (re.compile(r"可変する"), "「可変する」は不適切（「可変の」「変えられる」）"),
    (re.compile(r"[ヵヶ](?:月|所)"), "「ヵ月／ヶ所」→「か月／か所」（JTF 2.2.3）"),
]
RA_NUKI = re.compile(r"(?:見|来|着|寝|出|居|起き|食べ|決め|考え|覚え|答え|比べ|調べ)れ(?:る|ない|ます|た)")
CONJ = ("また", "さらに", "しかし", "しかしながら", "一方", "一方で", "そして", "したがって", "そのため", "加えて", "つまり", "なお", "ただし", "このように")
DESU = re.compile(r"(?:です|ます|でした|ました|ません|でしょう)[。！？]?$")
DEARU = re.compile(r"(?:である|だ|だった|であった|ない|なかった|[うくすつぬふむゆる]|た)[。！？]?$")


def load_prh(path):
    """prh 形式の辞書から (正規表現, 正しい表記) を読む。PyYAML に依存しないよう、
    `- expected:` と `patterns:` が1対1で並ぶ単純な形だけを扱う。"""
    rules, expected = [], None
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if line.startswith("- expected:"):
            expected = line.split(":", 1)[1].strip()
        elif line.startswith("patterns:") and expected:
            pat = line.split(":", 1)[1].strip()
            rx = pat[1:-1] if len(pat) > 2 and pat.startswith("/") and pat.endswith("/") else re.escape(pat)
            try:
                rules.append((re.compile(rx), expected))
            except re.error:
                pass  # JavaScript 固有の構文は読み飛ばす
            expected = None
    return rules


def body_lines(text):
    """コードフェンス・表・HTMLコメントを除いた (行番号, 行, 見出しか) を返す。"""
    fence = False
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence
            continue
        if fence or not s or s.startswith("|") or s.startswith("<!--"):
            continue
        yield i, line, s.startswith("#")


def sentences(line):
    # インラインコードと URL は判定対象から外す
    line = re.sub(r"`[^`]*`|\]\([^)]*\)|https?://\S+", "", line)
    parts = re.split(r"(?<=[。！？])", line)
    return [p.strip() for p in parts if p.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--mode", choices=["academic", "business", "casual"], default="academic")
    ap.add_argument("--max-len", type=int, default=100, help="1文の最大字数（textlint 既定 100、厳しめ 90）")
    ap.add_argument("--max-ten", type=int, default=3, help="1文の読点の上限（textlint 既定 3）")
    ap.add_argument("--max-kanji", type=int, default=6, help="漢字の連続の上限（textlint 既定 6）")
    ap.add_argument("--allow-kanji", nargs="*", default=[], help="漢字連続の例外にする固有名詞")
    ap.add_argument("--prh", help="誤用辞書（prh 形式）。textlint-rule-ja-no-abusage の dict/prh.yml を想定")
    a = ap.parse_args()
    prh = load_prh(a.prh) if a.prh else []

    text = open(a.file, encoding="utf-8").read()
    hits = []
    add = lambda n, rule, msg: hits.append((n, rule, msg))
    ends = Counter()
    ends_at = {"desu": [], "dearu": []}
    prev_conj = None
    kanji_run = re.compile("[一-龥々]{%d,}" % (a.max_kanji + 1))

    for n, line, heading in body_lines(text):
        if DASH.search(line):
            add(n, "dash", "ダッシュ [—―–] は和文で原則使わない（JTF 4.2.9）")
        if re.search(r"。 ", line):
            add(n, "space-after-kuten", "句点の直後に半角空白")
        for m in kanji_run.finditer(line):
            if not any(w in m.group() for w in a.allow_kanji):
                add(n, "kanji-run", f"漢字が{len(m.group())}字連続: {m.group()}")
        if heading:
            prev_conj = None
            continue
        for s in sentences(line):
            core = re.sub(r"[\s*_]", "", s)
            # 「」内は引用・語の言及として扱い、語句系の検査から外す（文長・読点は数える）
            prose = re.sub(r"「[^」]*」", "「」", s)
            if len(core) > a.max_len:
                add(n, "sentence-length", f"{len(core)}字（上限 {a.max_len}）: {core[:24]}…")
            if s.count("、") > a.max_ten:
                add(n, "max-ten", f"読点 {s.count('、')} 個（上限 {a.max_ten}）: {core[:24]}…")
            if s.count("が、") >= 2:
                add(n, "doubled-ga", "逆接の「が、」が1文に2回")
            for m in DOUBLE_NEG.finditer(prose):
                add(n, "double-negative", f"二重否定: {m.group()}")
            for rx, msg in REDUNDANT:
                if rx.search(prose):
                    add(n, "redundant", msg)
            if WEAK.search(prose):
                add(n, "weak-phrase", "弱い表現「かも（しれない）」")
            for rx, msg in MISUSE:
                if rx.search(prose):
                    add(n, "misuse", msg)
            for rx, want in prh:
                m = rx.search(prose)
                if m:
                    add(n, "misuse", f"誤用の疑い: {m.group()} → {m.expand(want.replace('$', chr(92)))}")
            if RA_NUKI.search(prose):
                add(n, "ra-nuki", f"ら抜きの疑い: {RA_NUKI.search(prose).group()}")
            if a.mode != "casual" and re.search(r"[!！?？]", s):
                add(n, "exclamation", "感嘆符・疑問符（和文では多用しない。JTF 4.2.1-2）")
            head = next((c for c in sorted(CONJ, key=len, reverse=True) if core.startswith(c)), None)
            if head and head == prev_conj:
                add(n, "doubled-conjunction", f"同じ接続詞が連続: {head}")
            prev_conj = head
            tail = re.sub(r"[）)」』\s]+$", "", core)
            if DESU.search(tail):
                ends["desu"] += 1
                ends_at["desu"].append(n)
            elif DEARU.search(tail):
                ends["dearu"] += 1
                ends_at["dearu"].append(n)

    # 文体の混在: 本文の多数派に対して少数派を報告する。academic はである調、business はですます調を正とする
    want = {"academic": "dearu", "business": "desu"}.get(a.mode) or max(ends, key=ends.get, default=None)
    if want:
        other = "desu" if want == "dearu" else "dearu"
        for n in ends_at[other]:
            add(n, "mixed-style", f"文体の混在（{'ですます' if other == 'desu' else 'である'}調の文末）")

    for n, rule, msg in sorted(hits):
        print(f"{a.file}:{n}: [{rule}] {msg}")
    by = Counter(r for _, r, _ in hits)
    print("--", " ".join(f"{k}={v}" for k, v in sorted(by.items())) or "no findings", file=sys.stderr)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
