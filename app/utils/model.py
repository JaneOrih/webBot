import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables from .env file
load_dotenv()

# Retrieve the API key from the environment
grok_api_key = os.getenv("GROQ_API_KEY")

if grok_api_key is None:
    raise ValueError("GROQ_API_KEY is not set in the environment variables.")

# Initialize the chat model with the API key
def chat_model():
    model = init_chat_model("llama3-8b-8192", model_provider="groq", api_key=grok_api_key)
    return model

