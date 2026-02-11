import streamlit as st
import google.generativeai as genai
import pypdf
import os
import tempfile
import time
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
    /* We position this just above the chat input */
    [data-testid="stBottom"] > div {
        padding-bottom: 20px;
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
    # Fallback for local testing if secrets.toml is missing
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.warning("⚠️ API Key missing. Please set it in secrets.toml")
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
    """Uses Gemini to transcribe audio to text"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    # Upload the audio file to Gemini
    myfile = genai.upload_file(audio_file)
    result = model.generate_content(["Transcribe this audio exactly as spoken in English.", myfile])
    return result.text

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
with st.container():
    c1, c2, c3 = st.columns([0.1, 2, 2]) # Spacer, Audio, File
    
    with c2:
        audio_val = st.audio_input("🎙️ Record Voice") 
    
    with c3:
        uploaded_file = st.file_uploader("📎 Attach Evidence", type=["pdf"], label_visibility="collapsed")

# --- PROCESSING INPUTS ---
pdf_text = ""
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        pdf_text = get_pdf_text(tmp.name)[:50000]
    st.toast("✅ File Attached to Context")

# --- HANDLING AUDIO INPUT (Auto-Trigger) ---
user_input = None
if audio_val:
    with st.spinner("🎧 Transcribing Audio..."):
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
            tmp_audio.write(audio_val.getvalue())
            tmp_audio_path = tmp_audio.name
        
        # Transcribe
        transcribed_text = transcribe_audio(tmp_audio_path, api_key)
        user_input = transcribed_text
        st.toast("✅ Audio Transcribed")

# --- CHAT INPUT (Text Override) ---
if prompt := st.chat_input("Type your legal question here..."):
    user_input = prompt

# --- MAIN GENERATION LOGIC ---
if user_input:
    # 1. Add User Message to History
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user", avatar="🧑‍⚖️").write(user_input)

    # 2. JARVIS ANIMATION & GENERATION
    with st.chat_message("assistant", avatar="⚖️"):
        
        # The Expanding Status Box (The "Working" Animation)
        with st.status("🚀 JurisAI is processing...", expanded=True) as status:
            
            # Step 1: Context
            if uploaded_file:
                st.write("📄 Scanning uploaded legal documents...")
                time.sleep(1.2) # Animation delay
            else:
                st.write("🌍 Accessing General Indian Penal Code (IPC)...")
                time.sleep(0.8)
            
            # Step 2: Reasoning
            st.write("⚖️ Analyzing legal precedents...")
            time.sleep(0.8)
            
            # Step 3: Drafting
            st.write("✍️ Drafting professional response...")
            
            # 3. Call AI
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            full_prompt = f"""
            Act as an expert Legal Consultant.
            Context from PDF: {pdf_text}
            Question: {user_input}
            Format: Use bullet points and clear headings.
            """
            
            try:
                response = model.generate_content(full_prompt).text
                
                # Close the status box
                status.update(label="✅ Analysis Complete", state="complete", expanded=False)
                
                # Show Result
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # 4. Audio Playback (Auto-Read)
                try:
                    tts = gTTS(text=response, lang='en', slow=False)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        tts.save(fp.name)
                        st.audio(fp.name, format="audio/mp3", start_time=0)
                except:
                    pass
                    
            except Exception as e:
                status.update(label="❌ Error", state="error")
                st.error(f"Error: {str(e)}")
