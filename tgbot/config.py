import os
from dotenv import load_dotenv

# load .env variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "en").lower()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Put it into .env")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Put it into .env")
