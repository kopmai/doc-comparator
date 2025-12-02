import google.generativeai as genai
import streamlit as st

# ตั้งค่าความปลอดภัย (ใช้ร่วมกันทั้งแอป)
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def configure_api(api_key):
    """ตั้งค่า API Key"""
    if api_key:
        genai.configure(api_key=api_key)

def get_best_model(api_key):
    """Auto-select โมเดลที่ดีที่สุด (Flash -> Pro)"""
    try:
        configure_api(api_key)
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # ลำดับความสำคัญ
        priority = [
            'models/gemini-2.5-flash',
            'models/gemini-2.5-flash-latest',
            'models/gemini-2.5-pro',
            'models/gemini-pro'
        ]
        
        for p in priority:
            if p in all_models: return p
            
        return all_models[0] if all_models else None
    except:
        return None

def generate_content(api_key, model_name, prompt, image=None, stream=False):
    """ฟังก์ชันยิง AI อเนกประสงค์ (รองรับทั้ง Text และ Image)"""
    try:
        configure_api(api_key)
        model = genai.GenerativeModel(model_name, safety_settings=SAFETY_SETTINGS)
        
        content = [prompt]
        if image:
            content.append(image)
            
        response = model.generate_content(content, stream=stream)
        
        if stream:
            return response # คืนค่าเป็น Generator สำหรับ Streaming
        else:
            return response.text
    except Exception as e:
        if "429" in str(e):
            return "API_ERROR: Quota Exceeded (โควต้าเต็ม กรุณารอสักครู่)"
        return f"API_ERROR: {str(e)}"
