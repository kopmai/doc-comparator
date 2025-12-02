import streamlit as st
# เรียกใช้จากโฟลเดอร์ services (Clean Code!)
from modules.services.ai_service import get_best_model, generate_content
from modules.services.file_service import extract_text_from_pdf, extract_text_from_docx, create_word_file

def render_summarize_mode():
    
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
            best_model = None
            if api_key:
                best_model = get_best_model(api_key)
                if best_model:
                    st.info(f"🤖 Auto-Selected: `{best_model}`")
                else:
                    st.error("❌ ไม่พบโมเดล")

    # --- 2. Upload ---
    uploaded_file = st.file_uploader("วางเอกสารที่ต้องการสรุป (PDF/Word)", type=["pdf", "docx"])

    if uploaded_file and api_key and best_model:
        
        if st.button("✨ เริ่มสรุปเนื้อหา (Summarize)", type="primary", use_container_width=True):
            
            # Step A: อ่านไฟล์ (ใช้ Service)
            with st.spinner("📖 กำลังอ่านเอกสาร..."):
                file_ext = uploaded_file.name.split('.')[-1].lower()
                raw_text = ""
                
                if file_ext == "pdf":
                    raw_text = extract_text_from_pdf(uploaded_file.read())
                elif file_ext == "docx":
                    raw_text = extract_text_from_docx(uploaded_file)
            
            if len(raw_text) < 50:
                st.warning("⚠️ ไม่พบข้อความในไฟล์ (อาจเป็นไฟล์สแกนรูปภาพ) กรุณาใช้เมนู OCR แทน")
            else:
                # Step B: ส่ง AI สรุป (ใช้ Service)
                st.info(f"⚡ พบเนื้อหา {len(raw_text)} ตัวอักษร.. กำลังวิเคราะห์")
                
                # Prompt สูตรเด็ด
                prompt = f"""
                You are an expert executive assistant. Summarize the following document in Thai.
                
                Structure:
                1. **หัวข้อเรื่อง (Topic):** (What is this about?)
                2. **ใจความสำคัญ (Executive Summary):** (3-5 sentences)
                3. **ประเด็นหลัก (Key Points):** (Bullet points)
                4. **สิ่งที่ต้องดำเนินการ (Action Items):** (If any)
                
                Document Content:
                {raw_text[:30000]} 
                """
                
                # Streaming Output
                st.markdown("### 📝 บทสรุป (Summary)")
                stream_box = st.empty()
                full_summary = ""
                
                stream_res = generate_content(api_key, best_model, prompt, stream=True)
                
                # Handle Generator (อาจเป็น Error string หรือ Object)
                if isinstance(stream_res, str) and stream_res.startswith("API_ERROR"):
                    st.error(stream_res)
                else:
                    for chunk in stream_res:
                        if chunk.text:
                            full_summary += chunk.text
                            stream_box.markdown(full_summary)
                    
                    # Save Result
                    st.session_state['summary_text'] = full_summary
                    st.success("✅ สรุปเสร็จเรียบร้อย")

    # --- 3. Download ---
    if 'summary_text' in st.session_state:
        st.markdown("---")
        docx = create_word_file(st.session_state['summary_text'])
        st.download_button(
            "💾 ดาวน์โหลดบทสรุป (.docx)",
            docx,
            "summary.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
