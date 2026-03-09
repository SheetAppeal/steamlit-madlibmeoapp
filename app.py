import streamlit as st
from google import genai
from google.genai import types
import random
import re

# --- 1. CONFIG & API (MUST BE FIRST) ---
st.set_page_config(page_title="Linguistic Processor | Sheet Appeal", page_icon="🗂️", layout="centered")

API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

if 'email_data' not in st.session_state:
    st.session_state.email_data = None

# --- 2. GLOBAL CSS & BRANDING OVERRIDES ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime&family=Jost:wght@400;500&display=swap');

    /* Hide Streamlit Header, Footer, and Scrollbars */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp::-webkit-scrollbar { display: none; }
    .stApp { -ms-overflow-style: none; scrollbar-width: none; }

    :root {
        --archival-paper: #FDFBF7;
        --faded-ledger: #D3D8D3;
        --vintage-cell-green: #2E8555;
        --lobby-boy-pink: #E29587;
        --courtesan-mustard: #E4B363;
    }

    /* Base Typography and Canvas */
    .stApp { 
        background-color: var(--archival-paper); 
        color: var(--vintage-cell-green); 
        font-family: 'Courier Prime', monospace !important; 
    }

    h1, h2, h3 {
        font-family: 'Jost', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        font-weight: 500 !important;
        color: var(--vintage-cell-green) !important;
    }

    p, label, [data-testid="stWidgetLabel"] p, span, div {
        font-family: 'Courier Prime', monospace !important;
        color: var(--vintage-cell-green) !important;
    }

    /* The Master Container */
    .main .block-container { 
        max-width: 850px; 
        padding-top: 1rem; 
        padding-bottom: 3rem;
    }

    /* Logo Styling */
    .sa-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 70px;
        height: 70px;
        border: 3px solid var(--vintage-cell-green);
        background-color: var(--archival-paper);
        color: var(--vintage-cell-green);
        font-family: 'Jost', sans-serif !important;
        font-size: 2.5rem;
        font-weight: 500;
        letter-spacing: 0.05em;
        margin: 0 auto 20px auto;
        box-shadow: 6px 6px 0px var(--lobby-boy-pink);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        cursor: pointer;
    }
    .sa-logo:hover {
        transform: translate(2px, 2px);
        box-shadow: 4px 4px 0px var(--courtesan-mustard);
    }

    .header-section {
        margin-bottom: 40px;
    }
    
    .header-section h1 {
        font-size: 1.4rem !important; 
        letter-spacing: 0.4em !important; 
        margin: 10px 0 15px 0 !important;
        opacity: 0.9;
        text-align: center;
    }
    .mission-statement {
        text-align: center;
        font-size: 1rem;
        letter-spacing: 0.05em;
    }

    /* Custom Input Fields: Force rigid corners */
    div[data-testid="stTextInput"] * {
        border-radius: 0px !important;
    }
    
    div[data-baseweb="input"] {
        background-color: var(--archival-paper) !important;
        border: 2px solid var(--vintage-cell-green) !important;
        transition: all 0.2s ease;
    }
    
    div[data-baseweb="input"]:focus-within {
        border-color: var(--lobby-boy-pink) !important;
        box-shadow: 4px 4px 0px var(--courtesan-mustard) !important;
    }
    
    div[data-baseweb="input"] input {
        background-color: transparent !important;
        color: var(--vintage-cell-green) !important;
        font-family: 'Courier Prime', monospace !important;
        padding: 12px 16px !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Section Labels */
    .section-label {
        font-family: 'Jost', sans-serif !important;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        border-bottom: 2px solid var(--faded-ledger);
        padding-bottom: 5px;
        margin-bottom: 15px;
        margin-top: 10px;
    }

    /* The Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 0px !important;
        border: 2px solid var(--vintage-cell-green) !important;
        height: 3.2rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 15px !important;
        transition: all 0.2s ease;
    }
    
    .stButton > button p {
        font-family: 'Jost', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        font-size: 0.85rem !important;
        margin: 0 !important;
        white-space: nowrap !important;
    }

    [data-testid="baseButton-secondary"] { background-color: var(--vintage-cell-green) !important; }
    [data-testid="baseButton-secondary"] p { color: var(--archival-paper) !important; }
    [data-testid="baseButton-secondary"]:hover { background-color: var(--archival-paper) !important; }
    [data-testid="baseButton-secondary"]:hover p { color: var(--vintage-cell-green) !important; }

    [data-testid="baseButton-primary"] { background-color: var(--archival-paper) !important; }
    [data-testid="baseButton-primary"] p { color: var(--vintage-cell-green) !important; }
    [data-testid="baseButton-primary"]:hover { background-color: var(--vintage-cell-green) !important; }
    [data-testid="baseButton-primary"]:hover p { color: var(--archival-paper) !important; }

    .output-card {
        background-color: var(--archival-paper);
        padding: 40px;
        border: 2px solid var(--vintage-cell-green);
        margin-top: 30px;
        line-height: 1.6;
        font-size: 1.05rem;
    }
    
    .output-header {
        font-family: 'Jost', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 8px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER LOGIC & VOCABULARY ---
PROPER_NOUNS = [
    "The Ghost of Lehman Brothers", "The HOA", "Y2K Survivalists", 
    "Burbank Parking Authority", "That guy who microwaves fish", 
    "The Shadow Council", "Middle Management"
]

FUNNY_SUBJECTS = [
    "Please stop reply-alling to the fire alarm",
    "Update: The water cooler is now sentient",
    "Regarding the chanting in conference room B",
    "Action Required: Stop using company funds for V-Bucks",
    "Dress code reminder: Chainmail is not business casual",
    "Who keeps printing out the entire internet?"
]

FUNNY_WORDS = {
    "Suspicious Liquid": ["Brake fluid", "Hot dog water", "Room-temperature milk", "Ectoplasm", "Liquid smoke"],
    "Obsolete Tech": ["Zune", "Fax machine", "Pager", "Overhead projector", "Floppy disk"],
    "Breakroom Activity (-ing)": ["Astral projecting", "Unionizing", "Deep-frying", "Yodeling", "Performative weeping"],
    "Unsettling Snack (plural)": ["Pickled eggs", "Loose pocket-tater-tots", "Unlabeled meat tubes", "Floor-pretzels", "Dehydrated water"],
    "Inappropriate Attire": ["JNCO jeans", "Velcro sandals", "A monocle", "Pleather pants", "A prop comedy tie"],
    "Sign-off phrase": ["Apologetically,", "May God have mercy on our KPIs,", "Sent from my aggressively loud mechanical keyboard,", "With a heavy heart,", "Survive the week,"]
}

# --- 4. CONDITIONAL TOP UI (HEADER) ---
is_embedded = st.query_params.get("hide_logo") == "true"

if not is_embedded:
    st.markdown("""
        <div class="header-section">
            <div class="sa-logo">SA</div>
            <h1>LINGUISTIC PROCESSOR</h1>
            <div class="mission-statement">A structured narrative diversion for the creatively starved.</div>
        </div>
    """, unsafe_allow_html=True)

# --- 5. DATA ENTRY ---
st.markdown("<div class='section-label'>Memo Details</div>", unsafe_allow_html=True)
header_col1, header_col2 = st.columns(2, gap="medium")
with header_col1:
    to_val = st.text_input("To", key="to_field", placeholder="e.g. The Shadow Council")
with header_col2:
    subj_val = st.text_input("Subject", key="subject_field", placeholder="e.g. Update: The water cooler is now sentient")

st.write("") 

st.markdown("<div class='section-label'>MAD LIB VARIABLES</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2, gap="medium")
word_keys = list(FUNNY_WORDS.keys())

# Dynamically split the items evenly between columns
half_point = (len(word_keys) + 1) // 2 
for i, label in enumerate(word_keys):
    with col1 if i < half_point else col2:
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

st.write("")
st.write("")

# Button row 
btn_col1, btn_col2, btn_col3 = st.columns(3, gap="medium")
with btn_col1:
    st.button("Auto-Fill", on_click=randomize_data, use_container_width=True)
with btn_col2:
    st.button("Clear", on_click=reset_data, use_container_width=True)
with btn_col3:
    execute = st.button("Generate Memo", type="primary", use_container_width=True)


# --- 6. EXECUTION & OUTPUT (METHOD 2 + NEW BRAIN) ---
if execute:
    # Validation
    missing_fields = []
    if not to_val: missing_fields.append("To")
    if not subj_val: missing_fields.append("Subject")
    
    user_inputs = {}
    sign_off_val = ""
    placeholder_instructions = ""
    
    # We dynamically map your specific rules to the exact categories
    guardrails = {
        "Suspicious Liquid": "Treat as a singular, uncountable noun (e.g., 'spilled {placeholder} on the floor').",
        "Obsolete Tech": "Treat as a singular, countable noun (e.g., 'the broken {placeholder}').",
        "Breakroom Activity (-ing)": "Treat strictly as a gerund/action ending in -ing (e.g., 'caught them {placeholder} near the copier').",
        "Unsettling Snack (plural)": "Treat strictly as a plural noun (e.g., 'eating all the {placeholder}').",
        "Inappropriate Attire": "Treat as an article of clothing (e.g., 'wearing {placeholder} to the client meeting')."
    }
    
    for label in word_keys:
        val = st.session_state.get(f"field_{label}", "").strip()
        if not val:
            missing_fields.append(label)
            
        if label == "Sign-off phrase":
            sign_off_val = val
        else:
            clean_placeholder = f"[{re.sub(r'[^a-zA-Z0-9]', '_', label).upper()}]"
            user_inputs[clean_placeholder] = val
            
            # Match the rule to the placeholder for the AI
            rule = guardrails.get(label, "Treat as a standard noun.").replace("{placeholder}", clean_placeholder)
            placeholder_instructions += f"- {clean_placeholder}: {rule}\n"

    if missing_fields:
        st.error("Missing Data: Please hit 'Auto-Fill' or manually complete all fields before generating.")
    else:
        with st.spinner("Processing linguistic parameters..."):
            
            # The New Brain Prompt
            
            prompt = f"""
            Role and Persona:
            You are an emotionless, highly professional corporate compliance system generating a standard administrative notification.

            The Assignment:
            Write a direct, seamlessly flowing email to "{to_val}" addressing the following issue: "{subj_val}".
            The email MUST have a clear narrative focused entirely on this specific subject.

            The Twist (How to use the placeholders):
            Weave these bracketed placeholders into the email. Treat them as completely normal corporate assets, incidents, or tools:
            {placeholder_instructions}

            Content & Style Rules:
            1. SMOOTH AND STERILE: Write in fluid, standard business English. The tone must be completely emotionless, dry, and professional. 
            2. NO DRAMA: Do not include dramatic pauses, excessive commas, or personal complaints. Do not try to be funny or theatrical. 
            3. LENGTH AND FLOW: Aim for 3 to 4 smooth, easily readable sentences. Use clear, direct sentence structures without unnecessary parentheticals.
            4. BANNED WORDS: You are strictly forbidden from using the word "synergy", "synergize", or any variation of it.
            5. CUT THE FLUFF: NO headers. Do NOT output "To:", "Subject:", or any greetings. Start immediately with the first sentence of the body.
            
            Write the template now:
            """
            
            try:
                response = client.models.generate_content(
                    model='gemma-3-27b-it', 
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.7)
                )
                
                template = response.text
                
                # Python aggressively replaces the brackets with the user's words and bolds them
                for placeholder, user_word in user_inputs.items():
                    template = template.replace(placeholder, f"**{user_word}**")
                
                # Tack the sign-off onto the end
                template += f"\n\n**{sign_off_val}**"
                
                st.session_state.email_data = template
                
            except Exception as e:
                st.error(f"Network Error: {e}")

# --- 7. OUTPUT DISPLAY ---
if st.session_state.email_data:
    # Convert markdown bold to HTML strong tags with the mustard color for popping effect
    body_html = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: var(--courtesan-mustard);">\1</strong>', st.session_state.email_data)
    
    report_html = f"""
    <div class="output-card">
        <div class="output-header"><strong>To:</strong> {to_val}</div>
        <div class="output-header"><strong>Subject:</strong> {subj_val}</div>
        <hr style="border:none; border-top:2px solid var(--faded-ledger); margin: 20px 0;">
        <div style="margin: 0;">{body_html}</div>
    </div>
    """
    st.markdown(report_html, unsafe_allow_html=True)

# --- 8. FOOTER ---
st.markdown("""
    <div style='text-align: center; margin-top: 60px; color: #2E8555; font-size: 0.9rem; font-family: "Courier Prime", monospace;'>
        Brought to you by <a href="https://sheetappeal.net" target="_blank" style="color: #E29587; font-weight: bold; text-decoration: none;">Sheet Appeal</a>
    </div>
""", unsafe_allow_html=True)