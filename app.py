import streamlit as st
from modules.loader import DocumentLoader
from modules.comparator import TextComparator 
from modules.code_view import render_code_compare_mode
# Import ไฟล์ใหม่
from modules.spell_check_view import render_spell_check_mode
import streamlit.components.v1 as components

# --- 1. CONFIG & STYLES ---
st.set_page_config(layout="wide", page_title="Pro Document Comparator", page_icon="⚖️")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

        html, body, [class*="css"], font, button, input, textarea, div { font-family: 'Kanit', sans-serif !important; }
        
        header[data-testid="stHeader"] { background-color: transparent !important; z-index: 999999 !important; }
        div[data-testid="stDecoration"] { display: none; }
        .block-container { padding-top: 75px !important; padding-bottom: 1rem !important; }
        
        .top-navbar {
            position: fixed; top: 0; left: 0; right: 0; height: 60px;
            background-color: #ffffff; border-bottom: 1px solid #e0e0e0;
            z-index: 99999; display: flex; align-items: center; padding-left: 80px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .navbar-logo { font-size: 22px; font-weight: 600; color: #2b5876; display: flex; align-items: center; gap: 10px; }

        div[data-baseweb="base-input"], div[data-baseweb="textarea"] { 
            border: 1px solid #ced4da !important; border-radius: 8px !important; background-color: #ffffff !important; 
        }
        
        .css-card { background-color: white; padding: 1rem 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #eef0f2; margin-top: -15px; }
        .match-badge { background-color: #2b5876; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.9rem; }
        section[data-testid="stSidebar"] { top: 60px !important; background-color: #f8f9fa; }
        textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 14px !important; }
    </style>
    <div class="top-navbar"><div class="navbar-logo"><span>⚖️</span> DocCompare <span style="font-size: 14px; color: #adb5bd; margin-left: 10px; font-weight: 300;">| ระบบเปรียบเทียบเอกสารและโค้ด</span></div></div>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.markdown("### 🛠️ เครื่องมือ (Tools)")
    # เพิ่มเมนูที่ 3
    app_mode = st.radio("เลือกโหมดการทำงาน", 
                        ["📄 เปรียบเทียบเอกสาร", 
                         "💻 เปรียบเทียบโค้ด (Source Code)",
                         "📝 ตรวจการสะกดคำ (Spell Check)"])
    
    st.markdown("---")
    
    if app_mode == "📄 เปรียบเทียบเอกสาร":
        st.markdown("### 📂 Upload Files")
        file1 = st.file_uploader("ต้นฉบับ (Original)", type=["docx", "pdf"])
        file2 = st.file_uploader("ฉบับแก้ไข (Modified)", type=["docx", "pdf"])
        st.markdown("---")
        st.markdown("### 👁️ Options")
        view_mode = st.radio("มุมมอง", ["แสดงทั้งหมด", "เฉพาะจุดต่าง"], index=0)
        mode_key = "diff_only" if view_mode == "เฉพาะจุดต่าง" else "all"
        
    elif app_mode == "💻 เปรียบเทียบโค้ด (Source Code)":
        st.info("💡 แปะโค้ดที่ต้องการเปรียบเทียบลงในช่อง Text Area ด้านขวาได้เลย")
        mode_key = "all" # Default Code Mode

    elif app_mode == "📝 ตรวจการสะกดคำ (Spell Check)":
        st.info("💡 วางข้อความภาษาไทย หรืออังกฤษ ระบบจะ Highlight คำที่น่าจะสะกดผิดให้")

# --- 3. MAIN LOGIC ---

if app_mode == "📄 เปรียบเทียบเอกสาร":
    # ... (Logic เดิมของ Document Compare) ...
    if file1 and file2:
        with st.spinner('⏳ กำลังประมวลผลไฟล์...'):
            try:
                type1, type2 = file1.name.split('.')[-1].lower(), file2.name.split('.')[-1].lower()
                text1 = DocumentLoader.extract_text(file1, type1)
                text2 = DocumentLoader.extract_text(file2, type2)
                
                col_search, col_count = st.columns([4, 1])
                with col_search:
                    search_query = st.text_input("", placeholder="🔍 พิมพ์คำค้นหา...")
                
                match_count = 0
                if search_query:
                    text1 = [line for line in text1 if search_query in line]
                    text2 = [line for line in text2 if search_query in line]
                    match_count = sum(line.count(search_query) for line in text1) + sum(line.count(search_query) for line in text2)
                
                with col_count:
                    if search_query:
                        badge_color = "#2b5876" if match_count > 0 else "#dc3545"
                        msg = f"เจอ {match_count} จุด" if match_count > 0 else "ไม่พบข้อมูล"
                        st.markdown(f"<div style='text-align:right; padding-top: 8px;'><span class='match-badge' style='background-color:{badge_color};'>{msg}</span></div>", unsafe_allow_html=True)

                comparator = TextComparator()
                current_mode = "all" if search_query else mode_key
                
                raw_html = comparator.generate_diff_html(text1, text2, mode=current_mode)
                final_html = comparator.get_final_display_html(raw_html, search_query)

                st.markdown('<div class="css-card">', unsafe_allow_html=True)
                components.html(final_html, height=800, scrolling=True)
                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
    else:
        st.info("👈 กรุณาอัปโหลดไฟล์ Word/PDF ที่เมนูด้านซ้าย")

elif app_mode == "💻 เปรียบเทียบโค้ด (Source Code)":
    # ... (Logic เดิมของ Code Compare) ...
    # เราส่ง mode_key เข้าไป แต่จริงๆ ใน Code View เรา hardcode ปุ่มไว้แล้ว
    # หรือจะแก้ Code View ให้รับ view_mode ก็ได้ แต่นี่ใช้แบบเดิมไปก่อนครับ
    render_code_compare_mode("all") 

elif app_mode == "📝 ตรวจการสะกดคำ (Spell Check)":
    # เรียกใช้ฟังก์ชันใหม่
    render_spell_check_mode()
