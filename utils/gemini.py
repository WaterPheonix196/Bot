from hikari import User
from google.genai import Client
from google.genai.types import GenerateContentConfig, ThinkingConfig
from pathlib import Path

class ChatbotManager:

    def __init__(self, keys: list[str]):
        self._keys = keys
        self._key_index = 0
        self.system_instruction = (Path(__file__).parent.parent / "ai-context.txt").read_text(encoding="utf-8")
        self.client = Client(api_key=self._keys[self._key_index]) 
        self.chat = self.client.chats.create(
            model="gemini-2.5-flash",
            config=GenerateContentConfig(
                thinking_config=ThinkingConfig(thinking_budget=0),
                system_instruction=self.system_instruction,
            )
        )

    def _cycle_key(self):
        self._key_index += 1

        if self._key_index >= len(self._keys):
            self.client = None
            return
        
        self.client = Client(api_key=self._keys[self._key_index])

    def reset(self): 
        self.system_instruction = (Path(__file__).parent.parent / "ai-context.txt").read_text(encoding="utf-8")
        self.chat = self.client.chats.create(
            model="gemini-2.5-flash",
            config=GenerateContentConfig(
                thinking_config=ThinkingConfig(thinking_budget=0),
                system_instruction=self.system_instruction,
            )
        )

    def generate_response(self, message: str, author: User) -> str:
        if not self.client:
            return "I'm currently out of power. Please try again later."
        
        try:
            response = self.chat.send_message(f"[Discord Id: {author.id}, Discord Name: {author.display_name}] says {message}")
            response_text = response.text
            return response_text
        except Exception:
            self._cycle_key()
            self.chat_history.pop()
            return "I'm currently out of power. Please try again later."