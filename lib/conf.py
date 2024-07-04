import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_APIKEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_APIKEY = os.environ.get("ANTHROPIC_API_KEY")
VOICEVOX_APIKEY = os.environ.get("VOICEVOX_API_KEY")
GEMINI_APIKEY = os.environ.get("GEMINI_API_KEY")
