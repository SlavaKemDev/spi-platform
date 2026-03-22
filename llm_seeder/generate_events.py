import random

from google import genai
from google.genai import types
from dotenv import load_dotenv
import django
import os
import json
from datetime import datetime, timedelta


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


from organizations.models import Organization
from events.models import Event
from django.utils import timezone

load_dotenv()
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])


org_text = ""

for org in Organization.objects.all():
    org_text += f"ID: {org.id}, Имя: {org.name}, Описание: {org.name}\n"


ans = client.models.generate_content(
    model="models/gemini-3-pro-preview",  # models/gemini-3-flash-preview
    contents=f"""Придумай 30 тем для студенческих событий в разных сферах: наука, искусство, спорт, технологии, культура. Каждая тема должна быть уникальной и интересной для студентов. Для каждого мероприятия придумай длинное описание, которое будет привлекать внимание и мотивировать студентов участвовать.
    Для каждого события выбери одну из организаций, которая могла бы его провести. Вот список организаций:
    {org_text}
    Ответ должен быть в формате JSON: [{{"organization_id": int, "name": "Название темы", "description": "Краткое описание темы"}}, ...]""",
    config=types.GenerateContentConfig(
        response_mime_type="application/json"
    )
)

data = json.loads(ans.text)

with open("llm_seeder/seed_output.json", "w") as f:
    f.write(ans.text)

# with open("llm_seeder/seed_output.json", "r") as f:
#     data = json.load(f)


for item in data:
    organization = Organization.objects.get(id=item["organization_id"])

    registration_start = timezone.now() - timedelta(seconds=random.randint(0, 10 ** 6))
    registration_end = timezone.now() + timedelta(seconds=random.randint(0, 10 ** 6))
    event_start = registration_end + timedelta(seconds=random.randint(0, 86400))
    event_end = event_start + timedelta(seconds=random.randint(0, 86400))

    event = Event.objects.create(
        organization=organization,
        title=item["name"],
        description=item["description"],
        registration_start=registration_start,
        registration_end=registration_end,
        event_start=event_start,
        event_end=event_end,
        format=random.choice([Event.Format.ONLINE, Event.Format.OFFLINE]),
        is_published=random.random() < 0.7
    )
