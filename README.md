# Exam Materials - KDDM

This repository contains exam preparation materials and data mining resources.

## Contents

- `Exam_Questions_Summary.pdf` - Summary of exam questions and key topics
- `KDDM - data - 2.pdf` - Data mining course materials and resources

## Setup Instructions

### Prerequisites
- Git installed on your system
- PDF reader (Adobe Acrobat, Preview, or similar)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd exam-maaz
   ```

2. **Open the materials**
   - Use any PDF reader to view the documents
   - Recommended: Adobe Acrobat Reader for best compatibility

## File Descriptions

### Exam_Questions_Summary.pdf
Contains comprehensive summary of exam questions and important topics for review.

### KDDM - data - 2.pdf
Knowledge Discovery and Data Mining course materials including:
- Key concepts and methodologies
- Data analysis techniques
- Reference materials for exam preparation

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
     --slides-pdf "KDDM - data - 2.pdf" \
     --exam-pdf "Exam_Questions_Summary.pdf" \
     --out results/mapped_topics.csv
   ```

Outputs:
- `data/slides_topics.txt` – one line per page: `page|title`
- `data/exam_questions.txt` – one question/topic per line
- `results/mapped_topics.csv` – slide topic ↔ exam question mapping with scores

Tuning:
- Add synonyms via JSON and re-run for better matches:
  ```json
  {
    "decision tree": ["id3", "c4.5", "cart"],
    "naive bayes": ["nb"],
    "k-means": ["kmeans", "k means"]
  }
  ```
  Then: `python3 tools/run_pipeline.py --aliases data/aliases.json`

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
