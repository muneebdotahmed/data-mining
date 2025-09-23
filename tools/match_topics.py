#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple


def load_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.rstrip("\n") for line in f]


def load_aliases(path: Optional[str]) -> Dict[str, List[str]]:
    default_aliases = {
        # General ML/DM topic aliases (extend as needed)
        "naive bayes": ["nb", "naïve bayes"],
        "k-means": ["kmeans", "k means", "k-means clustering"],
        "k-medoids": ["kmedoids", "k medoids"],
        "hierarchical clustering": ["agglomerative clustering", "divisive clustering"],
        "principal component analysis": ["pca"],
        "support vector machine": ["svm", "support vector machines", "support vector classifier"],
        "decision tree": ["dt", "id3", "c4.5", "cart"],
        "association rules": ["apriori", "fp growth", "frequent pattern", "market basket"],
        "outlier detection": ["anomaly detection"],
        "feature selection": ["attribute selection"],
        "data preprocessing": ["data preparation", "data cleaning", "data cleansing"],
        "distance measures": ["similarity measures", "dissimilarity", "proximity"],
        "logistic regression": ["logit"],
        "linear regression": ["ols"],
        "neural networks": ["ann", "mlp"],
        "k-nearest neighbors": ["knn", "k nn", "k-nn"],
        "dimensionality reduction": ["feature extraction"],
        "cross validation": ["k-fold", "k fold"],
    }
    if not path:
        return default_aliases
    try:
        with open(path, "r", encoding="utf-8") as f:
            user_aliases = json.load(f)
        # merge user_aliases over defaults
        for k, v in user_aliases.items():
            default_aliases[k.lower()] = [s.lower() for s in v]
        return default_aliases
    except Exception:
        return default_aliases


_punct_re = re.compile(r"[^a-z0-9\s]")
_ws_re = re.compile(r"\s+")
STOPWORDS = set(
    "the a an of and or to for from in on with without by as at into over under between among against".split()
)


def normalize(text: str, aliases: Dict[str, List[str]]) -> str:
    t = text.lower().strip()
    # apply aliases (replace synonyms with canonical form)
    # longer keys first to avoid partial overwrites
    for canon in sorted(aliases.keys(), key=len, reverse=True):
        for syn in aliases[canon]:
            t = re.sub(rf"\b{re.escape(syn)}\b", canon, t)
    # remove punctuation
    t = _punct_re.sub(" ", t)
    # collapse whitespace
    t = _ws_re.sub(" ", t).strip()
    # remove trivial stopwords at ends
    tokens = [w for w in t.split() if w not in STOPWORDS]
    return " ".join(tokens)


def tokens(text: str) -> List[str]:
    return [w for w in text.split() if w]


def jaccard(a_tokens: List[str], b_tokens: List[str]) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    a, b = set(a_tokens), set(b_tokens)
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def token_overlap(a_tokens: List[str], b_tokens: List[str]) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    a, b = set(a_tokens), set(b_tokens)
    inter = len(a & b)
    denom = min(len(a), len(b))
    return inter / denom if denom else 0.0


def char_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def combined_score(a: str, b: str) -> float:
    a_toks, b_toks = tokens(a), tokens(b)
    j = jaccard(a_toks, b_toks)
    o = token_overlap(a_toks, b_toks)
    c = char_similarity(a, b)
    # Weighted combination tuned for topic-question matching
    return 0.40 * c + 0.30 * j + 0.30 * o


def confidence(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.70:
        return "medium"
    return "low"


def parse_slides(lines: List[str]) -> List[Tuple[Optional[int], str]]:
    """Accepts either:
    - plain list of topics (one per line)
    - or lines like `page|topic` where page is an integer
    Returns list of (page, topic) preserving order.
    """
    out: List[Tuple[Optional[int], str]] = []
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        if "|" in s:
            left, right = s.split("|", 1)
            try:
                page = int(left.strip())
            except ValueError:
                page = None
                right = s  # fall back to whole line as topic
            topic = right.strip()
            if topic:
                out.append((page, topic))
        else:
            out.append((None, s))
    return out


def parse_exam(lines: List[str]) -> List[str]:
    out: List[str] = []
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        # Skip very short fragments that are likely headers
        if len(s) < 4:
            continue
        out.append(s)
    return out


def match_topics(
    slides: List[Tuple[Optional[int], str]],
    exam: List[str],
    aliases: Dict[str, List[str]],
    min_score: float,
    max_matches: int,
) -> Tuple[List[Dict], List[Tuple[Optional[int], str]], List[str]]:
    results: List[Dict] = []
    unmatched_slides: List[Tuple[Optional[int], str]] = []
    unmatched_exam: List[str] = exam.copy()

    # Pre-normalize exam questions
    norm_exam = [(q, normalize(q, aliases)) for q in exam]

    for page, topic in slides:
        norm_topic = normalize(topic, aliases)
        scored: List[Tuple[float, str]] = []
        for orig_q, norm_q in norm_exam:
            s = combined_score(norm_topic, norm_q)
            if s >= min_score:
                scored.append((s, orig_q))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:max_matches]
        if not top:
            unmatched_slides.append((page, topic))
            continue
        for s, q in top:
            if q in unmatched_exam:
                unmatched_exam.remove(q)
            results.append(
                {
                    "page": page,
                    "slide_topic": topic,
                    "exam_question": q,
                    "score": round(s, 3),
                    "confidence": confidence(s),
                }
            )

    return results, unmatched_slides, unmatched_exam


def write_csv(rows: List[Dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = ["page", "slide_topic", "exam_question", "score", "confidence"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main():
    ap = argparse.ArgumentParser(description="Match slide topics to exam questions (fuzzy)")
    ap.add_argument("--slides", required=True, help="Path to slides topics .txt (one per line or 'page|topic')")
    ap.add_argument("--exam", required=True, help="Path to exam questions .txt (one question per line)")
    ap.add_argument("--aliases", help="Optional JSON mapping canonical->list of synonyms")
    ap.add_argument("--out", default="results/mapped_topics.csv", help="Output CSV path")
    ap.add_argument("--min-score", type=float, default=0.72, help="Min combined score to consider a match (0-1)")
    ap.add_argument("--max-matches", type=int, default=2, help="Max exam questions per slide topic")
    args = ap.parse_args()

    aliases = load_aliases(args.aliases)
    slide_lines = load_lines(args.slides)
    exam_lines = load_lines(args.exam)

    slides = parse_slides(slide_lines)
    exam = parse_exam(exam_lines)

    results, unmatched_slides, unmatched_exam = match_topics(
        slides, exam, aliases, min_score=args.min_score, max_matches=args.max_matches
    )

    write_csv(results, args.out)

    # Also print a brief summary to stdout
    print(f"Matches written to: {args.out}")
    print(f"Matched pairs: {len(results)} (topics x questions)")
    if unmatched_slides:
        print(f"Unmatched slide topics: {len(unmatched_slides)}")
    if unmatched_exam:
        print(f"Unmatched exam questions: {len(unmatched_exam)}")

    # Offer quick review of low-confidence items
    lows = [r for r in results if r["confidence"] == "low"]
    if lows:
        print("\nLow-confidence matches (review suggested):")
        for r in lows[:10]:
            p = r["page"] if r["page"] is not None else "-"
            print(f"[score={r['score']}] page {p} | {r['slide_topic']}  <->  {r['exam_question']}")


if __name__ == "__main__":
    main()

