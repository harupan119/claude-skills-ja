#!/usr/bin/env python3
"""docs/research-notes.md が引く論文の原本を取得・検証する。

    python3 docs/papers/fetch_papers.py            # 同梱PDFのハッシュを検証
    python3 docs/papers/fetch_papers.py --fetch    # 同梱できない原本を cache/ に取得して検証
    python3 docs/papers/fetch_papers.py --check-updates   # arXiv に新しい版が出ていないか調べる

manifest.json が正本。各論文の取得元URL（arXiv は版番号つき）、ライセンス、
SHA-256 を持つ。再配布が許されるライセンス（CC BY / CC BY-SA / CC0）のものだけ
pdf/ に同梱し、それ以外は cache/（.gitignore 済み）へ手元で取得する。
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "claude-skills-ja paper mirror (research citation check)"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def local_path(p):
    sub = "pdf" if p["redistributable"] else "cache"
    return os.path.join(HERE, sub, p["key"] + ".pdf")


def download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if not data.startswith(b"%PDF"):
        raise ValueError(f"PDF ではない応答: {url}")
    tmp = dest + ".part"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, dest)


def latest_arxiv_version(landing):
    m = re.search(r"arxiv\.org/abs/([\d.]+)v(\d+)", landing)
    if not m:
        return None, None
    req = urllib.request.Request(f"https://arxiv.org/abs/{m.group(1)}", headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", "replace")
    versions = [int(v) for v in re.findall(rf"{re.escape(m.group(1))}v(\d+)", html)]
    return int(m.group(2)), max(versions) if versions else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fetch", action="store_true", help="手元に無い原本を取得する")
    ap.add_argument("--check-updates", action="store_true", help="arXiv の新版を調べる")
    args = ap.parse_args()

    with open(os.path.join(HERE, "manifest.json"), encoding="utf-8") as f:
        papers = json.load(f)["papers"]

    bad = 0
    for p in papers:
        path = local_path(p)
        if not os.path.exists(path):
            if not args.fetch:
                state = "未取得（--fetch で取得）" if not p["redistributable"] else "欠落"
                bad += p["redistributable"]
                print(f"[--] {p['key']}: {state}")
                continue
            try:
                download(p["url"], path)
            except Exception as e:
                bad += 1
                print(f"[NG] {p['key']}: 取得失敗 {e}")
                continue
        digest = sha256(path)
        if digest == p["sha256"]:
            print(f"[OK] {p['key']}")
        else:
            bad += 1
            print(f"[NG] {p['key']}: SHA-256 不一致（取得元が差し替わった可能性。"
                  f"内容を確かめてから manifest を更新する） {digest}")

    if args.check_updates:
        for p in papers:
            try:
                pinned, latest = latest_arxiv_version(p["landing"])
            except Exception as e:
                print(f"[??] {p['key']}: 版の確認に失敗 {e}")
                continue
            if pinned and latest and latest > pinned:
                print(f"[UP] {p['key']}: v{pinned} → v{latest} が出ている。"
                      "引用した数値が変わっていないか確認する")

    print(f"問題: {bad} 件")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
