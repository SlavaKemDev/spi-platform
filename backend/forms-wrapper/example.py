from form_reader import read_form
from field_matcher import match_fields
from prefill_url import prefill_url

form = read_form("")
mapping = match_fields(form, ["first_name", "last_name", "phone", "email"])

user_profile = {"first_name": "Иван", "last_name": "Иванов", "phone": "+79001234567", "email": "ivan@example.com"}

user_data = {field: user_profile[col] for field, col in mapping.items() if col and col in user_profile}

url = prefill_url(form, user_data)
print(url)