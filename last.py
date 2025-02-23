import google.generativeai as genai
import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
import time
from PIL import Image

# Configure GenAI API key using Streamlit Secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# -------------------------------
# Predefined Credentials and Child Profiles
# -------------------------------

# Predefined credentials for mothers and child profiles
credentials = {
    "mother1": "passmother1",
    "mother2": "passmother2",
    "mother3": "passmother3",
    "mother4": "passmother4",
    "mother5": "passmother5",
}

# Child profiles with allergens and medical history
child_profiles = {
    "child1": {"password": "passchild1", "allergies": ["lactose", "peanuts"], "medical_history": ["Regular checkups, no major issues."]},
    "child2": {"password": "passchild2", "allergies": ["gluten", "eggs"], "medical_history": ["Allergic to gluten and eggs, follow a strict diet."]},
    "child3": {"password": "passchild3", "allergies": ["shellfish", "soy"], "medical_history": ["Allergic to shellfish and soy, avoid seafood and soy products."]},
    "child4": {"password": "passchild4", "allergies": ["tree nuts", "sesame"], "medical_history": ["Allergic to tree nuts and sesame, avoid nuts and seeds."]},
    "child5": {"password": "passchild5", "allergies": ["fish", "mustard"], "medical_history": ["Allergic to fish and mustard, avoid fish and condiments."]},
}

# Allergen keywords (only for allergens mentioned in child profiles)
allergen_keywords = {
    "lactose": ["milk", "cheese", "yogurt", "dairy", "butter", "cream", "whey", "casein", "lactose", "curd"],
    "peanuts": ["peanut", "peanuts", "peanut butter", "groundnut", "arachis oil", "monkey nut"],
    "gluten": ["wheat", "barley", "rye", "bread", "pasta", "cereal", "flour", "couscous", "semolina", "bulgur"],
    "eggs": ["egg", "eggs", "mayonnaise", "custard", "albumin", "ovalbumin", "lecithin", "meringue", "binder", "coagulant"],
    "shellfish": ["shrimp", "crab", "lobster", "prawn", "shellfish", "crayfish", "scallop", "oyster", "clam", "mussel"],
    "soy": ["soy", "soya", "soybean", "tofu", "tempeh", "edamame", "soy milk", "soy sauce", "soy protein", "textured vegetable protein"],
    "tree nuts": ["almond", "cashew", "walnut", "pecan", "pistachio", "hazelnut", "macadamia", "brazil nut", "chestnut", "pine nut"],
    "sesame": ["sesame", "sesame seed", "tahini", "sesame oil", "benne seed", "gingelly", "simsim"],
    "fish": ["salmon", "tuna", "cod", "halibut", "sardine", "anchovy", "trout", "mackerel", "herring", "tilapia"],
    "mustard": ["mustard", "mustard seed", "mustard oil", "mustard greens", "mustard powder", "dijon mustard"],
}

# -------------------------------
# Helper Functions
# -------------------------------

def initialize_model():
    """Initialize the Gemini model."""
    generation_config = {"temperature": 0.9}
    return genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

