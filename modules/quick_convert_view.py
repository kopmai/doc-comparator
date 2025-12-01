import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io
from docx import Document
import re

def clean_ocr_text(text):
    """ล้างเส้นตารางออก เพื่อให้ได้ Word ที่สะอาด"""
    if not text: return ""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if re.match(r'^[\s\|\-\_\=\:\+]{3,}$', line.strip()):
            continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

def process_page_to_text(api_key, image, model_name):
    """ส่งรูปให้ AI แกะข้อความ (เน้นความเร็ว)"""
    try:
        genai.configure(api_key=api_key)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        model = genai.GenerativeModel(model_name, safety_settings=safety_settings)
        
        # Prompt สั่งให้เมิน Text Layer เดิม แล้วอ่านจากภาพเท่านั้น
        prompt = """
        You are a high-speed OCR engine. 
        Convert this document image into plain text.
        - IGNORE any underlying text layer (it might be corrupted). READ VISUALLY.
        - Preserve the original layout (paragraphs/lists).
        - If there are tables, keep the data structure clean.
        - Thai Language accuracy is top priority.
        """
        
        response = model.generate_content([prompt, image])
        return clean_ocr_text(response.text)
    except Exception as e:
        return f"[Error Page: {str(e)}]"

def create_doc_from_results(results):
    doc = Document()
    for text in results:
        doc.add_paragraph(text)
        doc.add_page_break()
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def render_quick_convert_mode():
    st.markdown("## ⚡ แก้ PDF เพี้ยนเป็น Word (Quick Fix)")
    st.caption("เหมาะสำหรับไฟล์ PDF ที่ก๊อปวางแล้วเป็นภาษาต่างดาว ระบบจะใช้ AI อ่านจากภาพโดยตรงแล้วแปลงเป็น Word ให้ทันที")

    # --- 1. Compact Settings (รวมไว้บรรทัดเดียว) ---
    with st.container():
        col_key, col_model = st.columns([1, 1])
        with col_key:
            api_key = None
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
                st.success("✅ API Key Connected")
            else:
                api_key = st.text_input("🔑 Gemini API Key", type="password")
        
        with col_model:
            # เลือกโมเดลแบบ Hardcode ตัวเร็วๆ ไปเลย เพื่อลดขั้นตอน User
            # แต่ยังเปิดให้เลือกได้เผื่ออยากเปลี่ยน
            model_options = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro']
            selected_model = st.selectbox("🤖 AI Model (แนะนำ Flash เพื่อความไว)", model_options, index=0)

    st.markdown("---")

    # --- 2. Upload Zone (ใหญ่ๆ) ---
    uploaded_file = st.file_uploader("วางไฟล์ PDF ที่มีปัญหาตรงนี้ (Drag & Drop)", type=["pdf"])

    if uploaded_file and api_key:
        
        # ปุ่ม Action ใหญ่ๆ
        if st.button("🚀 แปลงเป็น Word เดี๋ยวนี้ (Convert Now)", type="primary", use_container_width=True):
            
            progress_bar = st.progress(0, text="กำลังเตรียมไฟล์...")
            status_area = st.empty()
            
            try:
                # 1. แปลง PDF เป็นรูปภาพ
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                total_pages = len(doc)
                extracted_texts = []

                # 2. วนลูปทำทีละหน้า
                for i in range(total_pages):
                    # Update Status
                    progress_bar.progress((i / total_pages), text=f"⏳ กำลังแปลงหน้า {i+1} จาก {total_pages}...")
                    
                    # Render Image
                    page = doc.load_page(i)
                    pix = page.get_pixmap(dpi=150) # DPI 150 ก็ชัดพอสำหรับ AI (เร็วกว่า 300)
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    
                    # Call AI
                    text_result = process_page_to_text(api_key, img, selected_model)
                    extracted_texts.append(text_result)

                # 3. รวมร่างเป็น Word
                progress_bar.progress(0.9, text="💾 กำลังสร้างไฟล์ Word...")
                docx_file = create_doc_from_results(extracted_texts)
                
                # 4. เสร็จสิ้น -> โชว์ปุ่มโหลด
                progress_bar.progress(1.0, text="✅ เสร็จเรียบร้อย!")
                st.balloons()
                
                st.success(f"แปลงไฟล์ {uploaded_file.name} สำเร็จ! ({total_pages} หน้า)")
                
                # ปุ่มดาวน์โหลดใหญ่ๆ
                st.download_button(
                    label="📥 คลิกเพื่อดาวน์โหลดไฟล์ Word (.docx)",
                    data=docx_file,
                    file_name=f"fixed_{uploaded_file.name}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary", # สีเขียว/ฟ้า เด่นๆ
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
