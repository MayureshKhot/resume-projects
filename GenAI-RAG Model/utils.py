import PyPDF2
import pytesseract
from PIL import Image
import os

def extract_text(file_path):
    """Extract text from PDF, TXT, or image files"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ' '.join([page.extract_text() for page in reader.pages])
        return text
    
    elif ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif ext in ['.png', '.jpg', '.jpeg']:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)
    
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    
    return chunks
