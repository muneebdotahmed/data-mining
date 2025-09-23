#!/usr/bin/env python3
"""
Extract exam questions/topics from a PDF with layout-aware parsing
while preserving math/LaTeX symbols using pdfminer.six.

Output: one question/topic per line in a UTF-8 text file.

Usage:
  python3 tools/extract_exam_questions.py --pdf Exam_Questions_Summary.pdf --out data/exam_questions.txt

Heuristics:
  - Reads lines in visual order (top→bottom, left→right).
  - Starts a new item when encountering bullets/numbers or large vertical gaps.
  - Ends an item when encountering '?' or another clear bullet/numbered start.
  - Keeps formula characters as emitted by pdfminer (best-available text fidelity).
"""
import argparse
import os
import re
from dataclasses import dataclass
from typing import List, Tuple

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextBox, LTTextContainer, LTTextLine, LTTextLineHorizontal


@dataclass
class Line:
    page: int
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    avg_size: float


def iter_lines(layout) -> List[LTTextLine]:
    out = []
    for element in layout:
        if isinstance(element, LTTextBox):
            for line in element:
                if isinstance(line, (LTTextLine, LTTextLineHorizontal)):
                    out.append(line)
        elif isinstance(element, LTTextContainer):
            for line in element:
                if isinstance(line, (LTTextLine, LTTextLineHorizontal)):
                    out.append(line)
    return out


def avg_font_size(line: LTTextLine) -> float:
    sizes = [obj.size for obj in getattr(line, "_objs", []) if isinstance(obj, LTChar)]
    return sum(sizes) / len(sizes) if sizes else 0.0


def collect_ordered_lines(pdf_path: str) -> List[Line]:
    lines: List[Line] = []
    for page_idx, layout in enumerate(extract_pages(pdf_path), start=1):
        for line in iter_lines(layout):
            text = line.get_text().strip()
            if not text:
                continue
            x0, y0, x1, y1 = line.bbox
            lines.append(Line(page_idx, text, x0, y0, x1, y1, avg_font_size(line)))
    # Sort visual order: page asc, y desc (top first), x asc
    lines.sort(key=lambda l: (l.page, -l.y1, l.x0))
    return lines


BULLET_RE = re.compile(r"^(?:[-\u2022\u2219•◦·]|\d{1,3}[.)]|\(?\d{1,3}\)?[.)]?|[a-zA-Z][.)])\s+")
HEADER_RE = re.compile(r"^(?:page\s*\d+|\d{4}|section|part|final|midterm|exam)\b", re.I)


def extract_questions(lines: List[Line]) -> List[str]:
    items: List[str] = []
    buf: List[str] = []
    last_y = None
    last_size = None

    def flush():
        nonlocal buf
        if buf:
            s = " ".join(x.strip() for x in buf).strip()
            s = re.sub(r"\s+", " ", s)
            if s:
                items.append(s)
        buf = []

    for ln in lines:
        text = ln.text
        if HEADER_RE.match(text.lower()):
            # Ignore likely headers/footers/years
            continue

        # Large vertical gap => new item
        if last_y is not None and last_size is not None:
            gap = (last_y - ln.y1)
            if gap > max(20.0, 2.2 * last_size):
                flush()

        # New bullet/numbering => new item
        if BULLET_RE.match(text):
            flush()
            # Strip bullet prefix for cleanliness
            text = BULLET_RE.sub("", text)

        buf.append(text)

        # End when a line clearly ends with a question mark
        if text.rstrip().endswith("?"):
            flush()

        last_y = ln.y1
        last_size = ln.avg_size if ln.avg_size else last_size

    flush()
    # Deduplicate while preserving order (in case of repeated headings)
    seen = set()
    unique_items = []
    for s in items:
        if s not in seen:
            seen.add(s)
            unique_items.append(s)
    return unique_items


def main():
    ap = argparse.ArgumentParser(description="Extract exam questions/topics from a PDF into a text list")
    ap.add_argument("--pdf", required=True, help="Path to exam PDF")
    ap.add_argument("--out", required=True, help="Output .txt path (one item per line)")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    lines = collect_ordered_lines(args.pdf)
    items = extract_questions(lines)
    with open(args.out, "w", encoding="utf-8") as f:
        for s in items:
            f.write(s + "\n")
    print(f"Wrote exam items: {args.out}  (count={len(items)})")


if __name__ == "__main__":
    main()

