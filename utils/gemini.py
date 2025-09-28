from hikari import User
from google.genai import Client
from google.genai.types import GenerateContentConfig
from pathlib import Path

class ChatbotManager:
    def __init__(self, keys: list[str]):
        self._keys = keys
        self._key_index = 0
        self._special_enabled = False
        self.client = self._new_client()
        self.chat = self._new_chat()

    def _new_client(self) -> Client | None:
        if self._key_index < len(self._keys):
            return Client(api_key=self._keys[self._key_index])
        
        return None

    def _new_chat(self, force_special: bool = False):
        if not self.client:
            return None
        context_file = "special-context.txt" if (self._special_enabled or force_special) else "ai-context.txt"
        context_path = Path(__file__).parent.parent / context_file
        try:
            system_instruction = context_path.read_text(encoding="utf-8")
        except Exception:
            system_instruction = ""
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

    def enable_special_mode(self) -> None:
        self._special_enabled = True
        self.chat = self._new_chat()

    def disable_special_mode(self) -> None:
        self._special_enabled = False
        self.chat = self._new_chat() 

    def toggle_special_mode(self) -> bool:
        self._special_enabled = not self._special_enabled
        self.chat = self._new_chat() 
        return self._special_enabled


    def is_special_mode_enabled(self) -> bool:
        return self._special_enabled

    def reset(self):
        self.chat = self._new_chat()

    def generate_response(self, message: str, author: User) -> str:
        if not self.client:
            return "I'm currently out of power. Please try again later."

        try:
            # If Nathan, always use yandere mode
            if author.id == 1367543367277219840:
                self.chat = self._new_chat(force_special=True)
            else:
                self.chat = self._new_chat()

            response = self.chat.send_message(
                f"[Discord Id: {author.id}, Discord Name: {author.display_name}] says {message}"
            )
            return response.text
        except Exception as error:
            self._cycle_key()
            print(f"Error generating response: {error}")
            return "I'm currently out of power. Please try again later."
