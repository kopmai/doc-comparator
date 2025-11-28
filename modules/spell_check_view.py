import streamlit as st
import re
from pythainlp import word_tokenize
from pythainlp.spell import correct as thai_correct
from spellchecker import SpellChecker

eng_spell = SpellChecker()

def is_thai(word):
    return re.search(r'[\u0E00-\u0E7F]', word)

# เพิ่ม Parameter รับ progress_bar และ status_text
def highlight_errors(text, progress_bar=None, status_text=None):
    if not text.strip():
        return "", []

    # 1. แจ้งสถานะก่อนตัดคำ (ขั้นตอนนี้อาจจะนานถ้า text ใหญ่มาก)
    if status_text:
        status_text.text("⏳ กำลังแยกคำ (Tokenizing)... โปรดรอสักครู่")

    # ตัดคำ
    words = word_tokenize(text, engine="newmm")
    total_words = len(words)
    
    processed_html = ""
    error_list = []
    
    # 2. วนลูปตรวจทีละคำ
    for i, word in enumerate(words):
        
        # --- UPDATE PROGRESS BAR ---
        # อัปเดตทุกๆ 5% หรือทุกๆ 20 คำ (เพื่อไม่ให้ UI กระตุกเกินไป)
        if progress_bar and (i % 20 == 0 or i == total_words - 1):
            progress = (i + 1) / total_words
            progress_bar.progress(progress)
            if status_text:
                status_text.text(f"🔍 กำลังตรวจสอบคำที่ {i+1} จาก {total_words} ({int(progress*100)}%)")
        # ---------------------------

        clean_word = word.strip()
        
        if not clean_word or clean_word.isnumeric() or len(clean_word) <= 1:
            processed_html += word
            continue

        is_error = False
        suggestion = ""

        if is_thai(clean_word):
            corrected = thai_correct(clean_word)
            if corrected != clean_word:
                is_error = True
                suggestion = corrected
        
        elif re.match(r'^[a-zA-Z]+$', clean_word):
            if clean_word.lower() not in eng_spell:
                is_error = True
                suggestion = eng_spell.correction(clean_word)

        if is_error:
            span = f'<span style="background-color: #ffcccc; border-bottom: 2px solid red; cursor: help;" title="แนะนำ: {suggestion}">{word}</span>'
            processed_html += span
            error_list.append({"wrong": word, "suggest": suggestion})
        else:
            processed_html += word

    final_html = f"""
    <div style="font-family: 'Kanit'; font-size: 16px; line-height: 1.8; color: #333; background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
        {processed_html}
    </div>
    """
    return final_html, error_list

def render_spell_check_mode():
    col_input, col_result = st.columns([1, 1])
    
    with col_input:
        st.markdown("### ✍️ ต้นฉบับ (Input Text)")
        text_input = st.text_area("วางข้อความที่นี่...", height=500, label_visibility="collapsed", placeholder="วางข้อความภาษาไทย หรือ ภาษาอังกฤษ ที่ต้องการตรวจทาน...")

    with col_result:
        st.markdown("### 🔍 ผลการตรวจสอบ (Result)")
        
        if text_input:
            # สร้างตัวแปรสำหรับ UI Progress
            status_text = st.empty() # ข้อความแจ้งสถานะ (ตัวเลขวิ่ง)
            my_bar = st.progress(0)  # แถบ Progress Bar เริ่มที่ 0
            
            # ส่ง UI เข้าไปในฟังก์ชัน เพื่อให้อัปเดตจากข้างในได้
            html_output, errors = highlight_errors(text_input, progress_bar=my_bar, status_text=status_text)
            
            # พอเสร็จแล้ว เคลียร์ Progress bar ทิ้ง เพื่อความสวยงาม
            my_bar.empty()
            status_text.empty()

            # แสดงผลลัพธ์
            if errors:
                st.error(f"พบคำที่น่าจะผิด {len(errors)} จุด")
            else:
                st.success("ไม่พบคำผิด (หรือระบบอาจจะไม่รู้จัก)")

            st.markdown(html_output, unsafe_allow_html=True)
            
            if errors:
                st.markdown("---")
                st.markdown("**💡 รายการคำแนะนำ**")
                for err in list(set([tuple(d.items()) for d in errors])):
                    err_dict = dict(err)
                    st.markdown(f"- ❌ **{err_dict['wrong']}** → ✅ `{err_dict['suggest']}`")
        else:
            st.info("รอรับข้อความ...")
