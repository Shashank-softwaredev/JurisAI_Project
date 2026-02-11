import streamlit as st
import google.generativeai as genai
import pypdf
import os
import tempfile
from gtts import gTTS

# --- 1. PAGE CONFIGURATION (Standard Wide Mode) ---
st.set_page_config(
    page_title="JurisAI Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CLEAN CSS (Hides Branding & Widens Chat) ---
st.markdown("""
    <style>
    /* Hide Streamlit Branding (Header, Footer, Menu) */
    [data-testid="stHeader"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    footer {display: none;}
    
    /* Make Chat Input Wide & Clean */
    .stChatInput {
        padding-bottom: 20px;
    }
    
    /* Center the Main Title */
    .main-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #4F8BF9, #9b59b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: -50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (All Controls Go Here) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/924/924915.png", width=80)
    st.title("JurisAI Controls")
    
    # Automatic API Key Check
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("🔐 API Key Verified")
    except:
        api_key = st.text_input("Enter API Key:", type="password")
        
    st.markdown("---")
    
    # File Uploader
    uploaded_file = st.file_uploader("📂 Upload Case File (PDF)", type="pdf")
    
    # Settings
    language = st.selectbox("🗣️ Language", ["English", "Hindi", "Kannada"])
    enable_audio = st.toggle("🔊 Read Aloud Response", value=False)
    
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- 4. BACKEND LOGIC ---
def get_pdf_text(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except:
        return ""

# Handle PDF Context
pdf_text = ""
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        pdf_text = get_pdf_text(tmp.name)[:50000]
    st.toast(f"✅ Loaded: {uploaded_file.name}")
elif os.path.exists("law_data.pdf"):
    pdf_text = get_pdf_text("law_data.pdf")[:50000]

# --- 5. MAIN CHAT INTERFACE ---
st.markdown("""
    <style>
    /* --- 1. HIDE STREAMLIT BRANDING (The "Nuclear" Option) --- */
    
    /* Hides the top header bar completely */
    [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Hides the "Deploy" button and the 3-dot menu */
    [data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* Hides the specific "Deploy" button if it remains */
    [data-testid="stDeployButton"] {
        display: none !important;
    }
    
    /* Hides the "Stop/Running" animation in top right */
    [data-testid="stStatusWidget"] {
        display: none !important;
    }
    
    /* Hides the footer "Made with Streamlit" */
    footer {
        display: none !important;
    }
    
    /* Hides the colored line at the top of the screen */
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* --- 2. MAKE CHAT INPUT WIDER --- */
    
    /* This forces the chat input to ignore the default width limit */
    .stChatInput {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* This targets the bottom container to ensure it stretches to the edges */
    [data-testid="stBottom"] > div {
        width: 100% !important;
        max-width: 100% !important;
        padding-left: 2rem;   /* Adds a little breathing room on the left */
        padding-right: 2rem;  /* Adds a little breathing room on the right */
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize History
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your AI Legal Assistant. How can I help you today?"}]

# Display Chat
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user", avatar="🧑‍⚖️").write(msg["content"])
    else:
        st.chat_message("assistant", avatar="⚖️").markdown(msg["content"])

# --- 6. CHAT INPUT & RESPONSE ---
if prompt := st.chat_input("Type your legal question here..."):
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar="🧑‍⚖️").write(prompt)

    # Check API Key
    if not api_key:
        st.error("⚠️ Please enter an API Key in the sidebar.")
        st.stop()

    # Generate Response
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    full_prompt = f"""
    Act as an expert Legal Consultant.
    Language: {language}
    Context from PDF: {pdf_text}
    Chat History: {st.session_state.messages}
    User Question: {prompt}
    
    Provide a clear, point-wise legal answer.
    """
    
    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("Analyzing Law..."):
            try:
                response = model.generate_content(full_prompt).text
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Audio Playback
                if enable_audio:
                    lang_code = {"English": "en", "Hindi": "hi", "Kannada": "kn"}.get(language, "en")
                    tts = gTTS(text=response, lang=lang_code, slow=False)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        tts.save(fp.name)
                        st.audio(fp.name, format="audio/mp3")
            except Exception as e:
                st.error(f"Error: {e}")
