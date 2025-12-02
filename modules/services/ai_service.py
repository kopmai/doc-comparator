import google.generativeai as genai
import streamlit as st

# ตั้งค่า Safety ครั้งเดียวจบ
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def configure_api(api_key):
    """ตั้งค่า Key"""
    if api_key:
        genai.configure(api_key=api_key)

def get_gemini_models(api_key):
    """ดึงรายชื่อโมเดลที่รองรับการสร้างเนื้อหา"""
    try:
        configure_api(api_key)
        # กรองเฉพาะรุ่นที่ generateContent ได้
        return [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except:
        return []

def get_best_model(api_key):
    """Auto-select โมเดลที่ดีที่สุด (Flash -> Pro -> อื่นๆ)"""
    models = get_gemini_models(api_key)
    # ลำดับความสำคัญ
    priority = [
        'models/gemini-2.5-flash',
        'models/gemini-2.5-flash-latest',
        'models/gemini-2.5-pro',
        'models/gemini-pro'
    ]
    for p in priority:
        if p in models: return p
    # กันตาย
    return models[0] if models else None

def generate_content(api_key, model_name, prompt, image=None, stream=False):
    """ฟังก์ชันยิง AI อเนกประสงค์"""
    try:
        configure_api(api_key)
        model = genai.GenerativeModel(model_name, safety_settings=SAFETY_SETTINGS)
        
        content = [prompt]
        if image:
            content.append(image)
            
        response = model.generate_content(content, stream=stream)
        
        if stream:
            return response # คืนค่าเป็น Generator
        else:
            return response.text
    except Exception as e:
        if "429" in str(e):
            return "API_ERROR: Quota Exceeded (โควต้าเต็ม)"
        return f"API_ERROR: {str(e)}"
