from lightbulb import SlashCommand, Loader, Context, invoke, integer, string, boolean
from hikari import Permissions, GuildTextChannel, Embed, MessageFlag
import re

loader = Loader()

lockedChannels = []

@loader.command(guilds=[1325571365079879774, 1407043614068183221])
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


@loader.command(guilds=[1325571365079879774, 1407043614068183221])
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

@loader.command(guilds=[1325571365079879774, 1407043614068183221])
class Lock(
    SlashCommand,
    name="lock",
    description="Toggle lock on the channel (deny or restore send perms).",
    default_member_permissions=Permissions.MANAGE_CHANNELS,
):
    @invoke
    async def invoke(self, ctx: Context) -> None:
        succeeded = True
        description = ""

        try:
            channel = await ctx.client.app.rest.fetch_channel(ctx.channel_id)
            if not isinstance(channel, GuildTextChannel):
                raise ValueError("Not a text channel")

            overwrites = list(channel.permission_overwrites.values())

            if ctx.channel_id in lockedChannels:
                lockedChannels.remove(ctx.channel_id)
                for ow in overwrites:
                    if ow.type.name == "ROLE":
                        ow.allow |= Permissions.SEND_MESSAGES
                        ow.deny &= ~Permissions.SEND_MESSAGES
                description = "Channel unlocked!"
            else:
                lockedChannels.append(ctx.channel_id)
                for ow in overwrites:
                    if ow.type.name == "ROLE":
                        if not Permissions.ADMINISTRATOR in ow.allow:
                            ow.deny |= Permissions.SEND_MESSAGES
                            ow.allow &= ~Permissions.SEND_MESSAGES
                description = "Channel locked!"

            await ctx.client.app.rest.edit_channel(
                ctx.channel_id,
                permission_overwrites=overwrites,
            )

        except Exception as e:
            print(f"Lock failed: {e}")
            succeeded = False
            description = "Failed to lock/unlock channel."

        embed = Embed(
            description=description,
            color=(0x16C47F if succeeded else 0xF93827),
        )
        await ctx.respond(embed=embed, flags=MessageFlag.EPHEMERAL)

@loader.command(guilds=[1325571365079879774, 1407043614068183221])
class Ban(
    SlashCommand,
    name="ban",
    description="Ban a user from the server.",
    default_member_permissions=Permissions.BAN_MEMBERS | Permissions.ADMINISTRATOR,
):
    target = string("user", "The user to ban.")
    reason = string("reason", "The reason for the ban.", default="No reason provided.")
    delete_recent = boolean("delete_recent", "Delete recent messages from the user?", default=False)
    dm_recipient = boolean("dm_recipient", "DM the recipient about their ban?", default=True)

    @invoke
    async def invoke(self, ctx: Context) -> None:
        succeeded = True
        try:
            options = {opt.name: opt.value for opt in ctx.options}
            mention = options["user"]

            user = await resolve_user(ctx.client, options["user"])

            reason = options.get("reason", "No reason provided")
            delete_recent = options.get("delete_recent", False)
            dm_recipient = options.get("dm_recipient", True)

            if dm_recipient:
                try:
                    await send_dm(
                        ctx,
                        user,
                        "Banned from Cobalt",
                        f"You have been banned Cobalt.\nReason: {reason}",
                    )
                except Exception as e:
                    print(f"Could not DM user: {e}")

            await ctx.client.app.rest.ban_user(
                ctx.guild_id,
                user.id,
                delete_message_seconds=3600 if delete_recent else 0,
                reason=reason,
            )

            description = f"Banned <@{user.id}> (ID: {user.id})\nReason: {reason}"
        except Exception as e:
            succeeded = False
            description = f"Failed to ban user. {e}"

        embed = Embed(
            description=description,
            color=(0x16C47F if succeeded else 0xF93827),
        )
        await ctx.respond(embed=embed, flags=MessageFlag.EPHEMERAL)

@loader.command(guilds=[1325571365079879774, 1407043614068183221])
class Unban(
    SlashCommand,
    name="unban",
    description="Unban a user from the server.",
    default_member_permissions=Permissions.BAN_MEMBERS | Permissions.ADMINISTRATOR,
):
    target = string("user", "The user to unban.")

    @invoke
    async def invoke(self, ctx: Context) -> None:
        succeeded = True
        try:
            options = {opt.name: opt.value for opt in ctx.options}
            mention = options["user"]

            user = await resolve_user(ctx.client, options["user"])

            await ctx.client.app.rest.unban_user(
                ctx.guild_id,
                user.id,
            )

            description = f"Unbanned <@{user.id}> (ID: {user.id})"
        except Exception as e:
            succeeded = False
            description = f"Failed to unban user. {e}"

        embed = Embed(
            description=description,
            color=(0x16C47F if succeeded else 0xF93827),
        )
        await ctx.respond(embed=embed, flags=MessageFlag.EPHEMERAL)

@loader.command(guilds=[1325571365079879774, 1407043614068183221])
class Kick(
    SlashCommand,
    name="kick",
    description="Kick a user from the server.",
    default_member_permissions=Permissions.KICK_MEMBERS | Permissions.ADMINISTRATOR,
):
    target = string("user", "The user to kick.")
    reason = string("reason", "The reason for the kick.", default="No reason provided.")
    dm_recipient = boolean("dm_recipient", "DM the recipient about their kick?", default=True)

    @invoke
    async def invoke(self, ctx: Context) -> None:
        succeeded = True
        try:
            options = {opt.name: opt.value for opt in ctx.options}
            mention = options["user"]

            user = await resolve_user(ctx.client, options["user"])

            reason = options.get("reason", "No reason provided")
            dm_recipient = options.get("dm_recipient", True)

            if dm_recipient:
                try:
                    await send_dm(
                        ctx,
                        user,
                        "Kicked from Cobalt",
                        f"You have been kicked from Cobalt.\nReason: {reason}",
                    )
                except Exception as e:
                    print(f"Could not DM user: {e}")

            await ctx.client.app.rest.kick_user(
                ctx.guild_id,
                user.id,
                reason=reason,
            )

            description = f"Kicked <@{user.id}> (ID: {user.id})\nReason: {reason}"
        except Exception as e:
            succeeded = False
            description = f"Failed to kick user. {e}"

        embed = Embed(
            description=description,
            color=(0x16C47F if succeeded else 0xF93827),
        )
        await ctx.respond(embed=embed, flags=MessageFlag.EPHEMERAL)

async def resolve_user(client, user_input: str):
    user_input = user_input.strip()

    if user_input in ("@everyone", "@here"):
        raise ValueError("Cannot resolve @everyone or @here as a user.")
    if user_input.startswith("<@&") and user_input.endswith(">"):
        raise ValueError("a role isnt a person silly")
    match = re.search(r"(?<!&)\d{15,20}", user_input)
    if not match:
        raise ValueError("invalid format, provide a ping or id.")
    
    user_id = int(match.group())
    return await client.rest.fetch_user(user_id)  # maybe move to a general util file idk, same applies for send_dm func

async def send_dm(ctx: Context, user, title: str, description: str, color: int = 0xF93827):
    try:
        dm_channel = await ctx.client.app.rest.create_dm_channel(user.id)
        embed = Embed(title=title, description=description, color=color)
        await ctx.client.app.rest.create_message(dm_channel.id, embed=embed)
    except Exception as e:
        print(f"Could not DM user: {e}")
