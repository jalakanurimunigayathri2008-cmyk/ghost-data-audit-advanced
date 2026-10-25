from __future__ import annotations
from datetime import datetime
from typing import Any
from .models import EvidenceRecord
from .rules import treatment_for

PHASE_ORDER = {"FINDING": 0, "REMEDIATION": 1, "VERIFICATION": 2}
OP_ORDER = {
    "REPORT_REMAINING_RECORD": 0, "REPORT_EXPOSED_PII": 1, "REPORT_ACTIVE_DATA_FLOW": 2,
    "REPORT_RESTORE_RISK": 3, "DISABLE_DATA_FLOW": 4, "BLOCK_RESTORE": 5, "DELETE_RECORD": 6,
    "REDACT_RECORD": 7, "ANONYMIZE_RECORD": 8, "VERIFY_RECORD_ABSENT": 9,
    "VERIFY_RECORD_PRESENT": 10, "VERIFY_RECORD_REDACTED": 11, "VERIFY_RECORD_ANONYMIZED": 12,
    "VERIFY_DATA_FLOW_DISABLED": 13, "VERIFY_RESTORE_BLOCKED": 14,
}


def date_value(value: str):
    try:
        return datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def in_scope(record: EvidenceRecord, audit_at: str) -> bool:
    rd, ad = date_value(record.timestamp), date_value(audit_at)
    if not rd or not ad:
        return True
    if rd.tzinfo is None and ad.tzinfo is not None:
        rd = rd.replace(tzinfo=ad.tzinfo)
    if rd.tzinfo is not None and ad.tzinfo is None:
        ad = ad.replace(tzinfo=rd.tzinfo)
    try:
        return rd <= ad
    except TypeError:
        return True


def make_step(phase, system, resource, operation, state, evidence=""):
    return {"phase": phase, "system_id": system or "unknown", "resource_id": resource or "unknown",
            "operation": operation, "state": state, "evidence_id": evidence}


def audit_case(request: dict[str, Any], aliases: set[str], evidence: list[EvidenceRecord],
               rules: dict[str, dict[str, str]]) -> dict[str, Any]:
    case_id = str(request.get("case_id", "")).strip()
    email = str(request.get("email", "")).strip().lower()
    request_text = str(request.get("request_text", "")).lower()
    audit_at = str(request.get("audit_at", ""))
    no_request = ("did not request deletion", "no deletion request", "not a deletion request",
                  "do not delete", "not requesting deletion", "cancel deletion")
    if any(x in request_text for x in no_request):
        return {"case_id": case_id, "deletion_status": "NOT_APPLICABLE", "steps_json": []}

    aliases = {x.lower() for x in aliases if x}
    relevant = []
    for rec in evidence:
        if not in_scope(rec, audit_at):
            continue
        blob = str(rec.raw.get("_text", "")).lower()
        if rec.identifiers.intersection(aliases) or (email and email in blob):
            relevant.append(rec)

    findings, remediations, verifications = [], [], []
    unknown_policy = False
    for rec in relevant:
        action_text = (rec.action + " " + str(rec.raw.get("_text", ""))).lower()
        state = rec.state.upper()
        treatment = treatment_for(rec.category, rules)
        system, resource = rec.system_id, rec.resource_id
        flow = any(x in action_text for x in ("sync", "import", "replicat", "index", "export"))
        restore = any(x in action_text for x in ("restore", "backup", "recovery"))
        present = state in {"PRESENT", "ACTIVE", "EXISTS", "RETAINED", "ENABLED", "RUNNING"} or not state
        if flow and state not in {"DISABLED", "INACTIVE", "STOPPED"}:
            findings.append(make_step("FINDING", system, resource, "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", rec.file_id))
            remediations.append(make_step("REMEDIATION", system, resource, "DISABLE_DATA_FLOW", "DISABLED"))
            verifications.append(make_step("VERIFICATION", system, resource, "VERIFY_DATA_FLOW_DISABLED", "DISABLED"))
        elif restore and state not in {"BLOCKED", "DISABLED", "INACTIVE"}:
            findings.append(make_step("FINDING", system, resource, "REPORT_RESTORE_RISK", "ACTIVE", rec.file_id))
            remediations.append(make_step("REMEDIATION", system, resource, "BLOCK_RESTORE", "BLOCKED"))
            verifications.append(make_step("VERIFICATION", system, resource, "VERIFY_RESTORE_BLOCKED", "BLOCKED"))
        elif present:
            if "RETAIN" in treatment:
                verifications.append(make_step("VERIFICATION", system, resource, "VERIFY_RECORD_PRESENT", "PRESENT", rec.file_id))
            elif treatment in {"REDACT", "REDACT_RECORD", "REDACTION"}:
                findings.append(make_step("FINDING", system, resource, "REPORT_EXPOSED_PII", "PRESENT", rec.file_id))
                remediations.append(make_step("REMEDIATION", system, resource, "REDACT_RECORD", "REDACTED"))
                verifications.append(make_step("VERIFICATION", system, resource, "VERIFY_RECORD_REDACTED", "REDACTED"))
            elif treatment in {"ANONYMIZE", "ANONYMIZE_RECORD", "ANONYMIZATION"}:
                findings.append(make_step("FINDING", system, resource, "REPORT_EXPOSED_PII", "PRESENT", rec.file_id))
                remediations.append(make_step("REMEDIATION", system, resource, "ANONYMIZE_RECORD", "ANONYMIZED"))
                verifications.append(make_step("VERIFICATION", system, resource, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"))
            elif treatment in {"DELETE", "DELETE_RECORD", "PURGE", "ERASE"}:
                findings.append(make_step("FINDING", system, resource, "REPORT_REMAINING_RECORD", "PRESENT", rec.file_id))
                remediations.append(make_step("REMEDIATION", system, resource, "DELETE_RECORD", "ABSENT"))
                verifications.append(make_step("VERIFICATION", system, resource, "VERIFY_RECORD_ABSENT", "ABSENT"))
            else:
                unknown_policy = True

    def unique(items):
        result, seen = [], set()
        for item in items:
            key = tuple(item[k] for k in ("phase", "system_id", "resource_id", "operation", "state", "evidence_id"))
            if key not in seen:
                seen.add(key); result.append(item)
        return result

    findings, remediations, verifications = map(unique, (findings, remediations, verifications))
    # Fail closed: absence of a match is not proof of successful deletion.
    if findings or unknown_policy or not relevant:
        status, steps = "INCOMPLETE", findings + remediations + verifications
    else:
        status, steps = "COMPLETE", verifications
        if not steps or any(not s["evidence_id"] for s in steps):
            status, steps = "INCOMPLETE", []
    steps.sort(key=lambda s: (PHASE_ORDER[s["phase"]], OP_ORDER[s["operation"]],
                              s["system_id"].casefold(), s["resource_id"].casefold()))
    for i, step in enumerate(steps, 1):
        step["step_no"] = i
    return {"case_id": case_id, "deletion_status": status, "steps_json": steps}
