from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Any, Iterable
from .io_utils import get_value
from .models import EvidenceRecord


def flatten(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from flatten(child)
    elif isinstance(value, list):
        for child in value:
            yield from flatten(child)


def read_records(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    text = path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".json":
        try:
            return list(flatten(json.loads(text)))
        except json.JSONDecodeError:
            return [{"text": text}]
    if suffix == ".jsonl":
        result = []
        for line in text.splitlines():
            if line.strip():
                try:
                    result.extend(flatten(json.loads(line)))
                except json.JSONDecodeError:
                    result.append({"text": line})
        return result
    if suffix in {".txt", ".log", ".sql"}:
        return [{"text": line, "line_no": i + 1} for i, line in enumerate(text.splitlines()) if line.strip()]
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            return [{"text": page.extract_text() or "", "page_no": i + 1}
                    for i, page in enumerate(PdfReader(str(path)).pages)]
        except Exception:
            return [{"text": "PDF_EXTRACTION_UNAVAILABLE"}]
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}:
        try:
            from PIL import Image
            import pytesseract
            return [{"text": pytesseract.image_to_string(Image.open(path))}]
        except Exception:
            return [{"text": "IMAGE_OCR_UNAVAILABLE"}]
    return []


def load_evidence_file(path: Path, file_id: str) -> list[EvidenceRecord]:
    try:
        rows = read_records(path)
    except OSError:
        return []
    result = []
    for i, row in enumerate(rows, 1):
        text = " ".join(str(v) for v in row.values() if v is not None)
        action = get_value(row, "operation", "action", "event", "activity", "event_type")
        state = get_value(row, "state", "status", "result", "record_state")
        hay = (text + " " + action + " " + state).lower()
        if not action:
            action = next((x for x in ("restore", "backup", "sync", "import", "delete", "purge", "export", "index")
                           if x in hay), "")
        if not state:
            if any(x in hay for x in ("active", "enabled", "running", "exists", "present", "retained")):
                state = "ACTIVE" if any(x in hay for x in ("active", "enabled", "running")) else "PRESENT"
            elif any(x in hay for x in ("deleted", "absent", "purged")):
                state = "ABSENT"
        ids = set()
        for k, v in row.items():
            if any(t in str(k).lower() for t in ("email", "phone", "name", "hash", "user_id", "identifier")):
                if v is not None and str(v).strip():
                    ids.add(str(v).strip().lower())
        result.append(EvidenceRecord(
            file_id=file_id, source_path=str(path),
            system_id=get_value(row, "system_id", "system", "source_system", "service") or path.parent.name or "unknown",
            resource_id=get_value(row, "resource_id", "record_id", "object_id", "row_id", "account_id", "id", "path")
                         or f"{path.stem}_row_{i}",
            category=get_value(row, "data_category", "category", "record_type", "data_type", "table"),
            action=action, state=state, timestamp=get_value(row, "timestamp", "event_time", "created_at", "updated_at"),
            identifiers=ids, raw={**row, "_text": text}
        ))
    return result


def load_all_evidence(dataset_dir: Path, manifest: list[dict[str, Any]]) -> tuple[list[EvidenceRecord], list[str]]:
    warnings = []
    evidence_dir = dataset_dir / "evidence"
    if not evidence_dir.exists():
        return [], ["Evidence directory not found: dataset/evidence"]
    mapping = {}
    for row in manifest:
        fid = get_value(row, "file_id", "evidence_id", "id")
        rel = get_value(row, "relative_path", "path", "file_path", "filename", "evidence_path")
        if fid and rel:
            mapping[Path(rel).as_posix()] = fid
            mapping[Path(rel).name] = fid
    records = []
    for path in sorted(evidence_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(dataset_dir).as_posix()
        fid = mapping.get(rel, mapping.get(path.name, f"file:{rel}"))
        loaded = load_evidence_file(path, fid)
        if loaded and "UNAVAILABLE" in str(loaded[0].raw.get("_text", loaded[0].raw.get("text", ""))):
            warnings.append(f"Optional extractor unavailable for {rel}")
        records.extend(loaded)
    return records, warnings
