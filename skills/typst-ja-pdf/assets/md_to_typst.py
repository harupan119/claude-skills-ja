#!/usr/bin/env python3
"""report.md から Typst ソース（report.typ）を生成する。

report.md を正本とし、PDF はそこから機械的に作る。本文を直接 Typst で書くと
正本と提出物が乖離するため、変換を挟む。

------------------------------------------------------------------------
これは typst-ja-pdf スキルの実装例である。作業フォルダに写して使う。
レポートごとに直す箇所は次の3つ。それ以外はそのまま動く。

1. EQUATIONS  — 本文の `$…\\tag{n}$` に対応する Typst の数式。番号をキーにする。
                文書順と番号の一致は変換時に検査するので、抜けや順序違いは
                その場で落ちる。
2. PREAMBLE の表紙 — 科目名・レポート種別・テーマ・担当教員・提出日・
                学籍番号・氏名。
3. PREAMBLE のフォント — 既定は本文 MS 明朝／見出し MS ゴシック／欧文
                Times New Roman。替える時は references/fonts.md の落とし穴を
                先に読む。数式とコードブロックは本文と別のフォント列で
                組まれるため、個別の指定が要る。

想定する report.md の書き方:
  - 見出しは `##`（章）〜`####`。`## 要旨` より前は表紙に置き換えるので捨てる
  - 表は GFM のパイプ表。直前の行に `表n: …` の形でキャプションを書く
  - 図は `![キャプション](figures/xxx.png)`
  - 数式は `$…\\tag{n}$` を単独行に置く
  - コードは ``` のフェンス
------------------------------------------------------------------------
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "report.md")
DST = os.path.join(HERE, "report.typ")

# 数式は LaTeX から Typst 構文へ手で対応させる（tag 番号をキーにする）。
# Typst 側は #set math.equation(numbering: "(1)") で自動採番するため、
# 文書順が tag 番号と一致していることを変換時に検査する。
EQUATIONS = {
    1: '"成功探索の平均キー比較回数" = (N+1)/2',
    2: '"キー比較回数" <= ceil(log_2 (N+1)) + 1',
    3: 'alpha = N/m',
    4: '"成功探索:" quad 1 + alpha/2',
    5: '"不成功探索:" quad alpha',
    6: 'h_"除算" (k) = k mod m',
    7: 'h_"乗算" (k) = floor(((k dot A mod 2^32) dot m) / 2^32), quad A = 2654435769',
    8: 'h_"撹拌" (k) = "mix"(k) mod m',
    9: 'Q^* = (P_B - P_A) / (t_A - t_B)',
    10: 'h_"線形" (k, i) = (h_1 (k) + i) mod m',
    11: 'h_"二重" (k, i) = (h_1 (k) + i dot h_2 (k)) mod m',
    12: 'h_2 (k) = 1 + (k mod (m-2))',
    13: '"線形探査・成功探索:" quad 1/2 (1 + 1/(1-alpha))',
    14: '"線形探査・不成功探索:" quad 1/2 (1 + 1/(1-alpha)^2)',
    15: '"二重ハッシュ・成功探索:" quad 1/alpha ln 1/(1-alpha)',
    16: '"二重ハッシュ・不成功探索:" quad 1/(1-alpha)',
    17: 'alpha_"OA" = 12/(16 + 8/alpha_"chain")',
}

PREAMBLE = r'''// report.md から md_to_typst.py が生成する。直接編集しない。
#set page(
  paper: "a4",
  margin: (top: 25mm, bottom: 22mm, left: 20mm, right: 20mm),
  numbering: "1",
)
// 和文は MS 明朝、欧文は Times New Roman、見出しは MS ゴシック。
// 3番目以降は代替である。⌈ ⌉ ⌊ ⌋ はどの本文用フォントにも字形が無く、
// 指定しないと処理系任せの代替に落ちて床と天井の区別が失われるため、
// 数式フォントを明示して式(2)と同じ字形に固定する。
#set text(
  font: ("Times New Roman", "MS Mincho", "New Computer Modern Math",
         "Hiragino Mincho ProN", "Hiragino Sans"),
  lang: "ja", size: 10.5pt,
)
#set par(justify: true, leading: 0.8em, first-line-indent: (amount: 1em, all: true))
#set math.equation(numbering: "(1)", supplement: none)
// 数式は本文と別のフォント列で組まれる。数式フォントに和文が無いため、指定しないと
// 式中の「成功探索」等が処理系任せの代替（中国語フォント等）で描かれる。
#show math.equation: set text(font: ("New Computer Modern Math", "MS Mincho"))
#show heading: it => block(above: 1.4em, below: 0.7em)[
  #set text(font: ("MS Gothic", "Hiragino Sans"), weight: "bold")
  #it.body
]
#show heading.where(level: 1): it => block(above: 1.6em, below: 0.9em)[
  #set text(font: ("MS Gothic", "Hiragino Sans"), weight: "bold", size: 14pt)
  #it.body
]
#show heading.where(level: 2): it => block(above: 1.4em, below: 0.7em)[
  #set text(font: ("MS Gothic", "Hiragino Sans"), weight: "bold", size: 12pt)
  #it.body
]
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em)[
  #set text(font: ("MS Gothic", "Hiragino Sans"), weight: "bold", size: 11pt)
  #it.body
]
#show raw.where(block: true): it => block(
  fill: rgb("#f5f5f5"), inset: 7pt, radius: 2pt, width: 100%,
  text(font: ("Menlo", "MS Gothic"), size: 8.5pt, it),
)
#show raw.where(block: false): it => text(font: ("Menlo", "MS Gothic"), size: 9pt, it)
#set table(stroke: 0.5pt + rgb("#666666"), inset: 4pt)
// 表のキャプションは表の上、図のキャプションは図の下に置く。
// figure を breakable にして、長い表でもキャプションと本体が別ページに分かれないようにする。
#show figure: set block(breakable: true)
#show figure.where(kind: table): set figure.caption(position: top)
#show figure.caption: it => text(size: 9.5pt, it.body)

// ---------------- 表紙（ここはレポートごとに書き換える）----------------
#align(center)[
  #v(60mm)
  #text(font: ("MS Gothic", "Hiragino Sans"), size: 17pt, weight: "bold")[科目名]
  #v(8mm)
  #text(font: ("MS Gothic", "Hiragino Sans"), size: 17pt, weight: "bold")[レポート種別]
  #v(30mm)
  #table(
    columns: (32mm, 92mm),
    align: (center + horizon, left + horizon),
    inset: 6pt,
    [テーマ], [レポートの題],
    [担当教員], [教員名],
    [提出日], [20XX 年 X 月 X 日],
    [学籍番号], [00000000],
    [氏名], [氏名],
  )
]
#pagebreak()

'''

# --------------------------------------------------------------------------
# インライン記法の変換
# --------------------------------------------------------------------------
SPECIAL = "\\#$*_`<>@[]~"


def esc(s):
    """Typst マークアップの特殊文字を退避する。"""
    out = []
    for ch in s:
        if ch in SPECIAL:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def inline(s):
    """`コード` と **太字** を保ったまま、残りをエスケープする。"""
    slots = []

    def stash(text):
        slots.append(text)
        return "\x00%d\x00" % (len(slots) - 1)

    # 1. インラインコード
    s = re.sub(r"`([^`]+)`", lambda m: stash("`" + m.group(1) + "`"), s)
    # 2. 太字（Typst は *…*）
    s = re.sub(r"\*\*([^*]+)\*\*", lambda m: stash("*" + esc(m.group(1)) + "*"), s)
    # 3. 残りをエスケープ
    s = esc(s)
    # 4. 退避した部分を戻す（エスケープで \x00 は壊れないが順序に注意）
    s = re.sub(r"\\?\x00(\d+)\\?\x00", lambda m: slots[int(m.group(1))], s)
    return s


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def png_size(path):
    """PNG の IHDR から (幅, 高さ) を読む。Pillow に依存しない。"""
    import struct
    with open(os.path.join(HERE, path), "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def image_width(path):
    """縦横比から本文中の幅を決める。横長（2枚組）は大きく、単独図は小さくする。"""
    size = png_size(path)
    if not size:
        return "80%"
    w, h = size
    return "96%" if w / h >= 1.8 else "76%"


def table_end(lines, start):
    """表の直後の行番号を返す（start は見出し行）。"""
    j = start + 2
    while j < len(lines) and lines[j].startswith("|"):
        j += 1
    return j


def emit_table(lines, start, caption):
    """見出し行 start から表を Typst の figure として組み立てる。"""
    header = split_row(lines[start])
    ncol = len(header)
    rows = [split_row(lines[j]) for j in range(start + 2, table_end(lines, start))]
    size = 8 if ncol >= 6 else 9
    buf = ["#figure("]
    buf.append("  text(size: %dpt)[#table(" % size)
    buf.append("    columns: %d," % ncol)
    buf.append("    align: %s," % ("center + horizon" if ncol >= 4 else "left + horizon"))
    buf.append("    table.header(%s)," % ", ".join("[*%s*]" % inline(c) for c in header))
    for r in rows:
        cells = (r + [""] * ncol)[:ncol]
        buf.append("    %s," % ", ".join("[%s]" % inline(c) for c in cells))
    buf.append("  )],")
    if caption:
        buf.append("  caption: [%s]," % inline(caption))
    buf.append("  kind: table, supplement: none, numbering: none,")
    buf.append(")\n")
    return "\n".join(buf)


def main():
    text = open(SRC, encoding="utf-8").read()
    lines = text.split("\n")
    out = [PREAMBLE]
    i = 0
    eq_seen = 0
    n_tables = n_figs = n_code = 0
    # 表紙に置き換えるため、先頭の題名ブロック（最初の "## 要旨" まで）は捨てる
    while i < len(lines) and not lines[i].startswith("## 要旨"):
        i += 1

    while i < len(lines):
        line = lines[i]

        # 見出し
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            level = len(m.group(1)) - 1
            body = inline(m.group(2))
            # 章頭で改ページする。ただし付録は参考文献に続けて置く（短いので1章1ページは無駄）。
            if level == 1 and not m.group(2).startswith("付録"):
                out.append("#pagebreak(weak: true)")
            out.append("=" * level + " " + body + "\n")
            i += 1
            continue

        # 水平線は章の区切りなので落とす（章頭で改ページする）
        if line.strip() == "---":
            i += 1
            continue

        # コードブロック
        if line.startswith("```"):
            lang = line[3:].strip()
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].startswith("```"):
                buf.append(lines[j])
                j += 1
            body = "\n".join(buf)
            fence = "`" * max(4, (max((len(x) for x in re.findall(r"`+", body)), default=0) + 1))
            out.append(fence + lang + "\n" + body + "\n" + fence + "\n")
            n_code += 1
            i = j + 1
            continue

        # 数式
        m = re.match(r"^\$\$(.*)\\tag\{(\d+)\}\$\$$", line.strip())
        if m:
            tag = int(m.group(2))
            eq_seen += 1
            if tag != eq_seen:
                sys.exit("式の順序が番号と一致しない: %d 番目に tag=%d" % (eq_seen, tag))
            if tag not in EQUATIONS:
                sys.exit("式 %d の Typst 変換が未定義" % tag)
            out.append("$ " + EQUATIONS[tag] + " $\n")
            i += 1
            continue

        # 画像（直後の **図N: …** をキャプションとして扱う）
        m = re.match(r"^!\[[^\]]*\]\(([^)]+)\)\s*$", line)
        if m:
            path = m.group(1)
            cap = None
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                cm = re.match(r"^\*\*(図\d+:.*)\*\*$", lines[j].strip())
                if cm:
                    cap = cm.group(1)
                    i = j
            width = image_width(path)
            out.append("#figure(")
            out.append('  image("%s", width: %s),' % (path, width))
            if cap:
                out.append("  caption: [%s]," % inline(cap))
            out.append("  kind: image, supplement: none, numbering: none,")
            out.append(")\n")
            n_figs += 1
            i += 1
            continue

        # 表のキャプション（**表N: …**）→ 直後の表と1つの figure にまとめる。
        # キャプションだけが前ページに残るのを防ぐ。
        m = re.match(r"^\*\*(表\d+:.*)\*\*$", line.strip())
        if m:
            cap = m.group(1)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if (j + 1 < len(lines) and lines[j].startswith("|")
                    and re.match(r"^\|[\s:\-|]+\|$", lines[j + 1])):
                out.append(emit_table(lines, j, cap))
                n_tables += 1
                i = table_end(lines, j)
                continue
            out.append("#block(above: 1.1em, below: 0.4em)[%s]" % inline(cap))
            i += 1
            continue

        # キャプションのない表
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1]):
            out.append(emit_table(lines, i, None))
            n_tables += 1
            i = table_end(lines, i)
            continue

        # 箇条書き
        m = re.match(r"^(\s*)- (.*)$", line)
        if m:
            out.append(m.group(1) + "- " + inline(m.group(2)))
            i += 1
            continue
        m = re.match(r"^(\s*)(\d+)\. (.*)$", line)
        if m:
            out.append(m.group(1) + m.group(2) + ". " + inline(m.group(3)))
            i += 1
            continue

        # 空行・本文
        if not line.strip():
            out.append("")
        else:
            out.append(inline(line))
        i += 1

    open(DST, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("→ report.typ を生成した")
    print("   数式 %d 本 / 表 %d 件 / 図 %d 件 / コードブロック %d 件" %
          (eq_seen, n_tables, n_figs, n_code))
    if eq_seen != len(EQUATIONS):
        sys.exit("式の数が対応表と合わない: 本文 %d / 対応表 %d" % (eq_seen, len(EQUATIONS)))


if __name__ == "__main__":
    main()
