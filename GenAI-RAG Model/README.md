# 🚀 GenAI Document Assistant

A minimal RAG pipeline using BERT embeddings + FAISS + Groq LLM for fast document Q&A.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your Groq API key:
```
GROQ_API_KEY=your_key_here
```

3. (Optional) Install Tesseract for OCR support

## Usage

### Streamlit UI (Recommended)
```bash
streamlit run streamlit_app.py
```

### CLI
Add a document and ask a question:
```bash
python app.py --file "data/uploaded_pdfs/document.pdf" --query "Summarize this document"
```

Add document only:
```bash
python app.py --file "document.txt"
```

Query existing documents:
```bash
python app.py --query "What is the main topic?"
```

## Supported Files
- PDF (.pdf)
- Text (.txt)
- Images (.png, .jpg) - requires Tesseract

## Architecture
- **Embeddings**: Sentence-BERT (all-MiniLM-L6-v2)
- **Vector DB**: FAISS
- **LLM**: Groq (Mixtral-8x7B)
