from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceRecord:
    file_id: str
    source_path: str
    system_id: str = ""
    resource_id: str = ""
    category: str = ""
    action: str = ""
    state: str = ""
    timestamp: str = ""
    identifiers: set[str] = field(default_factory=set)
    raw: dict[str, Any] = field(default_factory=dict)
