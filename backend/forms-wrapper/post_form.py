import requests


def post_form(form: dict, user_data: dict) -> requests.Response:
    """
    Submit a form.

    form      — output of read_form()
    user_data — values for user_choice fields, e.g. {"name": "Ivan", "email": "ivan@example.com"}
    """
    payload = {}

    # Fixed fields
    for name, field in form.get("required", {}).items():
        payload[name] = field.get("value")

    # User-supplied fields
    for name, field in form.get("user_choice", {}).items():
        if name in user_data:
            payload[name] = user_data[name]

    action = form["action"] or form["url"]
    method = form.get("method", "POST").upper()
    headers = {"Referer": form["url"]}

    session = form.get("_session") or requests.Session()

    if method == "POST":
        response = session.post(action, data=payload, headers=headers)
    else:
        response = session.get(action, params=payload, headers=headers)

    return response
