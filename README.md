# 🧩 UIT Regulation Normalizer

### A preprocessing and normalization pipeline for UIT regulation documents  
> **Chuẩn hóa và cấu trúc dữ liệu quy định UIT phục vụ ontology & RAG chatbot**

---

## 📘 Overview

This repository is part of the **UIT AI Agent** ecosystem.  
It handles the **Normalization / Standardization** stage of the data pipeline —  
transforming raw regulation documents (PDF, DOCX, scanned images, HTML)  
into **clean, structured, machine-readable JSONL units** based on Vietnam’s legal hierarchy:

> **Chương → Điều → Khoản → Điểm**

Each “Điểm” (point) becomes a minimal knowledge unit ready for indexing, ontology mapping, and retrieval in the UIT regulation chatbot.

---

## 🧠 Objectives

| Stage | Description |
|--------|--------------|
| 🩵 **OCR Ingestion** | Extract text from scanned PDF/DOCX using PaddleOCR or Tesseract |
| 💙 **Structure Parsing** | Detect and split legal hierarchy: Chapter / Article / Clause / Point |
| 💜 **Text Normalization** | Fix OCR typos, unify Unicode, clean spacing and punctuation |
| 💛 **Metadata Extraction** | Retrieve document number, issue date, version, category |
| 🧾 **Export & QC** | Output structured JSONL, log OCR confidence, and report anomalies |

---

## 🚀 Quick Start
1️⃣ Installation

# Clone repository
- git clone : https://github.com/korobe0906/uit-regulation-normalizer.git
- cd uit-regulation-normalizer

# Install dependencies using uv

2️⃣ Run the pipeline

# Run full end-to-end pipeline
- uv run python src/main.py

- or (explicit orchestrator version):
uv run python src/pipeline.py --input data/raw --output data/normalized

### 📄 Sample Output
```json
{
  "doc_name": "Quyết định số 1393 - Bổ sung Quy chế đào tạo theo tín chỉ",
  "doc_number": "1393",
  "date": "2024-06-05",
  "category": "Đào tạo",
  "chapter": "II",
  "article": 4,
  "clause": 3,
  "point": null,
  "text": "Sinh viên được phép đăng ký học lại tối đa 3 học phần trong một học kỳ.",
  "source_file": "Quyet_dinh_1393.pdf",
  "page_range": [2,3],
  "ocr_confidence": 0.93
}
```
---

## 🧩 Integration in UIT AI Agent Ecosystem
```
Stage	Repository	Description
(1) Ingestion	uit-data-ingestion	Crawl official documents (web, announcements)
(2) Normalization	uit-regulation-normalizer	OCR + parse + clean + export structured data
(3) Ontology Builder	uit-ontology-builder	Map relations for knowledge graph
(4) RAG Backend	uit-rag-agent	Retrieve relevant regulations for chatbot
(5) Chat UI	uit-chat-ui	Student-facing chatbot interface
```
---

## 🧮 Logging & Reports
```
OCR confidence per page

Number of chapters, articles, clauses, and points detected

Documents with low quality (<0.85 confidence) flagged for review

JSONL record count summary

Exported logs in /data/normalized/reports/
```

