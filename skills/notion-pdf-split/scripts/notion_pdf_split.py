#!/usr/bin/env python3
import argparse
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except Exception as exc:
    raise SystemExit(
        "pypdf is required. Install with: python3 -m pip install pypdf\n"
        f"import error: {exc}"
    )


def split_ranges(total: int, parts: int):
    base = total // parts
    rem = total % parts
    ranges = []
    start = 0
    for i in range(parts):
        size = base + (1 if i < rem else 0)
        end = start + size
        ranges.append((start, end))
        start = end
    return ranges


def write_pdf(reader: PdfReader, start: int, end: int, out_path: Path):
    writer = PdfWriter()
    for i in range(start, end):
        writer.add_page(reader.pages[i])
    with out_path.open("wb") as f:
        writer.write(f)


def main():
    parser = argparse.ArgumentParser(description="Trim and split PDF for Notion")
    parser.add_argument("--input", required=True, help="Input PDF path")
    parser.add_argument("--drop-first", type=int, default=0, help="Pages to drop from beginning")
    parser.add_argument("--split", type=int, default=2, help="Number of output parts (>=1)")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"input not found: {src}")
    if args.drop_first < 0:
        raise SystemExit("--drop-first must be >= 0")
    if args.split < 1:
        raise SystemExit("--split must be >= 1")

    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(src))
    total = len(reader.pages)
    if args.drop_first >= total:
        raise SystemExit(f"--drop-first ({args.drop_first}) must be < total pages ({total})")

    trimmed_start = args.drop_first
    trimmed_total = total - trimmed_start

    trimmed_reader = PdfReader(str(src))

    if args.split == 1:
        out = out_dir / f"{src.stem}_trimmed.pdf"
        write_pdf(trimmed_reader, trimmed_start, total, out)
        print(f"source_pages={total}")
        print(f"trimmed_pages={trimmed_total}")
        print(str(out))
        return

    if args.split > trimmed_total:
        raise SystemExit(f"--split ({args.split}) must be <= trimmed pages ({trimmed_total})")

    ranges = split_ranges(trimmed_total, args.split)
    print(f"source_pages={total}")
    print(f"trimmed_pages={trimmed_total}")

    for idx, (a, b) in enumerate(ranges, start=1):
        out = out_dir / f"{src.stem}_part{idx}.pdf"
        write_pdf(trimmed_reader, trimmed_start + a, trimmed_start + b, out)
        print(f"part{idx}_pages={b-a}")
        print(str(out))


if __name__ == "__main__":
    main()
