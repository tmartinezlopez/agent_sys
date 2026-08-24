"""Persistencia del estado proyectado y del ledger append-only."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import validate_transition


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RunLedger:
    def __init__(self, run_dir: Path, run_id: str, objective: str) -> None:
        self.run_dir = run_dir
        self.run_id = run_id
        self.run_path = run_dir / "run.json"
        self.events_path = run_dir / "events.jsonl"
        self.run_dir.mkdir(parents=True, exist_ok=False)
        timestamp = now()
        self.state: dict[str, Any] = {
            "run_id": run_id,
            "objective": objective,
            "status": "pending",
            "created_at": timestamp,
            "updated_at": timestamp,
            "stages": {},
        }
        self._save()
        self.record("run_created", status="pending")

    @classmethod
    def load(cls, run_dir: Path) -> "RunLedger":
        state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        ledger = object.__new__(cls)
        ledger.run_dir = run_dir
        ledger.run_id = state["run_id"]
        ledger.run_path = run_dir / "run.json"
        ledger.events_path = run_dir / "events.jsonl"
        ledger.state = state
        return ledger

    def _save(self) -> None:
        self.state["updated_at"] = now()
        write_json(self.run_path, self.state)

    def record(self, event_type: str, **fields: Any) -> None:
        event = {"timestamp": now(), "run_id": self.run_id, "type": event_type, **fields}
        with self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")

    def ensure_stage(self, stage: str, role: dict[str, Any]) -> dict[str, Any]:
        stages = self.state["stages"]
        if stage not in stages:
            stages[stage] = {"status": "pending", "role": role}
            self._save()
        return stages[stage]

    def transition(self, stage: str, target: str, **fields: Any) -> None:
        current = self.state["stages"][stage]["status"]
        validate_transition(current, target)
        self.state["stages"][stage].update(fields, status=target, updated_at=now())
        self._save()
        self.record("stage_transition", stage=stage, from_status=current, status=target, **fields)

