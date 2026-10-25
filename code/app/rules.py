from __future__ import annotations
from typing import Any
from .io_utils import get_value


def load_rules(rows: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    result = {}
    for row in rows:
        category = get_value(row, "data_category", "category", "record_type", "data_type")
        if category:
            result[category.lower()] = {str(k).lower(): str(v or "").strip() for k, v in row.items()}
    return result


def treatment_for(category: str, rules: dict[str, dict[str, str]]) -> str:
    row = rules.get((category or "").lower(), {})
    for key in ("required_treatment", "treatment", "deletion_action", "action", "rule", "required_action"):
        if row.get(key):
            return row[key].upper().replace(" ", "_")
    return "UNKNOWN"
