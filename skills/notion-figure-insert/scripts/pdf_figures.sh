#!/usr/bin/env bash
# Helper for the notion-figure-insert skill: PDF page rendering / figure extraction / cropping.
# Requires: poppler (pdftoppm, pdfimages, pdfinfo), ImageMagick (magick).
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  pdf_figures.sh info <pdf>
      Show page count etc. (pdfinfo).

  pdf_figures.sh render <pdf> <outdir> [dpi=150]
      Render every page to <outdir>/page-NN.png for visual review.

  pdf_figures.sh list-images <pdf>
      List embedded raster images per page (pdfimages -list).
      Use this to find which page has a real embedded image worth
      extracting at full quality, vs. a page that is vector-drawn only.

  pdf_figures.sh extract-page <pdf> <page> <outdir>
      Extract all embedded raster images on one page as PNG
      (outdir/pfx-000.png, pfx-001.png, ...). Pick the largest one.

  pdf_figures.sh crop <in.png> <out.png> <WxH+X+Y>
      Crop a region (ImageMagick geometry) from in.png.

  pdf_figures.sh trim <in.png> <out.png> [border=20]
      Autotrim whitespace and re-add a small white border.
EOF
}

cmd="${1:-}"
shift || true

case "$cmd" in
  info)
    pdfinfo "$1"
    ;;
  render)
    pdf="$1"; outdir="$2"; dpi="${3:-150}"
    mkdir -p "$outdir"
    pdftoppm -png -r "$dpi" "$pdf" "$outdir/page"
    ls "$outdir"
    ;;
  list-images)
    pdfimages -list "$1"
    ;;
  extract-page)
    pdf="$1"; page="$2"; outdir="$3"
    mkdir -p "$outdir"
    pdfimages -png -f "$page" -l "$page" "$pdf" "$outdir/pfx"
    ls -la "$outdir"/pfx-*.png
    ;;
  crop)
    in="$1"; out="$2"; geom="$3"
    magick "$in" -crop "$geom" +repage "$out"
    ;;
  trim)
    in="$1"; out="$2"; border="${3:-20}"
    magick "$in" -trim +repage -bordercolor white -border "$border" "$out"
    ;;
  *)
    usage
    exit 1
    ;;
esac
