import streamlit as st
import google.generativeai as genai
import pypdf
import os
import tempfile
from gtts import gTTS

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="JurisAI Pro",
    page_icon="⚖️",
    layout="wide"
)

# --- CUSTOM CSS (Unified Input Bar Look) ---
st.markdown("""
    <style>
    /* 1. Hide Standard Streamlit Elements */
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stHeader"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    footer {visibility: hidden;}

    /* 2. Main Title Styling */
    .main-title {
        font-size: 3rem;
        background: -webkit-linear-gradient(45deg, #4F8BF9, #9b59b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        text-align: center;
        margin-top: 20px;
    }

    /* 3. FIXED BOTTOM CONTAINER (The "Command Center") */
    .bottom-container {
        position: fixed;
        bottom: 80px; /* Sits right above the chat input */
        left: 0;
        width: 100%;
        background-color: #0e1117; /* Matches dark theme */
        padding: 10px 50px;
        z-index: 99;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* 4. Chat Input Styling */
    .stChatInput {
        padding-bottom: 20px;
    }
    
    /* 5. Compact File Uploader & Audio */
    [data-testid="stFileUploader"] {
        width: 100%;
    }
    .stAudio {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- API KEY ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.warning("⚠️ API Key missing.")
    st.stop()

# --- HELPER FUNCTIONS ---
def get_pdf_text(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except:
        return ""

# --- MAIN UI ---
st.markdown('<div class="main-title">JurisAI Pro</div>', unsafe_allow_html=True)
st.caption("Example: 'Draft a rent agreement for a shop in Bangalore' or 'Explain IPC 302'")

# --- CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am JurisAI. Use the tools below 👇 to upload files or speak."}]

# Display Chat Messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user", avatar="🧑‍⚖️").write(msg["content"])
    else:
        st.chat_message("assistant", avatar="⚖️").markdown(msg["content"])

# --- 🚀 THE "COMMAND CENTER" (Fixed at Bottom) ---
# We use a container to hold the file/audio tools just above the chat bar
with st.container():
    # Use columns to put Audio and File side-by-side
    c1, c2, c3 = st.columns([0.1, 2, 2]) # Spacer, Audio, File
    
    with c2:
        # Audio Input (Standard Streamlit Widget)
        audio_val = st.audio_input("🎙️ Record Voice") 
    
    with c3:
        # File Uploader
        uploaded_file = st.file_uploader("📎 Attach Evidence", type=["pdf"], label_visibility="collapsed")

# --- PROCESSING INPUTS ---
pdf_text = ""
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        pdf_text = get_pdf_text(tmp.name)[:50000]
    st.toast("✅ File Attached to Context")

if audio_val:
    st.toast("✅ Audio Recorded (Processing functionality pending)")

# --- CHAT INPUT (Always at very bottom) ---
if prompt := st.chat_input("Type your legal question here..."):
    
    # 1. Add User Message to History
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar="🧑‍⚖️").write(prompt)

    # 2. Generate Response
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    full_prompt = f"""
    Act as a Legal Consultant.
    Context from PDF: {pdf_text}
    Question: {prompt}
    """
    
    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("Analyzing..."):
            response = model.generate_content(full_prompt).text
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
