# engine/normalization.py

from typing import Any, List


TRUE_STRINGS = {
    "true", "yes", "y", "sim", "s", "present", "documented", "evidenced",
    "available", "provided", "identified", "defined", "included",
}

FALSE_STRINGS = {
    "false", "no", "n", "nao", "não", "absent", "not documented",
    "not evidenced", "missing", "undefined", "not provided",
}


def normalize_bool(value: Any):
    if isinstance(value, bool):
        return value

    if value is None:
        return None

    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False

    if isinstance(value, str):
        v = value.strip().lower()
        if v in TRUE_STRINGS:
            return True
        if v in FALSE_STRINGS:
            return False

    return None


def normalize_int(value: Any):
    if isinstance(value, int):
        return value

    if value is None:
        return None

    if isinstance(value, float):
        return int(round(value))

    if isinstance(value, str):
        v = value.strip()
        if v.isdigit():
            return int(v)

    return None


def normalize_string(value: Any, allowed_values=None):
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    v = value.strip()
    if not v:
        return None

    if allowed_values and v not in allowed_values:
        return None

    return v


def normalize_list_string(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, list):
        out = []
        for item in value:
            if item is None:
                continue
            s = str(item).strip()
            if s:
                out.append(s)
        return out

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        parts = [p.strip() for p in raw.split(",")]
        return [p for p in parts if p]

    return []


def normalize_field_value(field_def: dict, value: Any):
    field_type = field_def["type"]

    if field_type == "boolean":
        return normalize_bool(value)

    if field_type == "integer":
        return normalize_int(value)

    if field_type == "string":
        return normalize_string(value, field_def.get("allowed_values"))

    if field_type == "list_string":
        return normalize_list_string(value)

    return value
