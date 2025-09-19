from hikari import User
from google.genai import Client
from google.genai.types import GenerateContentConfig
from pathlib import Path

class ChatbotManager:
    def __init__(self, keys: list[str]):
        self._keys = keys
        self._key_index = 0
        self.client = self._new_client()
        self.chat = self._new_chat()

    def _new_client(self) -> Client | None:
        if self._key_index < len(self._keys):
            return Client(api_key=self._keys[self._key_index])
        
        return None

    def _new_chat(self):
        if not self.client:
            return None
        
        system_instruction = (Path(__file__).parent.parent / "ai-context.txt").read_text(encoding="utf-8")
        return self.client.chats.create(
            model="gemini-2.5-flash-lite",
            config=GenerateContentConfig(
                system_instruction=system_instruction,
            ),
        )

    def _cycle_key(self):
        self._key_index += 1
        self.client = self._new_client()
        self.chat = self._new_chat()

    def reset(self):
        self.chat = self._new_chat()

    def generate_response(self, message: str, author: User) -> str:
        if not self.chat:
            return "I'm currently out of power. Please try again later."

        try:
            response = self.chat.send_message(
                f"[Discord Id: {author.id}, Discord Name: {author.display_name}] says {message}"
            )
            return response.text
        except Exception as error:
            self._cycle_key()
            print(f"Error generating response: {error}")
            return "I'm currently out of power. Please try again later."