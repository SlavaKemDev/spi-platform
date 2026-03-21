import json
from llm_api import LLM


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


def match_fields(form: dict, db_columns: list[str]) -> dict:
    """
    Match form user_choice fields to DB columns using LLM.

    Returns: {field_name: db_column_or_None}
    """
    fields_info = {
        name: field.get("description") or field.get("type")
        for name, field in form.get("user_choice", {}).items()
    }

    llm = LLM()
    result = llm.ask_json(PROMPT.format(
        fields=json.dumps(fields_info, ensure_ascii=False, indent=2),
        columns=json.dumps(db_columns, ensure_ascii=False),
    ))
    return result
