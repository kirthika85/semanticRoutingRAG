import streamlit as st
from sentence_transformers import SentenceTransformer, util
import google.generativeai as genai
import os

# Configure Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

intents = { 
    "recommendations": [
        "Can you recommend a good beach destination for a family vacation?",
        "I'm looking for suggestions on romantic getaways for couples.",
        "What are some popular outdoor adventure vacation ideas?",
        "Do you have any recommendations for budget-friendly vacations?",
        "I'd like to plan a trip for my upcoming anniversary. Can you suggest some options?",
        "Can you recommend a family-friendly resort with activities for kids?",
        "I'm interested in a cultural vacation. What cities would you recommend visiting?",
        "Do you have any suggestions for a relaxing spa vacation?",
        "I'm looking for vacation ideas that combine hiking and sightseeing.",
        "Can you recommend an all-inclusive resort with good reviews?"
    ],
    "how-to": [
        "How do I book a vacation package?",
        "What is the process for getting a travel visa?",
        "How can I find the best flight deals?",
        "How do I cancel my reservation?",
        "What steps should I take to plan a road trip?"
    ],
    "locality": [
        "What are some attractions near Paris?",
        "Are there good restaurants in Rome?",
        "What's the weather like in Bali?",
        "Tell me about local events in Tokyo.",
        "Are there any hiking trails near Denver?"
    ]
}

# Load models
@st.cache_resource
def load_models():
    return {
        "embedding": SentenceTransformer('all-MiniLM-L6-v2'),
        "gemini": genai.GenerativeModel('gemini-1.5-flash')
    }

models = load_models()

# Precompute embeddings
intent_embeddings = {}
for intent, examples in intents.items():
    intent_embeddings[intent] = models["embedding"].encode(examples)

# Streamlit UI
st.title("Semantic Router RAG POC")

user_query = st.text_input("Ask your travel question:")
response_container = st.empty()

if user_query:
    # Semantic routing
    query_embed = models["embedding"].encode([user_query])[0]
    best_intent = "default"
    best_score = 0.7  # Threshold
    
    for intent, embeds in intent_embeddings.items():
        scores = util.cos_sim(query_embed, embeds)
        if scores.max() > best_score:
            best_score = scores.max()
            best_intent = intent

    # Generate Gemini response based on intent
    prompt = f"""As a travel assistant, respond to this query in 2-3 sentences.
    Query: {user_query}
    Context: The user is asking about {best_intent.replace('_', ' ')}.
    Respond helpfully and concisely:"""
    
    try:
        response = models["gemini"].generate_content(prompt)
        response_container.markdown(f"""
        **Detected Intent**: `{best_intent}`  
        **Response**: {response.text}
        """)
    except Exception as e:
        st.error(f"Gemini API error: {str(e)}")
