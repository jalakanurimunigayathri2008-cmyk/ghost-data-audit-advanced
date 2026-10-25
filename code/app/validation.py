from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Any

VALID_STATUS = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}
VALID_PHASE = {"FINDING", "REMEDIATION", "VERIFICATION"}
KEYS = {"step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"}


def validate_rows(rows: list[dict[str, Any]], requests: list[dict[str, Any]]) -> list[str]:
    errors = []
    ids = [str(r.get("case_id", "")) for r in rows]
    expected = [str(r.get("case_id", "")) for r in requests]
    if len(rows) != len(requests): errors.append(f"Expected {len(requests)} rows, got {len(rows)}")
    if ids != sorted(ids): errors.append("Rows are not sorted by case_id")
    if len(ids) != len(set(ids)): errors.append("Duplicate case_id values")
    if set(ids) != set(expected): errors.append("Output case IDs differ from input")
    for row in rows:
        case, status, steps = row.get("case_id"), row.get("deletion_status"), row.get("steps_json")
        if status not in VALID_STATUS: errors.append(f"{case}: invalid status {status!r}")
        if not isinstance(steps, list):
            errors.append(f"{case}: steps_json must be an array"); continue
        if status == "NOT_APPLICABLE" and steps: errors.append(f"{case}: NOT_APPLICABLE must have []")
        if status == "COMPLETE" and any(s.get("phase") != "VERIFICATION" for s in steps):
            errors.append(f"{case}: COMPLETE may only have verification steps")
        for i, step in enumerate(steps, 1):
            if set(step) != KEYS: errors.append(f"{case}: step {i} has incorrect keys")
            if step.get("step_no") != i: errors.append(f"{case}: step numbers not consecutive")
            if step.get("phase") not in VALID_PHASE: errors.append(f"{case}: invalid phase")
            if status == "COMPLETE" and not step.get("evidence_id"): errors.append(f"{case}: missing evidence citation")
    return errors


def validate_csv(path: Path, expected_count: int) -> list[str]:
    if not path.exists(): return [f"Output file missing: {path}"]
    errors = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["case_id", "deletion_status", "steps_json"]:
            errors.append(f"Unexpected columns: {reader.fieldnames}")
        rows = list(reader)
    if len(rows) != expected_count: errors.append(f"Expected {expected_count} data rows, got {len(rows)}")
    for i, row in enumerate(rows, 1):
        try: json.loads(row["steps_json"])
        except Exception as exc: errors.append(f"Row {i} has invalid JSON: {exc}")
    return errors
