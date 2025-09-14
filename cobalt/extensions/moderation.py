from lightbulb import SlashCommand, Loader, Context, invoke, integer
from hikari import Permissions, GuildTextChannel, Embed, MessageFlag

loader = Loader()

@loader.command()
class Clear(
    SlashCommand,
    name="clear",
    description="Clear a set amount of messages.",
    default_member_permissions=Permissions.MANAGE_MESSAGES
):
    amount = integer("amount", "Amount of messages to clear (1-100).")
    
    @invoke
    async def invoke(self, ctx: Context) -> None:
        succeeded = True
        amount = ctx.options[0].value

        if (amount < 2 or amount > 100 or not amount.is_integer):
            succeeded = False

        try:
            messages = ctx.client.app.rest.fetch_messages(ctx.channel_id).limit(amount)
            await ctx.client.app.rest.delete_messages(ctx.channel_id, messages)
        except:
            succeeded = False

        embed = Embed(
            description=(f"Cleared {amount} messages!" if succeeded else "Failed to clear messages."),
            color=(0x16C47F if succeeded else 0xF93827)
        )

        await ctx.respond(embed=embed, flags=MessageFlag.EPHEMERAL)


@loader.command()
class Purge(
    SlashCommand,
    name="purge",
    description="Purge a channel by deleting it then recreate it.",
    default_member_permissions=Permissions.MANAGE_CHANNELS
):
    @invoke
    async def invoke(self, ctx: Context) -> None:
        succeeded = True

        try:
            channel = await ctx.client.app.rest.fetch_channel(ctx.channel_id)
            
            if not isinstance(channel, GuildTextChannel):
                raise ValueError()
            
            new_channel = await ctx.client.app.rest.create_guild_text_channel(
                guild=ctx.guild_id,
                name=channel.name,
                topic=channel.topic,
                position=channel.position,
                category=channel.parent_id,
                permission_overwrites=channel.permission_overwrites.values(),
                nsfw=channel.is_nsfw,
                rate_limit_per_user=channel.rate_limit_per_user
            )

            await ctx.client.app.rest.delete_channel(ctx.channel_id)
        except:
            succeeded = False

        embed = Embed(
            description=("Successfully purged the channel!" if succeeded else "Failed to purge channel."),
            color=(0x16C47F if succeeded else 0xF93827)
        )

        if succeeded:
            await new_channel.send(embed=embed)
        else:
            await ctx.respond(embed=embed, flags=MessageFlag.EPHEMERAL)