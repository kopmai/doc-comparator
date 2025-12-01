import streamlit as st
import google.generativeai as genai
from modules.comparator import TextComparator

# --- CONFIG: ตั้งค่ารุ่นโมเดลตรงนี้ง่ายๆ ---
# ถ้ามีรุ่นใหม่กว่านี้ (เช่น 3.0) ก็มาแก้ตรงนี้ได้เลยครับ
MODEL_VERSION = 'gemini-2.5-flash' 
# ----------------------------------------

def get_ai_correction(api_key, text):
    try:
        genai.configure(api_key=api_key)
        
        # เรียกใช้โมเดลตามตัวแปรที่ตั้งไว้ด้านบน
        model = genai.GenerativeModel(MODEL_VERSION)
        
        prompt = f"""
        Act as a professional proofreader. 
        Please correct the spelling, grammar, and punctuation errors in the following text (Thai and English).
        Maintain the original tone and style. 
        RETURN ONLY THE CORRECTED TEXT without any explanation or markdown formatting.
        
        Text to correct:
        {text}
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def render_spell_check_mode():
    col_setup, col_result = st.columns([1, 1])
    
    with col_setup:
        st.markdown("### 1. ใส่เนื้อหา (Input)")
        # โชว์ให้เห็นเลยว่ากำลังใช้โมเดลรุ่นไหน
        st.caption(f"🚀 AI Engine: {MODEL_VERSION}")

        api_key = None
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ เชื่อมต่อกับ API Key อัตโนมัติแล้ว")
        else:
            api_key = st.text_input("🔑 Gemini API Key", type="password", help="รับ Key ฟรีได้ที่ aistudio.google.com")
        
        st.markdown("---")
        text_input = st.text_area("✍️ ต้นฉบับ (Original Text)", height=400, placeholder="วางข้อความที่ต้องการตรวจทานที่นี่...")
        
        # ปุ่มกด
        btn_check = st.button(f"✨ ตรวจทานด้วย {MODEL_VERSION}", type="primary", use_container_width=True, disabled=(not api_key or not text_input))

    with col_result:
        st.markdown("### 2. ผลการตรวจทาน (AI Suggestion)")
        
        if btn_check and api_key and text_input:
            with st.spinner(f"🤖 {MODEL_VERSION} กำลังทำงาน..."):
                corrected_text = get_ai_correction(api_key, text_input)
                
                if "Error:" in corrected_text:
                    st.error(corrected_text)
                    st.warning(f"ถ้า Error 404 แสดงว่า Key ของคุณยังเข้าถึงรุ่น {MODEL_VERSION} ไม่ได้ (อาจต้องรอ Google ปล่อยให้ใช้ทั่วไป) ลองถอยไปใช้ 'gemini-1.5-flash' แก้ขัดก่อนได้ครับ")
                else:
                    original_lines = text_input.splitlines()
                    corrected_lines = corrected_text.splitlines()
                    
                    comparator = TextComparator()
                    raw_html = comparator.generate_diff_html(original_lines, corrected_lines, mode="all")
                    final_html = comparator.get_final_display_html(raw_html)
                    
                    st.success("✅ ตรวจเสร็จเรียบร้อย!")
                    st.markdown('<div class="css-card">', unsafe_allow_html=True)
                    import streamlit.components.v1 as components
                    components.html(final_html, height=600, scrolling=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    with st.expander("📄 ดูข้อความที่แก้แล้ว (Plain Text)"):
                        st.code(corrected_text, language=None)
        
        elif not btn_check:
            st.info("👈 กดปุ่มเพื่อเริ่มตรวจ")
