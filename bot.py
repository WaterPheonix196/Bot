from os import getenv
from dotenv import load_dotenv
from hikari import (
    GatewayBot,
    StartingEvent,
    StartedEvent,
    StoppingEvent,
    Activity,
    ActivityType,
    Status,
    Intents,
)
from lightbulb import client_from_app
from utils.smee import SmeeClient
import extensions

load_dotenv()

bot = GatewayBot(
    token=getenv("BOT_TOKEN"),
    intents=(
        Intents.MESSAGE_CONTENT
        | Intents.GUILD_MEMBERS
        | Intents.GUILD_MESSAGES
        | Intents.GUILDS
    ),
)

smee = SmeeClient(bot, getenv("WEBHOOK_URL"), getenv("WEBHOOK_SECRET"))
client = client_from_app(bot)

@bot.listen(StartingEvent)
async def on_starting(_: StartingEvent) -> None:
    smee.start_task()
    await client.load_extensions_from_package(extensions)
    await client.sync_application_commands()
    await client.start()

@bot.listen(StartedEvent)
async def on_started(event: StartedEvent) -> None:
    count = len(
        [member async for member in event.app.rest.fetch_members(1325571365079879774)]
    )
    await bot.update_presence(
        activity=Activity(type=ActivityType.WATCHING, name=f"{count} members!"),
        status=Status.DO_NOT_DISTURB,
    )

@bot.listen(StoppingEvent)
async def on_stopping(_: StoppingEvent) -> None:
    smee.stop_task()

if __name__ == "__main__":
    bot.run()