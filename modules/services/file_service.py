import fitz  # PyMuPDF
from docx import Document
import io

def extract_text_from_pdf(file_bytes):
    """อ่านข้อความจากไฟล์ PDF"""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_text_from_docx(file_obj):
    """อ่านข้อความจากไฟล์ Word"""
    try:
        doc = Document(file_obj)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        return f"Error reading Docx: {e}"

def create_word_file(content):
    """สร้างไฟล์ Word เพื่อดาวน์โหลด"""
    doc = Document()
    # ถ้า content เป็น string ยาวๆ ให้แตกบรรทัด
    if isinstance(content, str):
        for line in content.split('\n'):
            doc.add_paragraph(line)
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
