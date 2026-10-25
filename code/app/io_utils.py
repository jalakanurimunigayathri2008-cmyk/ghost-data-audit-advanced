from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Any


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_output(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"], lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({"case_id": row["case_id"], "deletion_status": row["deletion_status"],
                        "steps_json": json.dumps(row["steps_json"], ensure_ascii=False, separators=(",", ":"))})


def first_existing(directory: Path, names: list[str]) -> Path | None:
    return next((directory / n for n in names if (directory / n).exists()), None)


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def get_value(row: dict[str, Any], *keys: str) -> str:
    lower = {str(k).strip().lower(): v for k, v in row.items()}
    for key in keys:
        value = lower.get(key.lower())
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""
