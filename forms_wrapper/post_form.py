import re
import requests
from bs4 import BeautifulSoup


def _fetch_google_hidden_fields(url: str, session: requests.Session) -> dict:
    """Fetch fresh hidden fields (fbzx, partialResponse, etc.) from Google Forms page."""
    response = session.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    hidden = {}
    for inp in soup.find_all("input", type="hidden"):
        name = inp.get("name")
        if name:
            hidden[name] = inp.get("value", "")
    return hidden


def post_form(form: dict, user_data: dict) -> requests.Response:
    """
    Submit a form.

    form      — output of read_form()
    user_data — values for user_choice fields, e.g. {"name": "Ivan", "email": "ivan@example.com"}
    """
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    payload = {}

    # For Google Forms — always fetch fresh hidden fields right before POST
    if "docs.google.com/forms" in form.get("url", ""):
        fresh_hidden = _fetch_google_hidden_fields(form["url"], session)
        for name, value in fresh_hidden.items():
            payload[name] = value
    else:
        for name, field in form.get("required", {}).items():
            payload[name] = field.get("value")

    # User-supplied fields
    for name, field in form.get("user_choice", {}).items():
        if name in user_data:
            payload[name] = user_data[name]

    action = form["action"] or form["url"]
    method = form.get("method", "POST").upper()
    headers = {"Referer": form["url"]}

    if method == "POST":
        response = session.post(action, data=payload, headers=headers)
    else:
        response = session.get(action, params=payload, headers=headers)

    return response
