from dotenv import load_dotenv
from os import getenv
from hikari import Intents

load_dotenv()

BOT_TOKEN=getenv("BOT_TOKEN")
WEBHOOK_URL=getenv("WEBHOOK_URL")

GEMINI_API_KEYS=getenv("GEMINI_API_KEYS").split(",")
BOT_INTENTS = (
    Intents.MESSAGE_CONTENT | 
    Intents.GUILD_MEMBERS | 
    Intents.GUILD_MESSAGES | 
    Intents.GUILDS
)

GITHUB_PRIVATE_KEY=getenv("GITHUB_PRIVATE_KEY")
GITHUB_APP_ID=getenv("GITHUB_APP_ID")
GITHUB_INSTALLATION_ID=getenv("GITHUB_INSTALLATION_ID")