import streamlit as st
import google.generativeai as genai
import pypdf
import os
import tempfile
from gtts import gTTS

# --- PAGE CONFIGURATION (Must be first) ---
st.set_page_config(
    page_title="JurisAI Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (The "Make it Pretty" Part) ---
st.markdown("""
    <style>
    /* 1. Main Background - Dark Professional Blue/Black */
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #161b22 100%);
    }

    /* 2. Sidebar - Glassmorphism Effect */
    [data-testid="stSidebar"] {
        background-color: rgba(22, 27, 34, 0.8);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* 3. Title Typography - Gradient Glow */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #4F8BF9, #9b59b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
        padding-bottom: 10px;
        text-shadow: 0 0 30px rgba(79, 139, 249, 0.3);
    }
    .sub-title {
        font-size: 1.2rem;
        color: #a0aab9;
        text-align: center;
        margin-bottom: 30px;
        font-weight: 300;
        letter-spacing: 1px;
    }

    /* 4. Chat Input - Fixed at Bottom */
    .stChatInput {
        position: fixed;
        bottom: 20px;
        z-index: 100;
    }
    
    /* 5. Custom Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #4F8BF9 0%, #3a6cc2 100%);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(79, 139, 249, 0.4);
    }
    
    /* 6. Success/Info Messages */
    .stSuccess, .stInfo {
        background-color: rgba(28, 33, 40, 0.6) !important;
        border: 1px solid rgba(79, 139, 249, 0.2);
        color: #e6edf3 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_pdf_text(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return ""

# --- SIDEBAR DESIGN ---
with st.sidebar:
    st.markdown("<div style='text-align: center; font-size: 4rem;'>⚖️</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white;'>JurisAI</h2>", unsafe_allow_html=True)
    
        # --- API KEY AUTOMATION ---
    try:
        # This pulls the key from the "Secrets" you saved on Streamlit Cloud
        api_key = st.secrets["GEMINI_API_KEY"]
        st.sidebar.success("🔐 Security: Verified")
    except FileNotFoundError:
        # This handles the error if you run it locally without a secrets.toml file
        st.sidebar.warning("⚠️ API Key not found in Secrets")
        api_key = st.sidebar.text_input("Enter API Key manually:", type="password")


    st.markdown("### ⚙️ Preferences")
    language = st.selectbox("💬 Answer Language", ["English", "Hindi", "Kannada"])
    enable_audio = st.toggle("🔊 Read Aloud", value=False)
    
    st.markdown("### 📂 Evidence/Case File")
    uploaded_file = st.file_uploader("Upload Legal PDF", type="pdf", label_visibility="collapsed")
    
    # Status Indicator
    pdf_text = ""
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            pdf_text = get_pdf_text(tmp.name)[:50000]
        st.success(f"📄 Loaded: {uploaded_file.name}")
    elif os.path.exists("law_data.pdf"):
        pdf_text = get_pdf_text("law_data.pdf")[:50000]
        st.info("📚 Using Default Knowledge Base")
    else:
        st.warning("⚠️ No documents found. Using General AI.")

# --- MAIN UI LAYOUT ---
st.markdown('<div class="main-title">JurisAI Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Your Advanced AI Legal Consultant • VTU Project 2026</div>', unsafe_allow_html=True)
st.markdown("---")

# --- BACKEND LOGIC ---
def get_response(history, query, context, api_key, lang):
    if not api_key: return "⚠️ **System Alert:** Please enter your API Key in the sidebar to proceed."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        Role: Expert Legal Consultant (JurisAI).
        Task: Answer the user question in {lang}.
        
        Guidelines:
        1. Base your answer on the PDF CONTEXT provided below.
        2. If the answer is missing from the PDF, use your GENERAL LEGAL KNOWLEDGE.
        3. Structure your answer with clear headings and bullet points.
        4. Be professional, empathetic, and precise.

        PDF CONTEXT:
        {context}

        CONVERSATION HISTORY:
        {history}

        USER QUESTION:
        {query}
        """
        
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"❌ **Error:** {str(e)}"

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am JurisAI. I can analyze case files, explain laws, or draft legal notices. How can I assist you today?"}]

# Display Chat History with Avatars
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user", avatar="🧑‍⚖️").write(msg["content"])
    else:
        st.chat_message("assistant", avatar="⚖️").markdown(msg["content"])

# Handle User Input
if prompt := st.chat_input(f"Ask a question in {language}..."):
    # 1. Show User Message
    st.chat_message("user", avatar="🧑‍⚖️").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Generate Response
    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("🔍 Analyzing legal statutes..."):
            history_text = str(st.session_state.messages[-4:])
            response = get_response(history_text, prompt, pdf_text, api_key, language)
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # 3. Audio Playback
            if enable_audio:
                try:
                    lang_code = {"English": "en", "Hindi": "hi", "Kannada": "kn"}.get(language, "en")
                    tts = gTTS(text=response, lang=lang_code, slow=False)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        tts.save(fp.name)
                        st.audio(fp.name, format="audio/mp3")
                except:
                    pass