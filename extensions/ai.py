from lightbulb import Loader
from hikari import MessageCreateEvent

from utils.gemini import ChatbotManager 
from constants import GEMINI_API_KEYS

chatbot_manager = ChatbotManager(GEMINI_API_KEYS)
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

    if message.author.id == 1367543367277219840 and "dev reset" in content:
        chatbot_manager.reset()
        await event.message.respond("Sir yes sir! 🫡", reply=True)
        return

    await event.app.rest.trigger_typing(event.channel_id)
    messages = chatbot_manager.generate_response(content, message.author).split("|||")

    if not messages or all(not s.strip() for s in messages):
        return

    for i in range(5):
        if i < len(messages):
            msg = messages[i]
            if msg:
                if i == 0:
                    await message.respond(msg, reply=True)
                elif i == 4:
                    await message.respond("Be right back :D")
                else:
                    await message.respond(msg)