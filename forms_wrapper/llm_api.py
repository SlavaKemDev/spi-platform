import os
import json
import uuid
import requests


AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


class LLM:
    def __init__(self):
        self.credentials = os.environ.get("GIGACHAT_CREDENTIALS")
        if not self.credentials:
            raise ValueError("GIGACHAT_CREDENTIALS env var is not set")
        self._token = None

    def _get_token(self) -> str:
        response = requests.post(
            AUTH_URL,
            headers={
                "Authorization": f"Basic {self.credentials}",
                "RqUID": str(uuid.uuid4()),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"scope": "GIGACHAT_API_PERS"},
            verify=False,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def ask(self, query: str) -> str:
        if not self._token:
            self._token = self._get_token()

        response = requests.post(
            CHAT_URL,
            headers={"Authorization": f"Bearer {self._token}"},
            json={
                "model": "GigaChat",
                "messages": [{"role": "user", "content": query}],
            },
            verify=False,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    def ask_json(self, query: str) -> dict:
        text = self.ask(query)

        # Strip markdown code block if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0].strip()

        return json.loads(text)


if __name__ == "__main__":
    llm = LLM()
    print(llm.ask("Hello World"))