def build_conversation_context(messages):
    """Build a conversation context from the message history."""
    context = ""
    last_subject = None
    for msg in messages:
        if msg["role"] == "user":
            context += "User: " + msg["content"] + "\n"
            match = re.search(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", msg["content"])
            if match:
                last_subject = match.group(0)
        else:
            context += "Assistant: " + msg["content"] + "\n"
    if last_subject:
        context += f"(Context: The last discussed subject is {last_subject}.)\n"
    return context

def clean_text(text):
    """Clean text for display or TTS."""
    text = re.sub(r"[\*\_\-\[\]\(\)]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def text_to_speech(text, lang='en'):
    """Convert text to speech using gTTS."""
    clean_for_tts = clean_text(text)
    audio_bytes = io.BytesIO()
    tts = gTTS(text=clean_for_tts, lang=lang, slow=False)
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    return audio_bytes

def display_typing_effect(text, delay=0.03):
    """Display text with a typing effect."""
    clean_for_display = clean_text(text)
    text_placeholder = st.empty()
    typed_text = ""
    words = clean_for_display.split(" ")

    for word in words:
        typed_text += word + " "
        text_placeholder.markdown(
            f"<div class='assistant-message'><strong>Assistant:</strong> {typed_text}</div>",
            unsafe_allow_html=True,
        )
        time.sleep(delay)
    return typed_text

def check_allergens(image, allergies):
    """Check for allergens in the uploaded image."""
    if not allergies:
        return None

    # Generate a description of the image using the Gemini model
    model = initialize_model()
    response = model.generate_content(["Describe the contents of this image in detail.", image])
    image_description = response.candidates[0].content.parts[0].text if response.candidates else ""

    # Check for allergen-related keywords in the description
    detected_allergens = []
    for allergen in allergies:
        if allergen in allergen_keywords:
            for keyword in allergen_keywords[allergen]:
                if keyword.lower() in image_description.lower():
                    detected_allergens.append(allergen)
                    break

    if detected_allergens:
        return f"⚠️ **Warning:** This product may contain allergens your child is sensitive to: {', '.join(detected_allergens)}."
    return None

# -------------------------------
# Streamlit App Setup
# -------------------------------

# Custom CSS for animations and styling
st.set_page_config(page_title="👩‍👧 MotherSync AI – A Mother’s Voice of Comfort 🤱", layout="centered")
st.markdown("""
    <style>
        @keyframes glow {
            0% { box-shadow: 0 0 5px #ff4444; }
            50% { box-shadow: 0 0 20px #ff4444; }
            100% { box-shadow: 0 0 5px #ff4444; }
        }
        .warning-box {
            background-color: #ff4444;
            color: white;
            font-weight: bold;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 10px;
            animation: glow 1.5s infinite;
        }
        .chat-container {
            max-width: 700px;
            margin: 0 auto;
            padding: 10px;
        }
        .user-message {
            background-color: #D0E8FF;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 10px;
            text-align: left;
            color: black;
            max-width: 80%;
            animation: fadeIn 0.5s ease-in-out;
        }
        .assistant-message {
            background-color: #F0F0F0;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 10px;
            text-align: left;
            color: black;
            max-width: 80%;
            animation: fadeIn 0.5s ease-in-out;
        }
        .new-message {
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 5px;
        }
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------
# Login Page
# -------------------------------

def login_page():
    """Display the login page."""
    st.title("👩‍👧 MotherSync AI – Login")
    st.write("💖 **Welcome to MotherSync AI! Please log in to continue.** 🌷🤱✨")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in credentials and credentials[username] == password:
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.success("Logged in successfully! Redirecting...")
            time.sleep(2)
            st.rerun()
        elif username in child_profiles and child_profiles[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.success("Logged in successfully! Redirecting...")
            time.sleep(2)
            st.rerun()
        else:
            st.error("Invalid username or password.")

# -------------------------------
# Chatbot Page
# -------------------------------

def chatbot_page():
    """Display the chatbot page."""
    st.title("👩‍👧 MotherSync AI – A Mother’s Voice of Comfort 🤱")
    st.write("💖 **You are not alone—welcome to this beautiful journey of motherhood!** 🌷🤱✨")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None

    # Sidebar for image upload and child profile
    st.sidebar.header("📸 Upload Image for Analysis")
    uploaded_file = st.sidebar.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        st.session_state.uploaded_image = uploaded_file
        st.sidebar.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

        # Check for allergens if logged in as a child
        if st.session_state.current_user in child_profiles:
            allergies = child_profiles[st.session_state.current_user]["allergies"]
            image = Image.open(uploaded_file)
            allergen_warning = check_allergens(image, allergies)
            if allergen_warning:
                st.markdown(f"<div class='warning-box'>{allergen_warning}</div>", unsafe_allow_html=True)
                st.session_state.warning = allergen_warning  # Store warning in session state

    # Display previous chat history
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for message in st.session_state.messages:
        role_class = "user-message" if message["role"] == "user" else "assistant-message"
        st.markdown(f"<div class='{role_class}'><strong>{'You' if message['role']=='user' else 'Assistant'}:</strong> {message['content']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Chat Interface
    if user_input := st.chat_input("Type your message here..."):
        # Display the user's input immediately
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.markdown(f"<div class='user-message'><strong>You:</strong> {user_input}</div>", unsafe_allow_html=True)

        # Generate the assistant's response
        model = initialize_model()
        conversation_context = build_conversation_context(st.session_state.messages)
        
        # Include warning in the prompt if it exists
        if "warning" in st.session_state:
            full_prompt = f"{conversation_context}{st.session_state.warning}\nUser: {user_input}"
        else:
            full_prompt = conversation_context + user_input

        if st.session_state.uploaded_image:
            image = Image.open(st.session_state.uploaded_image)
            response = model.generate_content([full_prompt, image])
        else:
            response = model.generate_content([full_prompt])

        response_text = response.candidates[0].content.parts[0].text if response.candidates else "I couldn't generate a response."
        
        # Add danger alert if the user asks "Can I give this to my child?"
        if "can i give this to my child" in user_input.lower():
            if st.session_state.current_user in child_profiles:
                allergies = child_profiles[st.session_state.current_user]["allergies"]
                if any(allergen in response_text.lower() for allergen in allergies):
                    response_text = f"🚫 **Danger Alert:** This product contains allergens your child is sensitive to. Do not give it to your child! Side effects may include: stomach pain, diarrhea, vomiting, or allergic reactions."

        st.session_state.messages.append({"role": "assistant", "content": response_text})
        
        final_text = display_typing_effect(response_text, delay=0.03)
        
        # Determine the language for TTS
        selected_language = st.session_state.get("selected_language", "en")
        audio_bytes = text_to_speech(final_text, lang=selected_language)
        st.audio(audio_bytes, format='audio/mp3')

    # Translation Feature
    st.sidebar.header("🌍 Translate Response")
    selected_language = st.sidebar.selectbox("Choose Language", ["English", "Tamil", "Telugu", "Malayalam", "Kannada", "Hindi"])
    st.session_state.selected_language = {"English": "en", "Tamil": "ta", "Telugu": "te", "Malayalam": "ml", "Kannada": "kn", "Hindi": "hi"}[selected_language]

    if st.sidebar.button("Translate Last Response"):
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            original_text = st.session_state.messages[-1]["content"]
            lang_code = st.session_state.selected_language
            
            try:
                translated_text = GoogleTranslator(source='auto', target=lang_code).translate(original_text)
                st.sidebar.write("### Translated Response:")
                st.sidebar.write(translated_text)

                audio_bytes = text_to_speech(translated_text, lang_code)
                st.sidebar.audio(audio_bytes, format='audio/mp3')
            except Exception as e:
                st.sidebar.error(f"Translation Error: {e}")

# -------------------------------
# Main App Logic
# -------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
else:
    chatbot_page()
