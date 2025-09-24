import re
from hikari import Embed
from lightbulb import Context

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
    return await client.rest.fetch_user(user_id)

async def send_dm(ctx: Context, user, title: str, description: str, color: int = 0xF93827):
    try:
        dm_channel = await ctx.client.app.rest.create_dm_channel(user.id)
        embed = Embed(title=title, description=description, color=color)
        await ctx.client.app.rest.create_message(dm_channel.id, embed=embed)
    except Exception as e:
        print(f"Could not DM user: {e}")

def parse_duration(expr: str) -> int:
    units = {
        'w': 10080, 
        'd': 1440, 
        'h': 60,     
        'm': 1,    
    }

    pattern = re.compile(r'(\d+)([wdhm])', re.I)
    total_minutes = 0

    for amount, unit in pattern.findall(expr.lower()):
        if unit not in units:
            raise ValueError(f"Invalid unit: {unit}")
        total_minutes += int(amount) * units[unit]

    if total_minutes <= 0:
        raise ValueError("Duration must be greater than 0 minutes.")
    return total_minutes