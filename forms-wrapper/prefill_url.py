from urllib.parse import urlencode, urlparse, parse_qs, urlunparse, urlencode
from llm_api import LLM


GENERIC_PROMPT = """You are generating a prefilled URL for a web form.

The form is at: {url}

Form fields:
{fields}

User data to prefill:
{user_data}

Your task: generate a URL with query parameters that will prefill the form fields with the user data.
Most frameworks use the field `name` attribute directly as query parameter.

Return ONLY the full URL with query parameters, nothing else.
"""


def _google_prefill(form: dict, user_data: dict) -> str:
    params = {k: v for k, v in user_data.items() if k.startswith("entry.")}
    base = form["url"].split("?")[0]
    return f"{base}?{urlencode(params, quote_via=__import__('urllib.parse', fromlist=['quote']).quote)}"


def _yandex_prefill(form: dict, user_data: dict) -> str:
    # user_data keys should be like "answer_short_text_12345" or "answer_choices_12345"
    base = form["url"].split("?")[0]
    return f"{base}?{urlencode(user_data)}"


def _tilda_prefill(form: dict, user_data: dict) -> str:
    # user_data keys are field variable names, we add "form-setter-" prefix
    params = {f"form-setter-{k}": v for k, v in user_data.items()}
    base = form["url"].split("?")[0]
    return f"{base}?{urlencode(params)}"


def _generic_prefill(form: dict, user_data: dict) -> str:
    import json
    fields_info = {
        name: field.get("description") or field.get("type")
        for name, field in form.get("user_choice", {}).items()
    }
    llm = LLM()
    url = llm.ask(GENERIC_PROMPT.format(
        url=form["url"],
        fields=json.dumps(fields_info, ensure_ascii=False, indent=2),
        user_data=json.dumps(user_data, ensure_ascii=False, indent=2),
    ))
    return url.strip()


def prefill_url(form: dict, user_data: dict) -> str:
    """
    Generate a prefilled URL for the form.

    form      — output of read_form()
    user_data — {field_name: value} to prefill

    For Google Forms: user_data keys are entry.XXXXXX
    For Yandex Forms: user_data keys are answer_short_text_ID or answer_choices_ID
    For Tilda:        user_data keys are field variable names
    For others:       LLM figures it out
    """
    url = form.get("url", "")

    if "docs.google.com/forms" in url:
        return _google_prefill(form, user_data)
    elif "forms.yandex.ru" in url:
        return _yandex_prefill(form, user_data)
    elif form.get("_platform") == "tilda":
        return _tilda_prefill(form, user_data)
    else:
        return _generic_prefill(form, user_data)
