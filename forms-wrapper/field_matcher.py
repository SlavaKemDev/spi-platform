import json
from llm_api import LLM
from prefill_url import prefill_url


PROMPT = """You are matching form fields to database columns.

Form fields (name -> description):
{fields}

Database columns:
{columns}

Return a JSON object where keys are form field names and values are:
- a single DB column name string, if the field maps to one column
- an array of DB column names in order, if the field combines multiple columns into one string
  (e.g. full name "ФИО" -> ["last_name", "first_name", "middle_name"], "ФИ" -> ["last_name", "first_name"])
- null if no match

Only match if you are confident. Return ONLY the JSON, no explanation.

Example:
{{
  "entry.123": ["last_name", "first_name", "middle_name"],
  "entry.456": "phone",
  "entry.789": null
}}
"""


def _resolve_value(col, user_profile: dict) -> str | None:
    """Resolve a column or list of columns to a value from user_profile."""
    if col is None:
        return None
    if isinstance(col, list):
        parts = [user_profile[c] for c in col if c in user_profile]
        return " ".join(parts) if parts else None
    return user_profile.get(col)


def match_fields(form: dict, db_columns: list[str], user_profile: dict) -> dict:
    """
    Match form fields to DB columns and generate a prefill URL.

    Returns:
    {
        "mapping": {field_name: db_column_or_None},
        "prefill_url": "https://...",
        "manual_fields": {field_name: field_info}   <- поля которые пользователь вводит сам
    }
    """
    fields_info = {
        name: field.get("description") or field.get("type")
        for name, field in form.get("user_choice", {}).items()
    }

    llm = LLM()
    mapping = llm.ask_json(PROMPT.format(
        fields=json.dumps(fields_info, ensure_ascii=False, indent=2),
        columns=json.dumps(db_columns, ensure_ascii=False),
    ))

    # Build user_data from profile using mapping (supports composite columns)
    user_data = {}
    for field, col in mapping.items():
        value = _resolve_value(col, user_profile)
        if value is not None:
            user_data[field] = value

    # Fields that couldn't be matched — user fills manually
    manual_fields = {
        name: form["user_choice"][name]
        for name, col in mapping.items()
        if col is None
    }

    return {
        "mapping": mapping,
        "prefill_url": prefill_url(form, user_data),
        "manual_fields": manual_fields,
    }
