from lightbulb import Loader, SlashCommand, Context, invoke

loader = Loader()

@loader.command(guilds=[1325571365079879774, 1407043614068183221])
class Ping(
    SlashCommand,
    name="ping",
    description="Pong!",
):
    @invoke
    async def invoke(self, ctx: Context) -> None:
        await ctx.respond("Pong!")