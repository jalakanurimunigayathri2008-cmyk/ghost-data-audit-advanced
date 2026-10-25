from __future__ import annotations
import hashlib
from collections import defaultdict
from typing import Any
from .io_utils import get_value, norm


def identifier_tokens(value: Any) -> set[str]:
    raw = norm(value)
    if not raw:
        return set()
    tokens = {raw}
    if "@" in raw and " " not in raw:
        tokens.add(hashlib.sha256(raw.lower().encode()).hexdigest())
    return tokens


class IdentityResolver:
    """Union-find alias graph built from current identity and historical audit rows."""
    def __init__(self, identity_rows: list[dict[str, Any]], audit_rows: list[dict[str, Any]]):
        self.parent: dict[str, str] = {}
        for row in identity_rows + audit_rows:
            uid = get_value(row, "user_id", "current_user_id", "historical_user_id", "account_id")
            if not uid:
                continue
            self._add(uid)
            for key, value in row.items():
                if any(term in str(key).lower() for term in ("email", "phone", "name", "hash", "identifier")):
                    for alias in identifier_tokens(value):
                        self._add(alias)
                        self._union(uid, alias)
        self.components: dict[str, set[str]] = defaultdict(set)
        for token in list(self.parent):
            self.components[self._find(token)].add(token)

    def _add(self, token: str) -> None:
        self.parent.setdefault(token, token)

    def _find(self, token: str) -> str:
        if self.parent[token] != token:
            self.parent[token] = self._find(self.parent[token])
        return self.parent[token]

    def _union(self, a: str, b: str) -> None:
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            low, high = sorted((ra, rb))
            self.parent[high] = low

    def aliases_for(self, email: str, user_id: str = "") -> set[str]:
        seeds = identifier_tokens(email)
        if user_id:
            seeds.add(user_id)
        roots = {self._find(x) for x in seeds if x in self.parent}
        out = set(seeds)
        for root in roots:
            out.update(self.components.get(root, set()))
        return {x.lower() for x in out}
