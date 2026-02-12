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

# --- CUSTOM CSS (Gemini-Like Cleanup) ---
st.markdown("""
    <style>
    /* 1. Hide Sidebar & Premium Elements */
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
        margin-bottom: 0px;
    }
    
    /* 3. Make Chat Input Look Modern */
    .stChatInput {
        padding-bottom: 20px;
    }
    
    /* 4. Tool Bar Styling */
    .stSelectbox, .stFileUploader {
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER: GET PDF TEXT ---
def get_pdf_text(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except:
        return ""

# --- API KEY (AUTO) ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    # If no secrets, show a temporary warning
    st.warning("⚠️ API Key missing in Secrets.")
    st.stop()

# --- MAIN HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown('<div class="main-title">JurisAI Pro</div>', unsafe_allow_html=True)
    st.caption("Your Personal AI Legal Assistant • VTU 2026")

# --- 🛠️ THE NEW "TOOL KIT" BAR ---
# We use an expander or columns to keep it neat
with st.expander("🛠️ Open Toolkit (Uploads & Settings)", expanded=False):
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        language = st.selectbox("🗣️ Language", ["English", "Hindi", "Kannada"])
    
    with col2:
        enable_audio = st.toggle("🔊 Read Aloud", value=False)
        st.write("") # Spacer

    with col3:
        uploaded_file = st.file_uploader("📂 Upload Case File (PDF)", type="pdf")

# --- FILE PROCESSING LOGIC ---
pdf_text = ""
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        pdf_text = get_pdf_text(tmp.name)[:50000]
    st.toast(f"✅ Evidence Loaded: {uploaded_file.name}")
elif os.path.exists("law_data.pdf"):
    pdf_text = get_pdf_text("law_data.pdf")[:50000]

# --- CHAT HISTORY & LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am ready to assist. You can open the Toolkit above 👆 to upload files."}]

# Display History
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user", avatar="🧑‍⚖️").write(msg["content"])
    else:
        st.chat_message("assistant", avatar="⚖️").markdown(msg["content"])

# --- RESPONSE GENERATION FUNCTION ---
def get_response(query, history):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Act as an expert Indian Legal Consultant.
    Language: {language}
    Context: {pdf_text}
    History: {history}
    Question: {query}
    Keep answers precise, professional, and point-wise.
    """
    return model.generate_content(prompt).text

# --- INPUT AREA (FIXED AT BOTTOM) ---
if prompt := st.chat_input("Type your legal question here..."):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar="🧑‍⚖️").write(prompt)

    # 2. AI Response
    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("Analyzing Law..."):
            history_str = str(st.session_state.messages[-4:])
            response = get_response(prompt, history_str)
            st.markdown(response)
            
            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": response})

            # 3. Audio (Auto-Play)
            if enable_audio:
                try:
                    lang_code = {"English": "en", "Hindi": "hi", "Kannada": "kn"}.get(language, "en")
                    tts = gTTS(text=response, lang=lang_code, slow=False)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        tts.save(fp.name)
                        st.audio(fp.name, format="audio/mp3", start_time=0)
                except:
                    pass
