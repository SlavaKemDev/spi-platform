import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from llm_api import LLM


PROMPT = """You are analyzing an HTML page that contains a form.
Your task is to extract the information needed to submit the form via HTTP POST.

Return a JSON object with this structure:
{{
  "url": "<original page url>",
  "method": "<form method, usually POST>",
  "action": "<form action url>",
  "required": {{
    "<field_name>": {{"type": "<field type>", "value": "<fixed value if any>"}}
  }},
  "user_choice": {{
    "<field_name>": {{"type": "<field type>", "options": ["<option1>", ...], "description": "<what this field is for>"}}
  }}
}}

Rules:
- Pick the MAIN form on the page — the largest one with the most fields. Ignore popups, modals, newsletter signups, and small lead-gen forms.
- "required" contains fields with fixed or hidden values (hidden inputs, CSRF tokens, submit buttons, etc.)
- "user_choice" contains fields that the user must fill in or choose (text inputs, selects, radios, checkboxes, textareas)
- For fields with predefined options (select, radio, checkbox) include "options" list
- For free-text fields omit "options"
- Return ONLY the JSON, no explanation

Page URL: {url}

HTML:
{html}
"""


def _read_google_form(url: str) -> dict:
    # Extract form ID from URL
    match = re.search(r"/forms/d/e/([^/]+)/viewform", url)
    if not match:
        raise ValueError("Cannot extract Google Form ID from URL")
    form_id = match.group(1)

    # Google Forms exposes form structure in the page as a JS variable FB_PUBLIC_LOAD_DATA_
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    response = session.get(url)
    response.raise_for_status()

    # Extract FB_PUBLIC_LOAD_DATA_ JSON blob
    match = re.search(r"FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);\s*</script>", response.text, re.DOTALL)
    if not match:
        raise ValueError("Could not find form data in Google Forms page")

    import json
    data = json.loads(match.group(1))

    # Form structure is at data[1][1]
    fields_raw = data[1][1]
    action = f"https://docs.google.com/forms/d/e/{form_id}/formResponse"

    # Extract hidden fields required by Google Forms
    soup = BeautifulSoup(response.text, "html.parser")
    required = {}
    for hidden in soup.find_all("input", type="hidden"):
        name = hidden.get("name")
        value = hidden.get("value", "")
        if name:
            required[name] = {"type": "hidden", "value": value}

    user_choice = {}

    for field in fields_raw:
        title = field[1]
        field_type_id = field[3]
        entries = field[4] if len(field) > 4 else None

        if not entries:
            continue

        for entry in entries:
            entry_id = f"entry.{entry[0]}"
            options = entry[1] if len(entry) > 1 and entry[1] else None

            # field_type_id: 0=short text, 1=paragraph, 2=multiple choice, 3=dropdown, 4=checkbox, 5=scale, 7=grid, 9=date, 10=time
            if field_type_id in (2, 3, 4) and options:
                user_choice[entry_id] = {
                    "type": {2: "radio", 3: "select", 4: "checkbox"}.get(field_type_id, "select"),
                    "options": [o[0] for o in options],
                    "description": title,
                }
            else:
                field_type_name = {0: "text", 1: "textarea", 5: "scale", 9: "date", 10: "time"}.get(field_type_id, "text")
                user_choice[entry_id] = {
                    "type": field_type_name,
                    "description": title,
                }

    return {
        "url": url,
        "method": "POST",
        "action": action,
        "required": required,
        "user_choice": user_choice,
    }


def _read_generic_form(url: str) -> dict:
    with sync_playwright() as p:
        # Firefox has a different TLS fingerprint — required for Yandex/some other sites
        # that block Chromium headless at the TCP/TLS level
        is_yandex = "yandex.ru" in url or "yandex.com" in url
        browser = p.firefox.launch() if is_yandex else p.chromium.launch(
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="ru-RU",
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["script", "style", "meta", "link", "svg", "img", "noscript"]):
        tag.decompose()

    forms = soup.find_all("form")
    if not forms:
        raise ValueError("No forms found on the page")

    main_form = max(forms, key=lambda f: len(f.find_all(["input", "select", "textarea"])))
    html_content = str(main_form)

    llm = LLM()
    result = llm.ask_json(PROMPT.format(url=url, html=html_content))

    # Detect platform for prefill_url
    if "tilda.ws" in url or "tilda.cc" in url or "t396" in html:
        result["_platform"] = "tilda"

    return result


def read_form(url: str) -> dict:
    # Resolve short links (forms.gle, etc.)
    if "forms.gle" in url or ("docs.google.com/forms" not in url and "google" in url):
        response = requests.head(url, allow_redirects=True)
        url = response.url

    if "docs.google.com/forms" in url:
        return _read_google_form(url)
    return _read_generic_form(url)


