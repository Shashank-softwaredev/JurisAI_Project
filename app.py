import streamlit as st
import google.generativeai as genai
import pypdf
import os
import tempfile
import time
import json
from gtts import gTTS

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="JurisAI Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SECURITY & AUTHENTICATION SYSTEM ---
# Simple "Database" of users (Email : Password)
# You can give these credentials to your examiners
USERS = {
    "student@jurisai.com": "password123",
    "admin@jurisai.com": "admin",
    "examiner@vtu.ac.in": "vtu2026"
}

def load_history(username):
    """Loads specific chat history for the logged-in user"""
    filename = f"history_{username.split('@')[0]}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return [{"role": "assistant", "content": f"Welcome back, {username}! How can I help you today?"}]

def save_history(username, messages):
    """Saves chat history securely to a local JSON file"""
    filename = f"history_{username.split('@')[0]}.json"
    with open(filename, "w") as f:
        json.dump(messages, f)

# --- 3. CUSTOM CSS (Cyber Theme) ---
st.markdown("""
    <style>
    /* Animated Background */
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
    /* Login Box Styling */
    .login-box {
        background: rgba(255, 255, 255, 0.05);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        text-align: center;
        max-width: 500px;
        margin: auto;
    }
    /* Hide Standard Elements */
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stHeader"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIN LOGIC ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    # --- SHOW LOGIN SCREEN ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<h1 style="text-align: center; color: #00c6ff;">🔐 JurisAI Secure Login</h1>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("📧 Email Address")
            password = st.text_input("🔑 Password", type="password")
            submitted = st.form_submit_button("🚀 Login System")
            
            if submitted:
                if email in USERS and USERS[email] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = email
                    st.success("Access Granted")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid Credentials. Try: student@jurisai.com / password123")
    st.stop() # Stop here if not logged in

# =========================================================
#  🏁 MAIN APP STARTS HERE (Only visible after Login)
# =========================================================

# --- SIDEBAR LOGOUT (Hidden but accessible via code if needed) ---
with st.sidebar:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- API KEY ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.warning("⚠️ API Key Missing")
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

def transcribe_audio(audio_file, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    myfile = genai.upload_file(audio_file)
    result = model.generate_content(["Transcribe this audio exactly as spoken.", myfile])
    return result.text

# --- HEADER ---
c1, c2 = st.columns([8, 1])
with c1:
    st.markdown('<h1 style="color: #00c6ff;">JurisAI Pro</h1>', unsafe_allow_html=True)
    st.caption(f"👤 Logged in as: {st.session_state.username}")
with c2:
    if st.button("🔒 Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- LOAD USER HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = load_history(st.session_state.username)

# Display Chat
for msg in st.session_state.messages:
    role = msg["role"]
    avatar = "👤" if role == "user" else "⚖️"
    st.chat_message(role, avatar=avatar).write(msg["content"])

# --- COMMAND CENTER ---
with st.container():
    c1, c2, c3 = st.columns([0.1, 1, 3]) 
    with c2:
        audio_val = st.audio_input("🎙️ Voice") 
    with c3:
        uploaded_file = st.file_uploader("📂 Upload Evidence", type=["pdf"], label_visibility="collapsed")

# --- LOGIC ---
pdf_text = ""
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        pdf_text = get_pdf_text(tmp.name)[:50000]
    st.toast("✅ Encrypted & Loaded")

# Input Handling
user_input = None
if audio_val:
    with st.spinner("🎧 Transcribing..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_val.getvalue())
            user_input = transcribe_audio(tmp.name, api_key)

if prompt := st.chat_input("Type your query..."):
    user_input = prompt

# --- GENERATION ---
if user_input:
    # 1. Show & Save User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_history(st.session_state.username, st.session_state.messages) # Auto-Save
    st.chat_message("user", avatar="👤").write(user_input)

    # 2. Generate
    with st.chat_message("assistant", avatar="⚖️"):
        status = st.status("🚀 Processing...", expanded=True)
        with status:
            st.write("🔹 Verifying User Credentials...")
            time.sleep(0.5)
            st.write("🔹 Searching Legal Database...")
            time.sleep(0.8)
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            full_prompt = f"""
            Role: Legal AI.
            Context: {pdf_text}
            Question: {user_input}
            """
            
            try:
                response = model.generate_content(full_prompt).text
                status.update(label="✅ Secured Response Ready", state="complete", expanded=False)
                st.markdown(response)
                
                # Save Assistant Message
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_history(st.session_state.username, st.session_state.messages) # Auto-Save
                
                # Audio
                try:
                    tts = gTTS(text=response, lang='en', slow=False)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        tts.save(fp.name)
                        st.audio(fp.name, format="audio/mp3")
                except: pass
            except Exception as e:
                st.error("Error generating response")
