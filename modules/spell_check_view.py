import streamlit as st
import google.generativeai as genai
from modules.comparator import TextComparator

def get_available_models(api_key):
    """ดึงรายชื่อโมเดลทั้งหมดที่ Key นี้ใช้ได้จริง"""
    try:
        genai.configure(api_key=api_key)
        all_models = []
        for m in genai.list_models():
            # กรองเอาเฉพาะตัวที่เจนข้อความได้
            if 'generateContent' in m.supported_generation_methods:
                all_models.append(m.name)
        return all_models
    except:
        return []

def get_ai_correction(api_key, text, model_name):
    try:
        genai.configure(api_key=api_key)
        
        # ปิด Safety Filter (กัน Error หยุมหยิม)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        # ใช้โมเดลตามที่ User เลือกจาก Dropdown
        model = genai.GenerativeModel(model_name, safety_settings=safety_settings)
        
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
        if "429" in str(e):
            return "Error 429: โควต้าเต็ม (Quota Exceeded) สำหรับโมเดลนี้ กรุณาเปลี่ยนโมเดลอื่น"
        return f"Error: {str(e)}"

def render_spell_check_mode():
    col_setup, col_result = st.columns([1, 1])
    
    with col_setup:
        st.markdown("### 1. ตั้งค่า (Settings)")
        
        # 1. รับ Key
        api_key = None
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ เชื่อมต่อกับ API Key อัตโนมัติแล้ว")
        else:
            api_key = st.text_input("🔑 Gemini API Key", type="password")

        # 2. เลือกโมเดล (หัวใจสำคัญของรอบนี้)
        selected_model = None
        if api_key:
            # ดึงรายชื่อโมเดลสดๆ จาก Google
            model_options = get_available_models(api_key)
            
            if model_options:
                # พยายามหาตัวที่เป็น stable (gemini-pro) เป็นค่าเริ่มต้น
                default_idx = 0
                for i, name in enumerate(model_options):
                    if "gemini-pro" in name and "exp" not in name and "vision" not in name:
                        default_idx = i
                        break
                
                selected_model = st.selectbox(
                    "🤖 เลือก AI Model (เลือกตัวที่ไม่ใช่ exp จะดีสุด)", 
                    model_options, 
                    index=default_idx
                )
            else:
                st.error("❌ Key นี้เชื่อมต่อได้ แต่ไม่พบโมเดลที่ใช้งานได้เลย")
        else:
            st.info("กรุณาใส่ Key เพื่อโหลดรายชื่อโมเดล")

        st.markdown("---")
        text_input = st.text_area("✍️ ต้นฉบับ (Original Text)", height=400, placeholder="วางข้อความที่ต้องการตรวจทานที่นี่...")
        
        # ปุ่มกด
        btn_check = st.button("✨ เริ่มตรวจทาน (Start)", type="primary", use_container_width=True, disabled=(not api_key or not text_input or not selected_model))

    with col_result:
        st.markdown("### 2. ผลการตรวจทาน (AI Suggestion)")

        if btn_check and api_key and text_input and selected_model:
            with st.spinner(f"กำลังให้ {selected_model} ตรวจทาน..."):
                
                corrected_text = get_ai_correction(api_key, text_input, selected_model)

                if "Error" in corrected_text:
                    st.error("เกิดข้อผิดพลาด:")
                    st.error(corrected_text)
                    st.warning("คำแนะนำ: ลองเปลี่ยนโมเดลในช่องเลือกด้านซ้าย เป็นตัวอื่น (เช่น gemini-pro)")
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
