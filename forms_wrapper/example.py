from .form_reader import read_form
from .field_matcher import match_fields, apply_mapping
from .post_form import post_form


# Данные пользователя из БД
user_profile = {
    "first_name": "Иван",
    "last_name": "Иванов",
    "middle_name": "Иванович",
    "phone": "+79001234567",
    "email": "ivan@example.com",
}

db_columns = list(user_profile.keys())


# --- Шаг 1: Парсим форму (один раз, сохраняется в БД) ---

form = read_form("https://forms.yandex.ru/cloud/69a5b7cdd046887551c0c3bb/")


# --- Шаг 2: Матчим поля к колонкам БД через LLM (один раз, сохраняется в БД) ---

matched = match_fields(form, db_columns)

print("Маппинг:", matched["mapping"])
print("Поля для ручного ввода:", list(matched["manual_fields"].keys()))


# --- Шаг 3: Для каждого пользователя — подставляем данные (без LLM) ---

result = apply_mapping(form, matched["mapping"], user_profile)

print("Prefill URL:", result["prefill_url"])

# result["prefill_url"] — отдаём пользователю, он открывает в браузере
# и видит форму с уже заполненными полями из профиля.
# Остальные (manual_fields) вводит сам.


# --- Альтернатива prefill: POST напрямую ---
# Если prefill не нужен — можно отправить форму от имени пользователя.

# manual_input = {
#     # поля из result["manual_fields"] которые пользователь заполнил сам
# }

# response = post_form(form, {**result["prefill_url_data"], **manual_input})
# print("Статус POST:", response.status_code)
