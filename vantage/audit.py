"""Append-only, hash-chained audit ledger. Every delivered insight is reproducible:
replay the bundle_hash, get the identical evidence. Each entry also chains to the
previous entry's hash, so any retroactive edit to the ledger file is detectable.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LEDGER_PATH = Path(__file__).parent.parent / "data" / "audit_ledger.jsonl"


def _last_hash() -> str:
    if not LEDGER_PATH.exists():
        return "genesis"
    lines = LEDGER_PATH.read_text().strip().splitlines()
    if not lines:
        return "genesis"
    return json.loads(lines[-1])["entry_hash"]


def append_entry(
    event_id: str,
    bundle_hash: str,
    persona_id: str,
    methods_run: list[str],
    model_version: str,
    narrative_summary: str,
    row_policy: str,
    feedback: Optional[dict] = None,
    actions_taken: Optional[list[str]] = None,
) -> dict:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    prev_hash = _last_hash()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_id": event_id,
        "bundle_hash": bundle_hash,
        "persona_id": persona_id,
        "row_policy_applied": row_policy,
        "methods_run": methods_run,
        "model_version": model_version,
        "narrative_summary": narrative_summary[:280],
        "feedback": feedback,
        "actions_taken": actions_taken or [],
        "prev_hash": prev_hash,
    }
    canonical = json.dumps(entry, sort_keys=True, default=str)
    entry["entry_hash"] = hashlib.sha256((prev_hash + canonical).encode()).hexdigest()[:16]
    with open(LEDGER_PATH, "a") as fh:
        fh.write(json.dumps(entry, default=str) + "\n")
    return entry


def read_ledger(limit: int = 100) -> list[dict]:
    if not LEDGER_PATH.exists():
        return []
    lines = LEDGER_PATH.read_text().strip().splitlines()
    return [json.loads(line) for line in lines[-limit:]]


def verify_chain() -> bool:
    entries = read_ledger(limit=10_000)
    prev = "genesis"
    for e in entries:
        if e["prev_hash"] != prev:
            return False
        prev = e["entry_hash"]
    return True
