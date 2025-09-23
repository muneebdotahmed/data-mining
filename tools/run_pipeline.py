#!/usr/bin/env python3
"""
End-to-end pipeline to produce a mapping CSV:
  1) Extract slide titles from slides PDF (preserve math via pdfminer)
  2) Extract exam questions/topics from exam PDF
  3) Fuzzy-match slide topics to exam items and export a CSV

Usage:
  python3 tools/run_pipeline.py \
    --slides-pdf "KDDM - data - 2.pdf" \
    --exam-pdf "Exam_Questions_Summary.pdf" \
    --out results/mapped_topics.csv

Requires: pdfminer.six (for extraction)
"""
import argparse
import importlib
import os
import subprocess
import sys


def ensure_pdfminer() -> bool:
    try:
        importlib.import_module("pdfminer")
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="Run full matching pipeline (extract + match)")
    ap.add_argument("--slides-pdf", default="KDDM - data - 2.pdf")
    ap.add_argument("--exam-pdf", default="Exam_Questions_Summary.pdf")
    ap.add_argument("--slides-out", default="data/slides_topics.txt")
    ap.add_argument("--exam-out", default="data/exam_questions.txt")
    ap.add_argument("--out", default="results/mapped_topics.csv")
    ap.add_argument("--min-score", type=float, default=0.72)
    ap.add_argument("--max-matches", type=int, default=3)
    ap.add_argument("--aliases", help="Optional JSON synonyms map")
    args = ap.parse_args()

    if not ensure_pdfminer():
        print("ERROR: pdfminer.six is not installed.")
        print("Install it first, e.g.:\n  python3 -m pip install pdfminer.six")
        sys.exit(2)

    os.makedirs("data", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    # 1) Extract slide titles
    subprocess.check_call([
        sys.executable, "tools/extract_slide_titles.py",
        "--pdf", args.slides_pdf,
        "--out", args.slides_out,
    ])

    # 2) Extract exam items
    subprocess.check_call([
        sys.executable, "tools/extract_exam_questions.py",
        "--pdf", args.exam_pdf,
        "--out", args.exam_out,
    ])

    # 3) Match topics to questions
    cmd = [
        sys.executable, "tools/match_topics.py",
        "--slides", args.slides_out,
        "--exam", args.exam_out,
        "--out", args.out,
        "--min-score", str(args.min_score),
        "--max-matches", str(args.max_matches),
    ]
    if args.aliases:
        cmd.extend(["--aliases", args.aliases])
    subprocess.check_call(cmd)

    print("\nDone. Open:", args.out)


if __name__ == "__main__":
    main()

