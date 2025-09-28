from lightbulb import Loader
from hikari import MessageCreateEvent, Permissions
from utils.gemini import ChatbotManager 
from os import getenv

chatbot_manager = ChatbotManager(getenv("GEMINI_API_KEYS").split(","))
loader = Loader()

@loader.listener(MessageCreateEvent)
async def on_message_create(event: MessageCreateEvent):
    message = event.message
    content = event.content
    channel = await event.app.rest.fetch_channel(event.channel_id)

    if not "ai-chat" in channel.name:
        return 

    if event.is_bot or not content:
        return

    me = event.app.get_me()
    
    if not me or me.id not in message.user_mentions_ids:
        return

    if "dev reset" in content.lower():
        member = await event.app.rest.fetch_member(event.message.guild_id, event.author_id)
        roles = await member.fetch_roles()
        perms = Permissions.NONE
        
        for role in roles:
            perms |= role.permissions
        
        if Permissions.ADMINISTRATOR not in perms:
            await message.respond("You must have Administrator permissions to reset the chat.", reply=True)
            return

        chatbot_manager.reset()
        await event.message.respond("Sir yes sir! 🫡", reply=True)
        return

    await event.app.rest.trigger_typing(event.channel_id)
    response_text = chatbot_manager.generate_response(content, message.author)
    
    if not response_text or not response_text.strip():
        return

    messages = response_text.split("|||")
    is_first = True

    for msg in messages:
        if msg and msg.strip():
            if is_first:
                await message.respond(msg, reply=True)
                is_first = False
            else:
                await message.respond(msg)