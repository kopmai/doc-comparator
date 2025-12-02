import fitz  # PyMuPDF
from PIL import Image
import io
from docx import Document
import pandas as pd

def pdf_to_images(file_bytes, dpi=150):
    """แปลง PDF เป็น List ของรูปภาพ"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images = []
    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes()))
        images.append(img)
    return images

def extract_text_from_pdf(file_bytes):
    """อ่านข้อความจาก PDF (แบบดั้งเดิม)"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    return text

def create_word_file(text_content):
    """สร้างไฟล์ Word จากข้อความ"""
    doc = Document()
    # ถ้าเป็น list ให้วนลูป
    if isinstance(text_content, list):
        for t in text_content:
            doc.add_paragraph(str(t))
            doc.add_page_break()
    else:
        # ถ้าเป็น str ก้อนเดียว
        doc.add_paragraph(str(text_content))
        
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
