# engine/normalization.py

def normalize_bool(value):
    if isinstance(value, bool):
        return value

    if value is None:
        return None

    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "yes", "y", "present", "documented", "evidenced"}:
            return True
        if v in {"false", "no", "n", "absent", "not documented", "not evidenced"}:
            return False

    return None


def normalize_int(value):
    if isinstance(value, int):
        return value

    if value is None:
        return None

    if isinstance(value, str):
        v = value.strip()
        if v.isdigit():
            return int(v)

    return None


def normalize_string(value, allowed_values=None):
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    v = value.strip()

    if allowed_values and v not in allowed_values:
        return None

    return v


def normalize_field_value(field_def, value):
    field_type = field_def["type"]

    if field_type == "boolean":
        return normalize_bool(value)

    if field_type == "integer":
        return normalize_int(value)

    if field_type == "string":
        return normalize_string(value, field_def.get("allowed_values"))

    return value
