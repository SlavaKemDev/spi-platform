from google import genai
from google.genai import types
from dotenv import load_dotenv
import django
import os
import json


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


from events.models import EventTag

load_dotenv()

data = """IT
 Хакатоны
 Стартапы
 Нетворкинг
 Лекции
 Мастер-классы
 Игры
 Вечеринки
 Спорт
 Саморазвитие
 Знакомства
 Для всех"""

for tag in data.split("\n"):
    tag = tag.strip()
    if not EventTag.objects.filter(name=tag).exists():
        EventTag.objects.create(name=tag)
