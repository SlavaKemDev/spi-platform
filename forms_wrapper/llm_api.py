import os
import json
from google import genai


class LLM:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY env var is not set")
        self.client = genai.Client(api_key=api_key)

    def ask(self, query: str) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=query,
        )
        return response.text.strip()

    def ask_json(self, query: str) -> dict:
        text = self.ask(query)

        # Strip markdown code block if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0].strip()

        return json.loads(text)