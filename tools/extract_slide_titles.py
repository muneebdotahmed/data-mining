#!/usr/bin/env python3
"""
Extract likely slide titles (top-of-page headings) from a PDF while
preserving LaTeX/math characters, using pdfminer.six layout and font sizes.

Output format: one line per page as `page|title` (1-based page index).

Usage:
  python3 tools/extract_slide_titles.py --pdf "KDDM - data - 2.pdf" --out data/slides_topics.txt

Notes:
  - Requires: pdfminer.six
  - Heuristic: Pick the largest-font line in the top X% of each page.
  - Merges an immediately-adjacent second line if it shares similar font size.
"""
import argparse
import os
from dataclasses import dataclass
from statistics import mean
from typing import Iterable, List, Optional, Tuple

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextBox, LTTextContainer, LTTextLine, LTTextLineHorizontal


@dataclass
class LineInfo:
    page: int
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    avg_size: float


def iter_lines_from_layout(layout) -> Iterable[LTTextLine]:
    for element in layout:
        if isinstance(element, LTTextBox):
            for line in element:
                if isinstance(line, (LTTextLine, LTTextLineHorizontal)):
                    yield line
        elif isinstance(element, LTTextContainer):
            for line in element:
                if isinstance(line, (LTTextLine, LTTextLineHorizontal)):
                    yield line


def line_avg_font_size(line: LTTextLine) -> Optional[float]:
    sizes: List[float] = []
    for obj in getattr(line, "_objs", []):
        if isinstance(obj, LTChar):
            sizes.append(obj.size)
    if not sizes:
        return None
    return float(mean(sizes))


def extract_titles(pdf_path: str, top_ratio: float = 0.35, merge_threshold: float = 0.9) -> List[Tuple[int, str]]:
    results: List[Tuple[int, str]] = []
    for page_idx, layout in enumerate(extract_pages(pdf_path), start=1):
        page_height = getattr(layout, "height", None)
        if not page_height:
            page_height = 842.0  # default A4 height as a fallback

        # Collect all lines with coordinates and avg font size
        lines: List[LineInfo] = []
        for line in iter_lines_from_layout(layout):
            text = line.get_text().strip()
            if not text:
                continue
            avg_sz = line_avg_font_size(line)
            if avg_sz is None:
                continue
            x0, y0, x1, y1 = line.bbox
            lines.append(LineInfo(page_idx, text, x0, y0, x1, y1, avg_sz))

        if not lines:
            results.append((page_idx, ""))
            continue

        # Consider only lines in the top area of the page
        top_cut = page_height * (1 - top_ratio)
        top_lines = [ln for ln in lines if ln.y1 >= top_cut]
        if not top_lines:
            # fallback: take globally largest font line on page
            top_lines = lines

        # Choose the line with the largest avg font size; break ties by higher y
        top_lines.sort(key=lambda ln: (ln.avg_size, ln.y1), reverse=True)
        title = top_lines[0]

        # Try merging a second line directly below if font size similar (for 2-line titles)
        # Heuristic: same textbox proximity approximated via y-distance and size similarity
        candidates_below = [ln for ln in lines if (ln.y0 < title.y0 and abs(ln.avg_size - title.avg_size) / max(title.avg_size, 1e-6) >= 0)]
        # Sort by vertical proximity (closest below first)
        candidates_below.sort(key=lambda ln: abs(ln.y1 - title.y0))

        merged_text = title.text
        for ln in candidates_below:
            size_similarity = min(title.avg_size, ln.avg_size) / max(title.avg_size, ln.avg_size)
            vertically_close = (title.y0 - ln.y1) <= (title.avg_size * 1.6)
            horizontally_aligned = abs(ln.x0 - title.x0) <= max(10.0, title.avg_size * 0.8)
            if size_similarity >= merge_threshold and vertically_close and horizontally_aligned:
                merged_text = f"{merged_text} {ln.text}".strip()
                break

        results.append((page_idx, merged_text))
    return results


def main():
    ap = argparse.ArgumentParser(description="Extract slide page titles from a PDF (font-size & top-of-page heuristic)")
    ap.add_argument("--pdf", required=True, help="Path to slides PDF")
    ap.add_argument("--out", required=True, help="Output .txt path (one 'page|title' per line)")
    ap.add_argument("--top-ratio", type=float, default=0.35, help="Top-of-page ratio to search for titles")
    ap.add_argument("--merge-threshold", type=float, default=0.9, help="Font size similarity threshold for merging (0-1)")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    titles = extract_titles(args.pdf, top_ratio=args.top_ratio, merge_threshold=args.merge_threshold)
    with open(args.out, "w", encoding="utf-8") as f:
        for page, text in titles:
            f.write(f"{page}|{text}\n")
    print(f"Wrote slide titles: {args.out}  (pages={len(titles)})")


if __name__ == "__main__":
    main()

