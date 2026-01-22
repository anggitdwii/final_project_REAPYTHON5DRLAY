import streamlit as st
import requests
import json
import uuid
from datetime import datetime

# Custom CSS for Teman Wisata styling
st.markdown("""
<style>
/* Main container styling */
.main {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* Header styling */
.stTitle h1 {
    color: #2c3e50;
    text-align: center;
    font-size: 2.5rem !important;
    margin-bottom: 1rem;
}

/* Chat bubbles styling */
/* User message - right side */
.stChatMessage:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse;
    background: transparent !important;
}

.stChatMessage:has([data-testid="stChatMessageAvatarUser"]) .stMarkdown {
    background: linear-gradient(135deg, #ff7e5f 0%, #feb47b 100%);
    padding: 14px 18px 20px 18px;
    border-radius: 20px 20px 4px 20px;
    margin-left: auto;
    margin-right: 8px;
    color: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Assistant message - left side */
.stChatMessage:has([data-testid="stChatMessageAvatarAssistant"]) {
    background: transparent !important;
}

.stChatMessage:has([data-testid="stChatMessageAvatarAssistant"]) .stMarkdown {
    background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%);
    padding: 16px 20px 20px 20px;
    border-radius: 20px 20px 20px 4px;
    margin-left: 8px;
    color: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Ensure text is visible */
.stChatMessage p, .stChatMessage span, .stChatMessage li {
    color: white !important;
    font-size: 1rem;
    line-height: 1.5;
}

/* Add spacing between messages */
.stChatMessage {
    margin-bottom: 16px;
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Style the chat input */
[data-testid="stChatInput"] textarea {
    border-radius: 25px;
    border: 2px solid #4b6cb7;
    padding: 15px;
    font-size: 1rem;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2c3e50 0%, #1a2530 100%);
}

[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: white !important;
}

/* Card styling for info */
.info-card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    margin: 10px 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border-left: 5px solid #ff7e5f;
}

.info-card h4 {
    color: #2c3e50;
    margin-bottom: 10px;
}

/* Button styling */
.stButton button {
    background: linear-gradient(135deg, #ff7e5f 0%, #feb47b 100%);
    color: white;
    border: none;
    border-radius: 25px;
    padding: 10px 25px;
    font-weight: bold;
    transition: transform 0.2s;
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(255,126,95,0.3);
}
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---

def load_key():
    try:
        with open("api_key.txt", "r") as f:
            return f.read().strip()
    except:
        return ""

def save_key(key):
    with open("api_key.txt", "w") as f:
        f.write(key)

def load_history():
    try:
        with open("chat_history.json", "r") as f:
            return json.load(f)
    except:
        return {"conversations": [], "current_chat_id": None}

def save_history(history):
    with open("chat_history.json", "w") as f:
        json.dump(history, f)

def init_chat():
    """Create a new chat session"""
    new_chat_id = str(uuid.uuid4())
    pk = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_chat = {
        "id": new_chat_id,
        "title": "Percakapan Baru",
        "timestamp": pk,
        "messages": [
            {"role": "assistant", "content": "Halo! Saya Teman Wisata.\n\nSaya siap menemani petualanganmu di Indonesia. Mau pergi ke mana hari ini?"}
        ]
    }
    return new_chat

def get_current_chat():
    chat_id = st.session_state.history["current_chat_id"]
    for chat in st.session_state.history["conversations"]:
        if chat["id"] == chat_id:
            return chat
    # Fallback if id not found (e.g. corruption)
    if st.session_state.history["conversations"]:
        return st.session_state.history["conversations"][0]
    return None

def update_current_chat_messages(new_msg):
    chat = get_current_chat()
    if chat:
        chat["messages"].append(new_msg)
        
        # Update title if it's the first user message
        if len(chat["messages"]) == 2 and new_msg["role"] == "user":
            # Truncate title
            title = new_msg["content"]
            if len(title) > 30:
                title = title[:30] + "..."
            chat["title"] = title
            
        save_history(st.session_state.history)

def delete_chat(chat_id):
    st.session_state.history["conversations"] = [c for c in st.session_state.history["conversations"] if c["id"] != chat_id]
    
    # If we deleted the current chat, switch to another
    if st.session_state.history["current_chat_id"] == chat_id:
        if st.session_state.history["conversations"]:
            st.session_state.history["current_chat_id"] = st.session_state.history["conversations"][0]["id"]
        else:
            # Create new if all deleted
            new_chat = init_chat()
            st.session_state.history["conversations"].append(new_chat)
            st.session_state.history["current_chat_id"] = new_chat["id"]
            
    save_history(st.session_state.history)
    st.rerun()

def get_ai_response(messages_payload, model, api_key):
    """Get response from AI with LocalWisdomBot system prompt"""
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            data=json.dumps({
                "model": model,
                "messages": messages_payload,
                "max_tokens": 1500,
                "temperature": 0.8,
                "presence_penalty": 0.3,
                "frequency_penalty": 0.2
            })
        )
        if response.status_code != 200:
            st.error(f"Error {response.status_code}: {response.text}")
            return None
        answer = response.json()["choices"][0]["message"]["content"]
        return answer
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def get_localwisdom_response(user_input, conversation_history, model, api_key):
    """Generate response with LocalWisdomBot context"""
    
    # System prompt for Teman Wisata
    system_prompt = """Kamu adalah Teman Wisata, asisten perjalanan yang ramah, seru, dan sangat tahu tentang wisata serta budaya Indonesia. 
    Tugasmu adalah:
    1. Berikan informasi tentang budaya, tradisi, kuliner khas daerah di Indonesia
    2. Rekomendasikan tempat wisata kuliner dan atraksi budaya
    3. Bagikan cerita rakyat atau sejarah lokal yang menarik
    4. Berikan tips untuk pengunjung (etika, pakaian, waktu terbaik berkunjung)
    5. Jelaskan makna di balik tradisi atau makanan khas
    
    **Aturan respons:**
    - Selalu awali dengan salam ramah dalam bahasa Indonesia
    - Gunakan bahasa yang santai dan informatif
    - Struktur jawaban dengan: pengantar singkat, konten utama, tips tambahan
    - Jika tidak tahu, jangan mengarang - minta maaf dan arahkan ke topik terkait
    - Sertakan 1-2 fakta unik yang jarang diketahui
    
    Format jawaban:
    [Judul/Topik]
    
    [Isi penjelasan dengan poin-poin atau paragraf singkat]
    
    Tips & Info:
    • [Tips pertama]
    • [Tips kedua]
    • [Fakta unik]
    
    [Pertanyaan pengantar untuk melanjutkan percakapan]
    
    Contoh topik yang bisa dibahas:
    - Rendang Padang dan filosofinya
    - Upacara Ngaben di Bali
    - Wayang Kulit Jawa
    - Rumah Adat Toraja
    - Batik dan makna motifnya
    - Kue tradisional daerah
    - Festival budaya lokal
    - Alat musik tradisional
    - Mitos dan legenda daerah"""
    
    # Prepare messages with system prompt
    messages_for_api = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add conversation history
    for msg in conversation_history[-6:]:  # Keep last 6 messages for context
        messages_for_api.append(msg)
    
    # Add current user input
    messages_for_api.append({"role": "user", "content": user_input})
    
    return get_ai_response(messages_for_api, model, api_key)

# --- Initialization ---

# Initialize session state for Chat History
if "history" not in st.session_state:
    st.session_state.history = load_history()

# Ensure at least one chat exists
if not st.session_state.history["conversations"]:
    new_chat = init_chat()
    st.session_state.history["conversations"].append(new_chat)
    st.session_state.history["current_chat_id"] = new_chat["id"]
    save_history(st.session_state.history)

if "region_selected" not in st.session_state:
    st.session_state.region_selected = None

# --- UI Layout ---

st.title("Teman Wisata 🌏")
st.caption("Sahabat Perjalanan & Budaya Indonesia")

# Sidebar for configuration
with st.sidebar:
    st.header("Pengaturan Bot")
    
    # Load existing key
    saved_key = load_key()
    
    api_key = st.text_input("API Key OpenRouter", 
                          value=saved_key,
                          type="password", 
                          placeholder="sk-or-v1-...",
                          help="Dapatkan di openrouter.ai/keys")
    
    # Save if changed
    if api_key and api_key != saved_key:
        save_key(api_key)
        st.toast("API Key tersimpan otomatis!")
    
    api_key_status = "Tidak Aktif" if not api_key else "Aktif"
    st.markdown(f"**Status API:** {api_key_status}")
    
    st.divider()
    
    # Chat Management
    st.subheader("Riwayat Chat")
    
    if st.button("➕ Chat Baru", use_container_width=True):
        new_chat = init_chat()
        st.session_state.history["conversations"].insert(0, new_chat) # Add to top
        st.session_state.history["current_chat_id"] = new_chat["id"]
        save_history(st.session_state.history)
        st.session_state.region_selected = None # Reset context
        st.rerun()
        
    st.markdown("---")
    
    # List conversations
    # Sort by timestamp desc (optional, currently relying on insert order)
    for chat in st.session_state.history["conversations"]:
        col_btn, col_del = st.columns([0.8, 0.2])
        
        # Determine if active
        is_active = chat["id"] == st.session_state.history["current_chat_id"]
        # Simple Title
        label = f"{'📂' if is_active else '📄'} {chat['title']}"
        
        with col_btn:
            if st.button(label, key=f"sel_{chat['id']}", use_container_width=True):
                st.session_state.history["current_chat_id"] = chat["id"]
                st.session_state.region_selected = None 
                st.rerun()
                
        with col_del:
            if st.button("🗑️", key=f"del_{chat['id']}", help="Hapus chat"):
                delete_chat(chat['id'])

    st.divider()
    
    st.subheader("Pilih Daerah Fokus")
    
    # Region selection buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Bali", use_container_width=True):
            st.session_state.region_selected = "Bali"
    with col2:
        if st.button("Jawa", use_container_width=True):
            st.session_state.region_selected = "Jawa"
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Sumatra", use_container_width=True):
            st.session_state.region_selected = "Sumatra"
    with col4:
        if st.button("Sulawesi", use_container_width=True):
            st.session_state.region_selected = "Sulawesi"
    
    if st.session_state.region_selected:
        st.success(f"Fokus daerah: **{st.session_state.region_selected}**")
        if st.button("Reset Fokus", use_container_width=True):
            st.session_state.region_selected = None
            st.rerun()
    
    st.divider()
    
    selected_model = "meta-llama/llama-3.3-70b-instruct:free"



# Logic Phase

# Get Current Chat
current_chat = get_current_chat()
if current_chat:
    messages = current_chat["messages"]
else:
    messages = [] # Should not happen

# Main chat interface - Quick Question Handler
if "quick_question" in st.session_state:
    if not api_key:
         st.toast("Masukkan API Key terlebih dahulu di sidebar kiri!", icon=None)
         st.session_state.pop("quick_question")
    else:
        # Auto-insert quick question
        user_input = st.session_state.pop("quick_question")
        
        # Append to CURRENT chat
        new_msg = {"role": "user", "content": user_input}
        update_current_chat_messages(new_msg)
        st.rerun()

# Display chat history for CURRENT chat
for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Suggestion Chips for New Chat
if len(messages) == 1:
    st.markdown("### 💡 Ide Pertanyaan")
    example_questions = [
        "Ceritakan tentang Upacara Ngaben di Bali",
        "Apa makanan khas Yogyakarta?",
        "Bagaimana sejarah Batik?",
        "Rekomendasi tempat wisata budaya di Jawa Barat",
        "Apa makna filosofi Rendang?"
    ]
    
    # Create a grid layout for chips
    cols = st.columns(2)
    for i, q in enumerate(example_questions):
        if cols[i % 2].button(q, key=f"chip_{i}", use_container_width=True):
            st.session_state.quick_question = q
            st.rerun()

# Chat input
if prompt := st.chat_input(f"Tanya tentang budaya {st.session_state.region_selected or 'Indonesia'}..."):
    # Check API Key here
    if not api_key:
        st.warning("Silakan masukkan API Key OpenRouter di sidebar kiri untuk memulai percakapan.")
    else:
        # Append User Message to History
        new_msg = {"role": "user", "content": prompt}
        update_current_chat_messages(new_msg)
        st.rerun()

# Logic to generate AI response (Separated from input to handle buttons too)
# If last message is USER, then Assistant needs to reply
if messages and messages[-1]["role"] == "user":
    if not api_key:
        # Just in case we got here without key (should be handled above but good for safety)
        pass 
    else:
        # Get last user prompt
        last_user_msg = messages[-1]["content"]
        
        # Add region context if selected
        model_prompt = last_user_msg
        if st.session_state.region_selected:
            model_prompt = f"[Fokus daerah: {st.session_state.region_selected}] {last_user_msg}"
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Mencari kebijaksanaan lokal..."):
                ai_response = get_localwisdom_response(
                    model_prompt, 
                    messages, # Pass full history
                    selected_model, 
                    api_key
                )
                if ai_response:
                    st.markdown(ai_response)
                    # Append Assistant Message to History
                    asst_msg = {"role": "assistant", "content": ai_response}
                    update_current_chat_messages(asst_msg)
                else:
                    st.error("Maaf, terjadi kesalahan. Cek API Key atau koneksi Anda.")

# Footer
st.divider()
st.caption("""
**Teman Wisata** v1.0 • Menjelajah Indonesia lebih mudah dengan AI • 
Tips: Gunakan model gratis untuk testing, dan model berbayar untuk respons lebih akurat
""")