#!/usr/bin/env python3
"""sources/manifest.json に載せた原本を取得し、ハッシュで固定する。

- kind=git  : 指定コミットを浅く clone し、paths に挙げたファイルだけ複製する
- kind=http : ファイルを取得し、SHA-256 を lock.json に記録する（2回目以降は照合）

再配布可（redistributable=true）のものは sources/mirror/<id>/ に置き、git 管理する。
それ以外は sources/mirror/_local/<id>/ に置く。_local は .gitignore で除外してあり、
手元での参照専用。ライセンスを確認できていない原本を公開リポジトリに入れないため。

使い方:
  python3 sources/mirror.py            # 全件
  python3 sources/mirror.py --only ID  # 1件だけ
  python3 sources/mirror.py --verify   # 取得せず、手元の複製と lock.json の一致だけ確認
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest.json"
LOCK = ROOT / "lock.json"
UA = "claude-skills-ja-mirror/1.0 (+https://github.com/harupan119/claude-skills-ja)"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def dest_dir(src: dict) -> Path:
    base = ROOT / "mirror"
    return base / src["id"] if src.get("redistributable") is True else base / "_local" / src["id"]


def fetch_git(src: dict, out: Path) -> dict:
    files = {}
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q", tmp], check=True)
        subprocess.run(["git", "-C", tmp, "fetch", "-q", "--depth", "1", src["url"], src["commit"]], check=True)
        subprocess.run(["git", "-C", tmp, "checkout", "-q", "FETCH_HEAD"], check=True)
        for rel in src["paths"]:
            s = Path(tmp) / rel
            if not s.is_file():
                raise FileNotFoundError(f"{src['id']}: {rel} がコミット {src['commit'][:7]} に無い")
            d = out / rel
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
            files[rel] = sha256(d)
    return files


def fetch_http(src: dict, out: Path) -> dict:
    name = src.get("filename") or src["url"].rstrip("/").rsplit("/", 1)[-1]
    d = out / name
    d.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(src["url"], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r, d.open("wb") as f:
        shutil.copyfileobj(r, f)
    return {name: sha256(d)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
    failed = []

    for src in manifest["sources"]:
        if a.only and src["id"] != a.only:
            continue
        out = dest_dir(src)
        if a.verify:
            want = lock.get(src["id"], {}).get("files", {})
            if not want:
                print(f"--   {src['id']}: 未取得")
                continue
            bad = [n for n, h in want.items() if not (out / n).is_file() or sha256(out / n) != h]
            print(f"{'NG' if bad else 'OK'}   {src['id']}" + (f": {bad}" if bad else ""))
            if bad:
                failed.append(src["id"])
            continue
        try:
            files = fetch_git(src, out) if src["kind"] == "git" else fetch_http(src, out)
        except Exception as e:  # 取得失敗は記録して次へ（ネットワーク制限下でも他の原本は取る）
            print(f"FAIL {src['id']}: {e}", file=sys.stderr)
            failed.append(src["id"])
            continue
        prev = lock.get(src["id"], {}).get("files")
        if prev and prev != files:
            # 原本が差し替わった。黙って上書きせず、差分として報告する
            print(f"CHANGED {src['id']}: ハッシュが lock.json と不一致。更新内容を読んでから lock を更新すること", file=sys.stderr)
            failed.append(src["id"])
            continue
        lock[src["id"]] = {"retrieved": date.today().isoformat(), "files": files}
        print(f"OK   {src['id']} -> {out.relative_to(ROOT)} ({len(files)} files)")

    if not a.verify:
        LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
