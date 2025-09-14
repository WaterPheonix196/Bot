from lightbulb import Loader, SlashCommand, Context, invoke

loader = Loader()

@loader.command()
class Ping(
    SlashCommand,
    name="ping",
    description="Pong!",
):
    @invoke
    async def invoke(self, ctx: Context) -> None:
        await ctx.respond("Pong!")