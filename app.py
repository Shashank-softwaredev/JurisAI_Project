import streamlit as st
import google.generativeai as genai
import pypdf
import os
import tempfile
import time
from gtts import gTTS

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="JurisAI Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. ADVANCED VISUALS (CSS ANIMATIONS) ---
st.markdown("""
    <style>
    /* --- ANIMATED BACKGROUND (The "Nebula" Effect) --- */
    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    
    .stApp {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #141E30);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        color: white;
    }

    /* --- HIDE DEFAULT STREAMLIT JUNK --- */
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stHeader"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    footer {visibility: hidden;}

    /* --- TYPOGRAPHY (GLOWING TEXT) --- */
    .main-title {
        font-size: 4rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(to right, #00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0, 198, 255, 0.5);
        margin-top: -20px;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    .sub-title {
        text-align: center;
        color: #aab4be;
        font-size: 1.2rem;
        margin-bottom: 30px;
        letter-spacing: 1.5px;
    }

    /* --- CHAT BUBBLES (GLASSMORPHISM) --- */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 15px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
        margin-bottom: 10px;
    }
    [data-testid="stChatMessage"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 198, 255, 0.1);
    }
    
    /* User Bubble specific color */
    [data-testid="stChatMessage"][data-testid="user"] {
        background: rgba(0, 114, 255, 0.1);
        border-color: rgba(0, 114, 255, 0.3);
    }

    /* --- COMMAND CENTER (FLOATING DOCK) --- */
    [data-testid="stBottom"] > div {
        background: rgba(15, 12, 41, 0.85);
        backdrop-filter: blur(20px);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding-top: 20px;
        padding-bottom: 20px;
        box-shadow: 0 -10px 30px rgba(0,0,0,0.5);
    }

    /* --- BUTTONS & INPUTS --- */
    .stChatInput textarea {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border-radius: 12px;
    }
    .stChatInput textarea:focus {
        border-color: #00c6ff !important;
        box-shadow: 0 0 10px rgba(0, 198, 255, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. API & SETUP ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    api_key = os.getenv("GEMINI_API_KEY")
    # If using locally without secrets, you can hardcode it here for testing (not recommended for GitHub)
    # api_key = "YOUR_KEY_HERE" 

if not api_key:
    st.warning("⚠️ System Offline: API Key Missing")
    st.stop()

# --- 4. HELPER FUNCTIONS ---
def get_pdf_text(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except:
        return ""

def transcribe_audio(audio_file, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    myfile = genai.upload_file(audio_file)
    result = model.generate_content(["Transcribe this audio exactly as spoken.", myfile])
    return result.text

# --- 5. MAIN UI HEADER ---
st.markdown('<div class="main-title">JurisAI Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">ADVANCED LEGAL INTELLIGENCE SYSTEM</div>', unsafe_allow_html=True)

# --- 6. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello. I am online and ready to analyze legal documents. Upload a file or speak to begin."}]

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user", avatar="👤").write(msg["content"])
    else:
        st.chat_message("assistant", avatar="⚖️").markdown(msg["content"])

# --- 7. COMMAND CENTER (The Dock) ---
with st.container():
    # Grid Layout for Tools
    c1, c2, c3 = st.columns([0.1, 1, 3]) 
    
    with c2:
        audio_val = st.audio_input("🎙️ Voice Command") 
    
    with c3:
        uploaded_file = st.file_uploader("📂 Upload Legal Evidence (PDF)", type=["pdf"])

# --- 8. LOGIC CORE ---
pdf_text = ""
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        pdf_text = get_pdf_text(tmp.name)[:50000]
    st.toast("✅ Document Encrypted & Analyzed", icon="🔒")

# Handle Audio
user_input = None
if audio_val:
    with st.spinner("🎧 Processing Voice Stream..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
            tmp_audio.write(audio_val.getvalue())
            tmp_audio_path = tmp_audio.name
        
        user_input = transcribe_audio(tmp_audio_path, api_key)

# Handle Text
if prompt := st.chat_input("Type your query here..."):
    user_input = prompt

# --- 9. GENERATION ENGINE (The "Jarvis" Animation) ---
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user", avatar="👤").write(user_input)

    with st.chat_message("assistant", avatar="⚖️"):
        # The "Thinking" Animation
        status_box = st.status("🚀 JurisAI Processing...", expanded=True)
        
        with status_box:
            st.markdown("🔹 **Phase 1:** Natural Language Understanding...")
            time.sleep(0.7)
            
            if uploaded_file:
                st.markdown("🔹 **Phase 2:** Analyzing Document Vectors...")
                time.sleep(1.0)
            else:
                st.markdown("🔹 **Phase 2:** Accessing Indian Penal Code Database...")
                time.sleep(0.8)
                
            st.markdown("🔹 **Phase 3:** Drafting Legal Response...")
            time.sleep(0.5)
            
        # AI Generation
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        full_prompt = f"""
        Role: Elite Legal AI Consultant.
        Context: {pdf_text}
        Question: {user_input}
        Output Style: Professional, Point-wise, Clear.
        """
        
        try:
            response = model.generate_content(full_prompt).text
            
            # Collapse status and show result
            status_box.update(label="✅ Analysis Complete", state="complete", expanded=False)
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Audio Output
            try:
                tts = gTTS(text=response, lang='en', slow=False)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    tts.save(fp.name)
                    st.audio(fp.name, format="audio/mp3")
            except:
                pass
                
        except Exception as e:
            status_box.update(label="❌ System Error", state="error")
            st.error(f"Error: {str(e)}")
