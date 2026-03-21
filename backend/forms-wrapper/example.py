from form_reader import read_form
from field_matcher import match_fields
from post_form import post_form


# --- Шаг 1: Админ парсит форму (один раз, сохраняется в БД) ---

form = read_form("https://forms.gle/doTzzXDUjJyYijtL9")

# form выглядит так:
# {
#   "url": "...",
#   "method": "POST",
#   "action": "...",
#   "required": { "fvv": {...}, "fbzx": {...}, ... },
#   "user_choice": {
#     "entry.235906976": {"type": "radio", "options": ["Вариант 1"], "description": "Вопрос без заголовка"},
#     ...
#   }
# }


# --- Шаг 2: Сопоставляем поля формы с колонками БД (тоже один раз) ---

db_columns = ["first_name", "last_name", "middle_name", "phone", "email"]
mapping = match_fields(form, db_columns)

# mapping выглядит так:
# {
#   "entry.235906976": null,   <- нет совпадения, пользователь вводит сам
#   "entry.978410643": "email" <- совпало с колонкой email
# }

print("Маппинг полей:", mapping)

manual_fields = {
    name: form["user_choice"][name]
    for name, col in mapping.items()
    if col is None
}
print("Пользователь должен заполнить:", list(manual_fields.keys()))


# --- Шаг 3: Пользователь отправляет форму ---

# Данные пользователя из БД
user_profile = {
    "first_name": "Иван",
    "last_name": "Иванов",
    "middle_name": "Иванович",
    "phone": "+79001234567",
    "email": "ivan@example.com",
}

# Данные которые пользователь ввёл вручную (то что не нашлось в профиле)
manual_input = {
    "entry.235906976": "Вариант 1",
}

# Собираем итоговый payload
user_data = {}
for field, col in mapping.items():
    if col and col in user_profile:
        user_data[field] = user_profile[col]

user_data.update(manual_input)

print("Отправляем:", user_data)

response = post_form(form, user_data)
print("Статус:", response.status_code)
print("Успех:", "Your response" in response.text or "Ваш ответ" in response.text)
