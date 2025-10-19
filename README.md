# 🧩 UIT Regulation Normalizer

### A preprocessing and normalization pipeline for UIT regulation documents  
> **Chuẩn hóa và cấu trúc dữ liệu quy định UIT phục vụ ontology & RAG chatbot**

---

## 📘 Overview

This repository is part of the **UIT AI Agent** ecosystem.  
It focuses on the **Normalization / Standardization** stage of the data pipeline —  
where all regulation documents (PDF, DOCX, web text) are converted into **structured JSONL** data following the legal hierarchy:

> **Chương → Điều → Khoản → Điểm**

Each smallest unit (“Điểm”) becomes a clean, machine-readable data node for later indexing, ontology mapping, and retrieval in the chatbot.

---

## 🧱 Project Structure

uit-regulation-normalizer/
│
├── src/
│ ├── loaders/ # Read PDF, DOCX, or HTML input
│ ├── parsers/ # Detect and extract Chapter / Article / Clause / Point
│ ├── normalizers/ # Clean text, fix OCR errors, unify encoding
│ ├── exporters/ # Export structured JSONL dataset
│ └── main.py # Pipeline entrypoint
│
├── data/
│ ├── raw/ # Original regulation files
│ ├── processed/ # Intermediate cleaned text
│ └── normalized/ # Final JSONL outputs
│
├── pyproject.toml
├── uv.lock
└── README.md

---

## ⚙️ Pipeline Workflow

1. **Ingest**
   - Load regulation documents from `/data/raw`
   - Supported formats: `.pdf`, `.docx`, `.txt`, `.html`

2. **Parse**
   - Detect the structure:
     ```
     Chương I → Điều 5 → Khoản 2 → Điểm b
     ```
   - Split into hierarchical elements.

3. **Normalize**
   - Clean text (OCR, whitespace, Unicode normalization)
   - Fix numbering and formatting errors.

4. **Export**
   - Save standardized dataset to `/data/normalized/uit_regulations.jsonl`

---

## 📄 Output Schema Example

Each record represents a **single "Điểm"** (smallest legal unit):

```json
{
  "doc_name": "Quy chế đào tạo đại học UIT 2024",
  "chapter": "I",
  "article": 5,
  "clause": 2,
  "point": "b",
  "text": "Sinh viên phải giữ gìn vệ sinh, trật tự trong lớp học.",
  "source_file": "uit_regulation_2024.pdf",
  "page_range": [10, 11],
  "version_date": "2024-09-01"
}

🚀 Quick Start

# Clone repo
git clone https://github.com/korobe0906/uit-regulation-normalizer.git
cd uit-regulation-normalizer

# Install dependencies using uv
uv sync

# Run the normalization pipeline
uv run python src/main.py --input data/raw --output data/normalized