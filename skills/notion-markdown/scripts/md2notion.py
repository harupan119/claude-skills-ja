#!/usr/bin/env python3
"""通常の Markdown を Notion 拡張 Markdown に変換し、送信前に壊れる箇所を検出する。

Notion MCP (`mcp__notion__API-update-page-markdown` / `API-post-page`) が受け取る
Markdown は方言で、素の Markdown をそのまま送ると数式・太字・表が崩れる。

サブコマンド:
  lint     : 送信すると崩れる箇所を行番号付きで報告する（変換はしない）
  convert  : 機械的に直せるものを変換して出力する
  split    : 変換済みファイルを送信可能なサイズのチャンクに割る

依存なし（標準ライブラリのみ）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 1リクエストで送れるおおよその上限。実測では JSON 化後 ~68KB で切断されたため、
# 日本語（1文字≒3バイト、JSON エスケープでさらに増える）を見込んで安全側に置く。
DEFAULT_CHUNK_CHARS = 12000


# --------------------------------------------------------------------------
# 変換
# --------------------------------------------------------------------------

def _stash_block_math(text: str) -> tuple[str, list[str]]:
    """ブロック数式を退避する。インライン変換の誤爆を防ぐため必ず先に呼ぶ。"""
    blocks: list[str] = []

    def stash(m: re.Match) -> str:
        blocks.append(m.group(1).strip())
        return f"\x00BLOCK{len(blocks) - 1}\x00"

    return re.sub(r"\$\$(.+?)\$\$", stash, text, flags=re.DOTALL), blocks


def _restore_block_math(text: str, blocks: list[str]) -> str:
    """`$$` を独立行に置いて戻す。Notion は同一行に閉じた `$$...$$` を数式と見ない。"""
    text = re.sub(
        r"\x00BLOCK(\d+)\x00",
        lambda m: "$$\n" + blocks[int(m.group(1))] + "\n$$",
        text,
    )
    # `**(f)** $$` のように行頭以外から始まると開始デリミタと認識されない
    text = re.sub(r"(?<=[^\n])(\$\$\n)", r"\n\1", text)
    # 閉じた直後に文が続く場合も同様に切る
    text = re.sub(r"(\n\$\$)(?=[^\n])", r"\1\n", text)
    return text


def convert_math(text: str) -> str:
    """インライン数式を `$`...`$` 形式に、ブロック数式を独立行の `$$` にする。"""
    text, blocks = _stash_block_math(text)
    text = re.sub(r"\$([^$\n]+?)\$", lambda m: f"$`{m.group(1)}`$", text)
    return _restore_block_math(text, blocks)


def convert_table_separators(text: str) -> str:
    """表の区切り行の中央揃え/右揃え記法を `---` に統一する。

    Notion のパーサは `:--:` を区切りと認識せず、データ行として表に混入させる。
    """
    def fix(m: re.Match) -> str:
        cells = m.group(0).strip().strip("|").split("|")
        return "|" + "|".join("---" for _ in cells) + "|"

    return re.sub(r"^\|[\s:\-|]+\|\s*$", fix, text, flags=re.MULTILINE)


def shift_headings(text: str, mapping: dict[int, int]) -> str:
    """見出しレベルを付け替える。深い方から処理して衝突を避ける。"""
    for depth in sorted(mapping, reverse=True):
        src, dst = "#" * depth, "#" * mapping[depth]
        text = re.sub(rf"^{src} ", f"\x01{dst} ", text, flags=re.MULTILINE)
    return text.replace("\x01", "")


def auto_heading_map(text: str) -> dict[int, int]:
    """H4 以降を含む場合に、H1〜H3 へ収まるよう詰める写像を決める。

    Notion の見出しは H1/H2/H3 まで。H4 以降はただの段落になり階層が失われる。
    """
    used = sorted({len(m.group(1)) for m in re.finditer(r"^(#{1,6}) ", text, re.MULTILINE)})
    if not used or used[-1] <= 3:
        return {}
    # 使われている深さを浅い順に 1,2,3... へ詰める（4段以上あれば3で頭打ち）
    return {depth: min(i + 1, 3) for i, depth in enumerate(used)}


def strip_title(text: str) -> tuple[str | None, str]:
    """先頭の H1 をページタイトルとして抜き出す。Notion ではタイトルは本文外にある。"""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            del lines[i]
            return title, "\n".join(lines)
    return None, text


def convert(text: str, *, shift: bool = True, drop_title: bool = True) -> tuple[str | None, str]:
    title = None
    if drop_title:
        title, text = strip_title(text)
    if shift:
        mapping = auto_heading_map(text)
        if mapping:
            text = shift_headings(text, mapping)
    text = convert_table_separators(text)
    text = convert_math(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return title, text


# --------------------------------------------------------------------------
# 検査
# --------------------------------------------------------------------------

class Finding:
    def __init__(self, line: int, kind: str, detail: str, fixable: bool):
        self.line, self.kind, self.detail, self.fixable = line, kind, detail, fixable

    def __str__(self) -> str:
        mark = "auto" if self.fixable else "MANUAL"
        return f"  L{self.line:<5} [{mark}] {self.kind}: {self.detail}"


def lint(text: str) -> list[Finding]:
    """送信すると崩れる箇所を洗い出す。converted 済みのテキストにも使える。"""
    findings: list[Finding] = []
    stashed, _ = _stash_block_math(text)
    stashed_lines = stashed.split("\n")
    lines = text.split("\n")

    for i, line in enumerate(lines, 1):
        # 太字スパンの内側に数式があると ** の位置がずれる。
        # Notion は数式を先に切り出すため、`**$x$ を証明**` が `$x$** を証明**` になる。
        # 太字の「外」にある数式（`**(b)** $x$ より`）は壊れないので対象外。
        for m in re.finditer(r"\*\*(.+?)\*\*", line):
            if "$" in m.group(1):
                findings.append(Finding(
                    i, "太字の内側の数式",
                    f"** がずれる。数式を太字の外に出す → {m.group(0)[:48]}",
                    fixable=False))

        # 見出しに数式を入れると表示が不安定
        if line.startswith("#") and ("$" in line):
            findings.append(Finding(
                i, "見出し内の数式",
                "見出しはプレーンテキストにする",
                fixable=False))

        # 表の中央揃え記法
        if re.match(r"^\|[\s:\-|]+\|\s*$", line) and ":" in line:
            findings.append(Finding(
                i, "表の区切り行",
                ":--: は区切りと認識されずデータ行になる → --- に統一",
                fixable=True))

        # H4 以降
        m = re.match(r"^(#{4,6}) ", line)
        if m:
            findings.append(Finding(
                i, f"H{len(m.group(1))} 見出し",
                "Notion は H3 までしかない。階層を詰める",
                fixable=True))

    # 1行に閉じたブロック数式（要変換）
    for i, line in enumerate(lines, 1):
        if re.match(r"^\$\$.+\$\$\s*$", line):
            findings.append(Finding(
                i, "1行完結のブロック数式",
                "$$ は独立行に置く",
                fixable=True))

    # 未変換のインライン数式（stash 後に残る $ で判定）
    for i, line in enumerate(stashed_lines, 1):
        if re.search(r"(?<!\$)(?<!`)\$(?!`)(?!\$)", line):
            findings.append(Finding(
                i, "未変換のインライン数式",
                "$x$ ではなく $`x`$ 形式にする",
                fixable=True))

    # \text{...} の中の入れ子数式（KaTeX では通るが Notion のパーサが壊す）
    for i, line in enumerate(lines, 1):
        if re.search(r"\\text\{[^}]*\$", line):
            findings.append(Finding(
                i, "\\text{} 内の入れ子数式",
                "\\text{$x$ ...} は避け、数式を \\text{} の外に出す",
                fixable=False))

    findings.sort(key=lambda f: f.line)
    return findings


# --------------------------------------------------------------------------
# 分割
# --------------------------------------------------------------------------

def split_by_heading(text: str, limit: int = DEFAULT_CHUNK_CHARS) -> list[str]:
    """H1 境界を優先して、送信可能なサイズのチャンクに割る。

    1リクエストが大きすぎると MCP 側で切断されるため、
    先頭チャンクを replace_content、以降を insert_content(position=end) で送る。
    """
    parts = re.split(r"^(?=# )", text, flags=re.MULTILINE)
    chunks: list[str] = []
    buf = ""
    for part in parts:
        if buf and len(buf) + len(part) > limit:
            chunks.append(buf)
            buf = part
        else:
            buf += part
    if buf.strip():
        chunks.append(buf)

    # H1 単体で上限を超える場合は H2 でさらに割る
    out: list[str] = []
    for chunk in chunks:
        if len(chunk) <= limit:
            out.append(chunk)
            continue
        subs = re.split(r"^(?=## )", chunk, flags=re.MULTILINE)
        buf = ""
        for sub in subs:
            if buf and len(buf) + len(sub) > limit:
                out.append(buf)
                buf = sub
            else:
                buf += sub
        if buf.strip():
            out.append(buf)
    return out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def cmd_lint(args) -> int:
    text = Path(args.input).read_text(encoding="utf-8")
    findings = lint(text)
    print(f"{args.input}: {len(findings)} 件")
    for f in findings:
        print(f)
    manual = [f for f in findings if not f.fixable]
    if manual:
        print(f"\n手で直す必要があるもの: {len(manual)} 件")
    return 1 if manual else 0


def cmd_convert(args) -> int:
    text = Path(args.input).read_text(encoding="utf-8")
    title, converted = convert(
        text, shift=not args.no_shift, drop_title=not args.keep_title
    )
    out = Path(args.output) if args.output else None
    if out:
        out.write_text(converted, encoding="utf-8")

    remaining = lint(converted)
    manual = [f for f in remaining if not f.fixable]

    n_block = len(re.findall(r"^\$\$$", converted, re.M)) // 2
    print(f"input      : {args.input}")
    print(f"title      : {title or '(なし)'}")
    print(f"chars      : {len(converted):,}")
    print(f"inline math: {converted.count('$`')}")
    print(f"block math : {n_block}")
    h = [len(re.findall(rf"^{'#' * n} ", converted, re.M)) for n in (1, 2, 3)]
    print(f"H1/H2/H3   : {h[0]}/{h[1]}/{h[2]}")
    print(f"chunks     : {len(split_by_heading(converted))} "
          f"(上限 {DEFAULT_CHUNK_CHARS:,} 文字)")
    if out:
        print(f"output     : {out}")

    if manual:
        print(f"\n手で直す必要がある箇所 ({len(manual)} 件):")
        for f in manual:
            print(f)
    else:
        print("\n手で直す必要がある箇所: なし")
    return 0


def cmd_split(args) -> int:
    text = Path(args.input).read_text(encoding="utf-8")
    chunks = split_by_heading(text, args.limit)
    stem = Path(args.input).stem
    outdir = Path(args.outdir or Path(args.input).parent)
    outdir.mkdir(parents=True, exist_ok=True)
    for i, chunk in enumerate(chunks, 1):
        path = outdir / f"{stem}.part{i:02d}.md"
        path.write_text(chunk, encoding="utf-8")
        head = chunk.lstrip().split("\n", 1)[0][:40]
        print(f"part{i:02d}  {len(chunk):>7,} chars  {path}  # {head}")
    print(f"\n{len(chunks)} chunks. "
          f"part01 を replace_content、以降を insert_content(position=end) で順に送る。")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        prog="md2notion",
        description="Markdown を Notion 拡張 Markdown に変換・検査する")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("lint", help="崩れる箇所を報告する")
    pl.add_argument("input")
    pl.set_defaults(func=cmd_lint)

    pc = sub.add_parser("convert", help="変換して出力する")
    pc.add_argument("input")
    pc.add_argument("-o", "--output")
    pc.add_argument("--no-shift", action="store_true",
                    help="見出しレベルを詰めない")
    pc.add_argument("--keep-title", action="store_true",
                    help="先頭 H1 を本文に残す（既定は抜いてページタイトルに回す）")
    pc.set_defaults(func=cmd_convert)

    ps = sub.add_parser("split", help="送信サイズに割る")
    ps.add_argument("input")
    ps.add_argument("--limit", type=int, default=DEFAULT_CHUNK_CHARS)
    ps.add_argument("--outdir")
    ps.set_defaults(func=cmd_split)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
