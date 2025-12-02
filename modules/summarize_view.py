import streamlit as st
# เรียกใช้บริการจากไฟล์กลาง (โค้ดสะอาดขึ้นเยอะ!)
from modules.ai_service import get_best_model, generate_content
from modules.file_service import extract_text_from_pdf, create_word_file
from modules.loader import DocumentLoader # ใช้ตัวเดิมช่วยอ่าน docx ได้

def render_summarize_mode():
    st.markdown("## 📝 สรุปย่อเอกสาร (AI Summarizer)")
    st.caption("ช่วยอ่านเอกสารยาวๆ แล้วสรุปใจความสำคัญให้ภายในพริบตา")

    # --- 1. Settings (Expander) ---
    with st.expander("⚙️ ตั้งค่า (Settings)", expanded=True):
        col_key, col_model = st.columns([1, 1])
        with col_key:
            api_key = None
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
                st.success("✅ API Key Connected")
            else:
                api_key = st.text_input("🔑 Gemini API Key", type="password")
        
        with col_model:
            # ใช้ฟังก์ชันกลางหาโมเดลให้อัตโนมัติ ไม่ต้องเขียนยาวๆ แล้ว
            best_model = None
            if api_key:
                best_model = get_best_model(api_key)
                st.info(f"🤖 Auto-Selected Model: `{best_model}`")

    # --- 2. Upload ---
    uploaded_file = st.file_uploader("อัปโหลดไฟล์ (PDF หรือ Word)", type=["pdf", "docx"])

    if uploaded_file and api_key and best_model:
        if st.button("✨ เริ่มสรุปเนื้อหา (Summarize)", type="primary"):
            
            with st.spinner("📖 กำลังอ่านเอกสาร..."):
                # 1. แกะข้อความตามประเภทไฟล์
                file_ext = uploaded_file.name.split('.')[-1].lower()
                raw_text = ""
                
                try:
                    if file_ext == "pdf":
                        raw_text = extract_text_from_pdf(uploaded_file.read())
                    elif file_ext == "docx":
                        # ใช้ Loader เดิมที่มีอยู่แล้วก็ได้ หรือจะย้ายไป file_service ก็ได้
                        # ในที่นี้ขอใช้ Loader เดิมเพื่อความรวดเร็ว
                        lines = DocumentLoader.extract_text(uploaded_file, "docx")
                        raw_text = "\n".join(lines)
                except Exception as e:
                    st.error(f"อ่านไฟล์ไม่ได้: {e}")
                    st.stop()

            if len(raw_text) < 50:
                st.warning("⚠️ ไฟล์ดูเหมือนจะไม่มีข้อความ (อาจเป็นไฟล์สแกนรูปภาพ) กรุณาใช้เมนู OCR แทน")
            else:
                # 2. ส่ง AI สรุป
                st.info(f"📄 พบเนื้อหาประมาณ {len(raw_text)} ตัวอักษร.. กำลังส่งให้ AI วิเคราะห์")
                
                # Prompt สูตรเด็ดสำหรับสรุปงาน
                prompt = f"""
                You are an expert executive assistant. Summarize the following document in Thai.
                
                Please structure the summary as follows:
                1. **หัวข้อเรื่อง (Topic):** What is this document about?
                2. **ใจความสำคัญ (Executive Summary):** 3-5 sentences summary.
                3. **ประเด็นหลัก (Key Points):** Bullet points of important details.
                4. **สิ่งที่ต้องดำเนินการ (Action Items):** (If any)
                
                Original Text:
                {raw_text[:20000]}  # ตัด Text บางส่วนถ้าเยอะเกิน token limit (Flash รับได้เยอะอยู่)
                """
                
                # ใช้ Stream เพื่อให้เห็นตัวหนังสือวิ่ง
                stream_box = st.empty()
                full_summary = ""
                
                # เรียกใช้ AI Service แบบ Stream
                stream_res = generate_content(api_key, best_model, prompt, stream=True)
                
                for chunk in stream_res:
                    if chunk.text:
                        full_summary += chunk.text
                        stream_box.markdown(full_summary)
                
                # 3. จบงาน & ปุ่มโหลด
                st.success("✅ สรุปเสร็จเรียบร้อย")
                
                # เก็บลง Session (เผื่อ user กดเล่น)
                st.session_state['summary_result'] = full_summary
                
    # Show Download if result exists
    if 'summary_result' in st.session_state:
        docx = create_word_file(st.session_state['summary_result'])
        st.download_button(
            "💾 ดาวน์โหลดบทสรุป (.docx)",
            docx,
            "summary.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="secondary"
        )
