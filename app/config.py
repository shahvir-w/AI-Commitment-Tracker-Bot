import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_BOT_USER_ID = os.getenv("SLACK_BOT_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_PASSWORD = os.getenv("DB_PASS")
