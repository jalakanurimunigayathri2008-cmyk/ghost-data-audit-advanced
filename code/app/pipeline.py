from __future__ import annotations
from pathlib import Path
from typing import Any
from .io_utils import read_csv_rows, first_existing, get_value, write_output
from .identity import IdentityResolver, identifier_tokens
from .evidence import load_all_evidence
from .rules import load_rules
from .auditor import audit_case
from .validation import validate_rows, validate_csv


def run_pipeline(dataset_dir: Path, output_path: Path, strict: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")
    names = {
        "requests": ["deletion_requests.csv"],
        "identities": ["user_identities.csv"],
        "audit": ["user_audit_log.csv"],
        "rules": ["deletion_rules.csv"],
        "manifest": ["evidence_files.csv"],
    }
    paths = {k: first_existing(dataset_dir, v) for k, v in names.items()}
    if not paths["requests"]:
        raise FileNotFoundError(f"Missing {dataset_dir / 'deletion_requests.csv'}")
    warnings = []
    for key in ("identities", "audit", "rules", "manifest"):
        if not paths[key]: warnings.append(f"Missing expected dataset file: {names[key][0]}")
    if strict and warnings:
        raise RuntimeError("; ".join(warnings))
    requests = read_csv_rows(paths["requests"])
    identities = read_csv_rows(paths["identities"]) if paths["identities"] else []
    audit_rows = read_csv_rows(paths["audit"]) if paths["audit"] else []
    rule_rows = read_csv_rows(paths["rules"]) if paths["rules"] else []
    manifest = read_csv_rows(paths["manifest"]) if paths["manifest"] else []
    resolver = IdentityResolver(identities, audit_rows)
    evidence, ev_warnings = load_all_evidence(dataset_dir, manifest)
    warnings.extend(ev_warnings)
    rules = load_rules(rule_rows)
    rows = []
    for request in requests:
        email = get_value(request, "email")
        uid = get_value(request, "user_id", "account_id")
        aliases = resolver.aliases_for(email, uid) | identifier_tokens(email)
        rows.append(audit_case(request, aliases, evidence, rules))
    rows.sort(key=lambda x: str(x["case_id"]))
    errors = validate_rows(rows, requests)
    if not dry_run:
        write_output(output_path, rows)
        errors.extend(validate_csv(output_path, len(requests)))
    warnings.extend(errors)
    return {"request_count": len(requests), "output_count": len(rows), "warnings": warnings,
            "valid": not errors, "rows": rows}
