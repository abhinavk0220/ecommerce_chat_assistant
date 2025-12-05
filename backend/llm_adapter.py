# backend/llm_adapter.py

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_llm(provider="gemini", model_name="models/gemini-2.5-flash"):
    """
    Returns a configured LLM client based on provider choice.
    Supports Gemini for production and allows future extension to Ollama.
    """
    
    if provider == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("Missing GEMINI_API_KEY in .env")
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(model_name=model_name)
        return model
    
    else:
        raise ValueError(f"Provider '{provider}' not supported yet! Only 'gemini' available.")

