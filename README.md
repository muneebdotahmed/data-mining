# Data Mining Course Materials

This repository contains comprehensive exam preparation materials and data mining resources for Knowledge Discovery and Data Mining (KDDM) courses.

## Contents

### Core Materials
- `Exam_Questions_Summary.pdf` - Summary of exam questions and key topics
- `slides/` - Individual chapter slides organized by topic:
  - Chapter 2: Data
  - Chapter 3: Classification  
  - Chapter 4: Clustering, Frequent Patterns, Outlier Detection, Rare Patterns
  - Chapter 5: Process Mining

### Extracted Data
- `data/exam_questions.txt` - All exam questions extracted from PDF
- `data/slides_topics.txt` - Slide topics by chapter
- `data/aliases.json` - Topic synonyms for improved matching

### Analysis Results
- `results/mapped_topics_all.csv` - Complete topic-to-question mapping
- `results/mapped_topics_*.csv` - Various threshold analyses
- Chapter-specific mappings for focused study

## Setup Instructions

### Prerequisites
- Git installed on your system
- PDF reader (Adobe Acrobat, Preview, or similar)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/muneebdotahmed/data-mining.git
   cd data-mining
   ```

2. **Open the materials**
   - Use any PDF reader to view the documents
   - Recommended: Adobe Acrobat Reader for best compatibility

## Automated Tools

### Extraction Pipeline
The repository includes Python tools for automated analysis:
- `tools/extract_exam_questions.py` - Extract questions from exam PDF
- `tools/extract_slide_titles.py` - Extract slide titles from chapter PDFs  
- `tools/run_pipeline.py` - Complete analysis pipeline
- `tools/match_topics.py` - Topic matching and scoring

## Usage

These materials are designed for exam preparation. Review both documents thoroughly.

### Automated Extraction & Matching (preserves LaTeX/math)

Generate a CSV mapping of slide topics to exam questions locally:

1) Install dependencies (one-time):
   - Python 3.8+ and `pip`
   - `pdfminer.six` for math-aware text extraction
   ```bash
   python3 -m pip install pdfminer.six
   ```

2) Run the full pipeline:
   ```bash
   python3 tools/run_pipeline.py \
     --slides-pdf "slides/Chapter 2 - Data.pdf" \
     --exam-pdf "Exam_Questions_Summary.pdf" \
     --out results/mapped_topics.csv
   ```

   Or analyze all chapters at once:
   ```bash
   python3 tools/run_pipeline.py \
     --slides-pdf "slides/" \
     --exam-pdf "Exam_Questions_Summary.pdf" \
     --out results/mapped_topics_all.csv
   ```

Outputs:
- `data/slides_topics.txt` – one line per page: `page|title`
- `data/exam_questions.txt` – one question/topic per line
- `results/mapped_topics.csv` – slide topic ↔ exam question mapping with scores

### Pre-Generated Results

The repository includes ready-to-use analysis results:
- `results/mapped_topics_all.csv` - Complete mapping across all chapters
- `results/mapped_topics_[0.60-0.72].csv` - Different similarity thresholds
- `results/mapped_topics__chapter_*.csv` - Individual chapter analyses

### Advanced Usage

Customize topic matching with synonyms:
```json
{
  "decision tree": ["id3", "c4.5", "cart"],
  "naive bayes": ["nb"],
  "k-means": ["kmeans", "k means"]
}
```
Then run: `python3 tools/run_pipeline.py --aliases data/aliases.json`

## Contributing

If you have additional materials or corrections:
1. Fork the repository
2. Create a feature branch
3. Add your materials or corrections
4. Submit a pull request

## Notes

- Ensure you have proper permissions to access and use these materials
- Keep materials updated with latest versions
- Share responsibly within academic guidelines

---

*Last updated: September 2025*
