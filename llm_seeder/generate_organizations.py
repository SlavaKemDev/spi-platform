from google import genai
from google.genai import types
from dotenv import load_dotenv
import django
import os
import json


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


from organizations.models import Organization

load_dotenv()
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

ans = client.models.generate_content(
    model="models/gemini-3-pro-preview",  # models/gemini-3-flash-preview
    contents="""Придумай название и описание для 5 организаций, которые могли бы проводить студенческие мероприятия в разных сферах: наука, искусство, спорт, технологии, культура. Для каждой организации придумай короткое описание.
    Ответ должен быть в формате JSON: [{"name": "Название организации", "description": "Описание организации"}, ...]""",
    config=types.GenerateContentConfig(
        response_mime_type="application/json"
    )
)

data = json.loads(ans.text)

for item in data:
    organization = Organization.objects.create(name=item["name"], description=item["description"])
