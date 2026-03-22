from form_reader import read_form
from field_matcher import match_fields
from post_form import post_form


# Данные пользователя из БД
user_profile = {
    "first_name": "Иван",
    "last_name": "Иванов",
    "middle_name": "Иванович",
    "phone": "+79001234567",
    "email": "ivan@example.com",
}

db_columns = list(user_profile.keys())


# --- Шаг 1: Админ парсит форму (один раз, сохраняется в БД) ---

form = read_form("https://kazandigitallegends.com/gaica")


# --- Шаг 2: Матчим поля и генерируем prefill URL (один раз, сохраняется в БД) ---

result = match_fields(form, db_columns, user_profile)

print("Маппинг:", result["mapping"])
print("Поля для ручного ввода:", list(result["manual_fields"].keys()))
print("Prefill URL:", result["prefill_url"])

# result["prefill_url"] — отдаём пользователю, он открывает в браузере
# и видит форму с уже заполненными полями из профиля.
# Остальные (manual_fields) вводит сам.


# --- Шаг 3 (альтернатива prefill): POST напрямую ---
# Если prefill не нужен — можно отправить форму от имени пользователя.

# manual_input = {
#     # поля из result["manual_fields"] которые пользователь заполнил сам
#     # например: "Трек хакатона": "Музыкотерапия"
# }

# user_data = {
#     field: user_profile[col]
#     for field, col in result["mapping"].items()
#     if col and col in user_profile
# }
# user_data.update(manual_input)

# response = post_form(form, user_data)
# print("Статус POST:", response.status_code)
# print("Успех:", "Your response" in response.text or "Ваш ответ" in response.text)
