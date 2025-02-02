from api.prompt import Prompt
import os
from openai import OpenAI
client = OpenAI()

client.api_key = os.getenv("OPENAI_API_KEY")


class ChatGPT:
    def __init__(self):
        self.prompt = Prompt()
        self.model = os.getenv("OPENAI_MODEL", default = "gpt-4o-mini")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", default = 0))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", default = 500))
        #OPENAI
        self.base_url = os.getenv("OPENAI_BASE_URL", default="https://api.openai.com/v1")
        #Groq (OPENAI_BASE_URL", default="https://api.groq.com/openai/v1") => 翻譯的不太好

    def get_response(self):
        response = client.chat.completions.create(
            model=self.model,
            messages=self.prompt.generate_prompt(),
        )
        return response.choices[0].message.content

    def add_msg(self, text):
        self.prompt.add_msg(text)

    def reinit(self, text):
        self.prompt.reinit_(text)
