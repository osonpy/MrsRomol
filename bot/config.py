"""
config.py — bot settings. Database and notification settings come from
api/config.py (the bot reuses the API's database and Telegram helpers).
"""
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
MINI_APP_URL: str = os.getenv("MINI_APP_URL", "http://localhost:5173").rstrip("/")
