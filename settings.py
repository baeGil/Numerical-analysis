# settings.py
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY chưa được thiết lập trong .env")

# shared LLM
LLM = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=GEMINI_API_KEY, temperature=0)