"""Operaciones de consulta sobre runs persistidos en disco."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _run_dirs(runs_dir: Path) -> list[Path]:
    if not runs_dir.is_dir():
        return []
    return sorted(
        (path for path in runs_dir.iterdir() if path.is_dir() and (path / "run.json").is_file()),
        key=lambda path: path.name,
        reverse=True,
    )


def load_state(runs_dir: Path, run_id: str) -> dict[str, Any]:
    run_path = runs_dir / run_id / "run.json"
    if not run_path.is_file():
        raise ValueError(f"run desconocido: {run_id}")
    try:
        state = json.loads(run_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"run.json inválido: {run_id}") from exc
    if state.get("run_id") != run_id:
        raise ValueError(f"run.json no corresponde al run: {run_id}")
    return state


def _status_summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": state["run_id"],
        "objective": state.get("objective", state.get("prompt")),
        "status": state.get("status"),
        "created_at": state.get("created_at"),
        "updated_at": state.get("updated_at"),
        "stages": {name: stage.get("status") for name, stage in state.get("stages", {}).items()},
        "gates": {
            name: gate.get("status") for name, gate in state.get("gates", {}).items()
        },
    }


def status_runs(runs_dir: Path, run_id: str | None = None) -> dict[str, Any]:
    """Devuelve el estado resumido de un run o del directorio de runs."""
    if run_id:
        return _status_summary(load_state(runs_dir, run_id))
    return {
        "runs_dir": str(runs_dir),
        "runs": [_status_summary(load_state(runs_dir, path.name)) for path in _run_dirs(runs_dir)],
    }


def read_logs(runs_dir: Path, run_id: str) -> list[dict[str, Any]]:
    """Lee el ledger de eventos append-only del run en orden de escritura."""
    load_state(runs_dir, run_id)
    events_path = runs_dir / run_id / "events.jsonl"
    if not events_path.is_file():
        raise ValueError(f"events.jsonl ausente para el run: {run_id}")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"evento inválido en {run_id}, línea {line_number}") from exc
        events.append(event)
    return events


def inspect_run(runs_dir: Path, run_id: str) -> dict[str, Any]:
    """Devuelve el estado completo y los artefactos existentes del run."""
    state = load_state(runs_dir, run_id)
    run_dir = runs_dir / run_id
    artifacts = [
        str(path.relative_to(run_dir))
        for path in sorted(run_dir.rglob("*"))
        if path.is_file() and path.name not in {"run.json", "events.jsonl"}
    ]
    return {"run": state, "artifacts": artifacts, "event_count": len(read_logs(runs_dir, run_id))}
