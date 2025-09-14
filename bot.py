from hikari import GatewayBot, StartingEvent, StartedEvent, Activity, ActivityType, Status
from asyncio import create_task
from lightbulb import GatewayEnabledClient, client_from_app

from constants import BOT_TOKEN, BOT_INTENTS, WEBHOOK_URL
from utils.smee import SmeeClient
import extensions

bot = GatewayBot(token=BOT_TOKEN, intents=BOT_INTENTS)
smee = SmeeClient(bot=bot, url=WEBHOOK_URL)
client = client_from_app(bot)

def _on_start(
    app: GatewayBot, client: GatewayEnabledClient
):
    async def on_starting(_: StartingEvent):
        await client.load_extensions_from_package(extensions)
        await client.sync_application_commands()
        await client.start()

    return on_starting


bot.subscribe(StartingEvent, _on_start(bot, client))

@bot.listen()
async def on_starting(event: StartedEvent) -> None:
    count = len([member async for member in bot.rest.fetch_members(1325571365079879774)])

    await bot.update_presence(
        activity=Activity(type=ActivityType.WATCHING, name=f"{count} members!"),
        status=Status.DO_NOT_DISTURB
    )

    create_task(smee.start())

if __name__ == "__main__":
    bot.run()