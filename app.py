import streamlit as st
import google.generativeai as genai
import json
import random
import datetime
import textwrap
import io
import re
from PIL import Image, ImageDraw, ImageFont

# --- 1. CONFIG & API ---
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Memo Generator | Sheet Appeal", page_icon="📝", layout="centered")

if 'email_data' not in st.session_state:
    st.session_state.email_data = None
if 'draft_img' not in st.session_state:
    st.session_state.draft_img = None

# --- 2. MODERN SAAS CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    /* Clean, modern app background */
    .stApp { 
        background-color: #f8fafc; 
        color: #0f172a; 
        font-family: 'Plus Jakarta Sans', sans-serif !important; 
    }

    /* Typography overrides */
    h1, h2, h3, p, label, [data-testid="stWidgetLabel"] p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #0f172a !important;
    }

    /* Style the main container to look compact and centered */
    .main .block-container { 
        max-width: 850px; 
        padding-top: 3rem; 
        padding-bottom: 3rem;
    }

    /* Custom Input Fields: Floating, clean, soft borders */
    [data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 14px 16px !important;
        font-size: 0.95rem;
        color: #334155 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: #0ea5e9 !important; /* Sheet Appeal accent color */
        box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1) !important;
    }
    
    /* Section Labels */
    .section-label {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748b;
        margin-bottom: 15px;
        margin-top: 10px;
    }

    /* Standard Buttons (Secondary) */
    [data-testid="baseButton-secondary"] {
        background-color: #ffffff;
        color: #334155;
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        font-weight: 600;
        height: 2.8em;
        transition: all 0.2s ease;
    }
    [data-testid="baseButton-secondary"]:hover { 
        background-color: #f1f5f9; 
        border-color: #94a3b8;
        color: #0f172a;
    }
    
    /* Primary Execute Button */
    [data-testid="baseButton-primary"] {
        background-color: #0ea5e9;
        background-image: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        height: 2.8em;
        box-shadow: 0 4px 6px -1px rgba(14, 165, 233, 0.2), 0 2px 4px -1px rgba(14, 165, 233, 0.1);
        transition: all 0.2s ease;
    }
    [data-testid="baseButton-primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 8px -1px rgba(14, 165, 233, 0.3), 0 4px 6px -1px rgba(14, 165, 233, 0.2);
        color: #ffffff;
    }
    
    /* Output Box */
    .output-card {
        background-color: #ffffff;
        padding: 35px;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        line-height: 1.7;
        margin-top: 30px;
        font-size: 1.05rem;
        color: #1e293b;
    }
    
    .output-header {
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER LOGIC & VOCABULARY ---
PROPER_NOUNS = ["The IRS", "Clippy", "Enron", "Gary from HR", "Burbank", "The 1997 Florida Marlins", "The Janitorial Union"]
FUNNY_SUBJECTS = [
    "Regarding bees in the bathrooms",
    "Kool-Aid in the water fountain",
    "Mandatory updates to internal communication protocol",
    "Action Required: Feral cats in the server room",
    "Update on the breakroom microwave incident",
    "Expense report rejection: 'Wizard Robes'",
    "Urgent: Gary's stapler has breached containment"
]

FUNNY_WORDS = {
    "Noun": ["Rotisserie Chicken", "Pivot Table", "Ham Sandwich", "Subpoena"],
    "Adjective": ["Damp", "Aggressive", "Suspicious", "Lumpy", "Passive-Aggressive"],
    "Verb": ["Audit", "Depreciate", "Ferment", "Yodel", "Recalculate"],
    "Place": ["Arby's Bathroom", "The Void", "Burbank", "The Breakroom"],
    "Corporate Jargon": ["Forced Synergy", "Core Competency", "Actionable Item", "Paradigm Shift", "Bandwidth"],
    "Absurd Office Supply": ["Ergonomic Kneeling Chair", "Decaf Coffee Pod", "Yellow Dry-Erase Marker", "Single-Ply Toilet Paper"],
    "Vague Metric": ["KPIs", "Eyeballs", "Touchbases", "Friction Points", "Actionables"],
    "Passive-Aggressive Sign-off": ["Govern yourself accordingly,", "Per my last email,", "Regretfully,", "Sent from my smart fridge,", "Warmly,"]
}

def generate_draft_image(text, to_val, subj_val):
    width, height = 800, 900
    paper = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(paper)
    
    try:
        font_header = ImageFont.truetype("calibri.ttf", 20)
        font_main = ImageFont.truetype("calibri.ttf", 22)
        font_title = ImageFont.truetype("calibrib.ttf", 24)
    except:
        font_header = font_main = font_title = ImageFont.load_default()
    
    margin, y = 40, 40
    
    draw.text((margin, y), "Message", font=font_title, fill=(15, 23, 42))
    y += 45
    
    headers = [
        ("From:", "Current User <user@corpnet.local>"),
        ("To:", to_val),
        ("Date:", str(datetime.date.today())),
        ("Subject:", subj_val)
    ]
    
    for label, val in headers:
        draw.text((margin, y), f"{label:<10} {val}", font=font_header, fill=(100, 116, 139))
        y += 30
        
    y += 15
    draw.line([(margin, y), (width - margin, y)], fill=(226, 232, 240), width=1)
    y += 35
    
    clean_text = text.replace('**', '')
    for line in clean_text.split('\n'):
        for w_line in textwrap.wrap(line, width=65):
            draw.text((margin, y), w_line, font=font_main, fill=(30, 41, 59))
            y += 32
        y += 15
        
    img_byte_arr = io.BytesIO()
    paper.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# --- 4. TOP UI (HEADER) ---
st.markdown("<h1 style='text-align: center; color: #0f172a; margin-bottom: 5px; font-weight: 800;'>Mad Lib Memo Generator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b; margin-bottom: 40px; font-size: 1.1rem;'>Turn absolute nonsense into corporate reality.</p>", unsafe_allow_html=True)

# Metadata Section
st.markdown("<div class='section-label'>MEMO DETAILS</div>", unsafe_allow_html=True)
header_col1, header_col2 = st.columns(2, gap="medium")
with header_col1:
    to_val = st.text_input("To", key="to_field", placeholder="e.g. Gary from HR")
with header_col2:
    subj_val = st.text_input("Subject", key="subject_field", placeholder="e.g. Feral cats in the server room")

st.write("") 

# --- 5. DATA ENTRY ---
st.markdown("<div class='section-label'>MAD LIB VARIABLES</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2, gap="medium")
word_keys = list(FUNNY_WORDS.keys())

for i, label in enumerate(word_keys):
    with col1 if i < 4 else col2:
        st.text_input(label, key=f"field_{label}", placeholder=f"Enter a {label.lower()}...")

def randomize_data():
    st.session_state.to_field = random.choice(PROPER_NOUNS)
    st.session_state.subject_field = random.choice(FUNNY_SUBJECTS)
    for key in FUNNY_WORDS.keys():
        st.session_state[f"field_{key}"] = random.choice(FUNNY_WORDS[key])

def reset_data():
    st.session_state.to_field = ""
    st.session_state.subject_field = ""
    for key in FUNNY_WORDS.keys():
        st.session_state[f"field_{key}"] = ""
    st.session_state.email_data = None
    st.session_state.draft_img = None

st.write("")
st.write("")

# Button row - Now perfectly aligned natively
btn_col1, btn_col2, btn_col3 = st.columns(3, gap="medium")
with btn_col1:
    st.button("Auto-Fill", on_click=randomize_data, use_container_width=True)
with btn_col2:
    st.button("Clear", on_click=reset_data, use_container_width=True)
with btn_col3:
    execute = st.button("Generate Memo ✨", type="primary", use_container_width=True)

# --- 6. EXECUTION & OUTPUT ---
if execute:
    collected_main = []
    sign_off_val = ""
    
    for label in word_keys:
        val = st.session_state.get(f"field_{label}", "").strip()
        if label == "Passive-Aggressive Sign-off":
            sign_off_val = val
        else:
            collected_main.append(val)
    
    if not to_val or not subj_val or not sign_off_val or any(not val for val in collected_main):
        st.error("Missing Data: Please fill out all fields before generating the memo.")
    else:
        with st.spinner("Drafting memo..."):
            prompt = f"""
            Write a highly concise corporate email regarding '{subj_val}'.
            STYLE: Extremely dry, bureaucratic, and jargon-heavy (think Office Space). 
            LENGTH LIMIT: STRICTLY TWO SHORT PARAGRAPHS. Absolute maximum of 6 sentences total for the body. Corporate memos are brutally brief, dense, and to the point. Cut all fluff and pleasantries.
            
            THE VARIABLES TO INTEGRATE INTO THE BODY:
            - Primary Stakeholder/Recipient: {to_val}
            - Other details: {json.dumps(collected_main)}
            
            - Bold all these provided variables exactly like this: **word**. Do not bold other words.
            
            SIGN-OFF:
            Conclude the email by placing this exact phrase on its own line at the very end (bold it): **{sign_off_val}**
            """
            try:
                response = client.models.generate_content(model='gemma-3-27b-it', contents=prompt)
                st.session_state.email_data = response.text
            except Exception as e:
                st.error(f"Network Error: {e}")

if st.session_state.email_data:
    body_html = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #0ea5e9;">\1</strong>', st.session_state.email_data)
    
    report_html = f"""
    <div class="output-card">
        <div class="output-header"><strong>To:</strong> {to_val}</div>
        <div class="output-header"><strong>Subject:</strong> {subj_val}</div>
        <hr style="border:none; border-top:1px solid #e2e8f0; margin: 20px 0;">
        {body_html}
    </div>
    """
    st.markdown(report_html, unsafe_allow_html=True)

    st.write("---")
    l_col1, l_col2 = st.columns([1, 2])
    with l_col1:
        if st.button("Save as Image 💾"):
            st.session_state.draft_img = generate_draft_image(st.session_state.email_data, to_val, subj_val)

    if st.session_state.draft_img:
        st.image(st.session_state.draft_img, caption="memo_export.png", use_container_width=True)
        st.download_button("Download Image Export", data=st.session_state.draft_img, file_name="memo_export.png", mime="image/png")

# --- 7. FOOTER ---
st.markdown("<div style='text-align: center; margin-top: 60px; color: #94a3b8; font-size: 0.9rem; font-weight: 500;'>Brought to you by <span style='color: #0ea5e9; font-weight: 700;'>Sheet Appeal</span></div>", unsafe_allow_html=True)