from hikari import User
from google.genai import Client
from google.genai.types import GenerateContentConfig
from pathlib import Path

class ChatbotManager:

    def __init__(self, keys: list[str]):
        self._keys = keys
        self._key_index = 0
        self.chat_history = []
        self.system_instruction = (Path(__file__).parent.parent / "ai-context.txt").read_text(encoding="utf-8")
        self.client = Client(api_key=self._keys[self._key_index]) 

    def _cycle_key(self):
        self._key_index += 1

        if self._key_index >= len(self._keys):
            self.client = None
            return
        
        self.client = Client(api_key=self._keys[self._key_index])

    def reset(self): 
        self.system_instruction = (Path(__file__).parent.parent / "ai-context.txt").read_text(encoding="utf-8")
        self.chat_history = []

    def generate_response(self, message: str, author: User) -> str:
        if not self.client:
            return "I'm currently out of power. Please try again later."

        self.chat_history.append({
            "role": "user",
            "parts": [{ "text": f"Discord Id: [{ author.id }, Name: ({ author.display_name })]: { message }" }]
        })

        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=self.chat_history,
                config=GenerateContentConfig(
                    system_instruction=self.system_instruction,
                )
            )

            response_text = response.text
            self.chat_history.append({ "role": "model", "parts": [{ "text": response_text }] })
            return response_text
        except Exception:
            self._cycle_key()
            self.chat_history.pop()
            return "I'm currently out of power. Please try again later."