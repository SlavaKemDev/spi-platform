ALLOWED_TYPES = {'text', 'textarea', 'number', 'select', 'checkbox'}


def validate_form_schema(schema: list) -> tuple[bool, str]:
    """
    Validates the registration form schema.

    Expected format — a list of field dicts:
    [
        {
            "name": str,        # unique field identifier, required
            "label": str,       # human-readable field name, required
            "type": str,        # one of: text, textarea, number, select, checkbox; required
            "required": bool,   # whether the field is required, required
            "options": list     # list of strings, required only for type "select"
        },
        ...
    ]

    Examples:
        [
            {"name": "motivation", "label": "Мотивация", "type": "textarea", "required": True},
            {"name": "experience", "label": "Опыт (лет)", "type": "number", "required": False},
            {"name": "track", "label": "Трек", "type": "select", "required": True, "options": ["AI", "Web", "Mobile"]},
        ]

    Returns:
        (True, "") if valid
        (False, "<error message>") if invalid
    """
    if not isinstance(schema, list):
        return False, 'Схема должна быть списком'

    names = set()

    for i, field in enumerate(schema):
        prefix = f'Поле #{i + 1}'

        if not isinstance(field, dict):
            return False, f'{prefix}: должно быть словарём'

        for key in ('name', 'label', 'type', 'required'):
            if key not in field:
                return False, f'{prefix}: отсутствует обязательный ключ "{key}"'

        if not isinstance(field['name'], str) or not field['name']:
            return False, f'{prefix}: "name" должен быть непустой строкой'

        if not isinstance(field['label'], str) or not field['label']:
            return False, f'{prefix}: "label" должен быть непустой строкой'

        if field['type'] not in ALLOWED_TYPES:
            return False, f'{prefix}: недопустимый тип "{field["type"]}", допустимы: {", ".join(ALLOWED_TYPES)}'

        if not isinstance(field['required'], bool):
            return False, f'{prefix}: "required" должен быть булевым значением'

        if field['type'] == 'select':
            options = field.get('options')
            if not isinstance(options, list) or not options:
                return False, f'{prefix}: для типа "select" необходим непустой список "options"'
            if not all(isinstance(o, str) for o in options):
                return False, f'{prefix}: все элементы "options" должны быть строками'

        if field['name'] in names:
            return False, f'{prefix}: дублирующийся "name" "{field["name"]}"'
        names.add(field['name'])

    return True, ''


def validate_form_data(data: dict, schema: list) -> tuple[bool, str]:
    """
    Validates filled form data against a form schema.

    Args:
        data: dict with user's answers, keys are field "name" values from schema.
        schema: list of field dicts (see validate_form_schema for format).

    Expected format:
        {
            "motivation": "Хочу развиваться",
            "experience": 2,
            "track": "AI",
            "agree": True
        }

    Rules:
        - All fields marked as required=True must be present and non-empty
        - Unknown keys (not in schema) are not allowed
        - Values must match the field type:
            text / textarea  → str
            number           → int or float
            checkbox         → bool
            select           → str and must be one of options

    Returns:
        (True, "") if valid
        (False, "<error message>") if invalid
    """
    if not isinstance(data, dict):
        return False, 'Данные формы должны быть словарём'

    schema_by_name = {field['name']: field for field in schema}

    for key in data:
        if key not in schema_by_name:
            return False, f'Неизвестное поле "{key}"'

    for field in schema:
        name = field['name']
        field_type = field['type']
        label = field['label']

        if name not in data:
            if field['required']:
                return False, f'Поле "{label}" обязательно для заполнения'
            continue

        value = data[name]

        if field_type in ('text', 'textarea'):
            if not isinstance(value, str):
                return False, f'Поле "{label}" должно быть строкой'
            if field['required'] and not value.strip():
                return False, f'Поле "{label}" не может быть пустым'

        elif field_type == 'number':
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False, f'Поле "{label}" должно быть числом'

        elif field_type == 'checkbox':
            if not isinstance(value, bool):
                return False, f'Поле "{label}" должно быть булевым значением'

        elif field_type == 'select':
            if not isinstance(value, str):
                return False, f'Поле "{label}" должно быть строкой'
            if value not in field.get('options', []):
                options_str = ', '.join(field.get('options', []))
                return False, f'Поле "{label}": недопустимое значение "{value}", допустимы: {options_str}'

    return True, ''
