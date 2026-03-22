import json
from .llm_api import LLM
from .prefill_url import prefill_url


PROMPT = """You are matching form fields to database columns.

Form fields (name -> description):
{fields}

Database columns:
{columns}

Return a JSON object where keys are form field names and values are the matching DB column name, or null if no match.
Only match if you are confident the field maps to that column.
Return ONLY the JSON, no explanation.

Example:
{{
  "entry.123": "first_name",
  "entry.456": "phone",
  "entry.789": null
}}
"""


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

    # Build user_data from profile using mapping
    user_data = {
        field: user_profile[col]
        for field, col in mapping.items()
        if col and col in user_profile
    }

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
