#!/usr/bin/env python3
"""Informe read-only de etapas Codex, gates y resultados de un run."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


LEDGER = Path(__file__).with_name("run-ledger.py")
spec = importlib.util.spec_from_file_location("pipeline_run_ledger", LEDGER)
if spec is None or spec.loader is None:
    raise SystemExit(f"no se pudo cargar el ledger: {LEDGER}")
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


def load_result(event: dict[str, Any], run_dir: Path) -> dict[str, Any] | None:
    path_value = event.get("resultFile")
    if not isinstance(path_value, str):
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = run_dir / path
    if not path.exists():
        return None
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return {
        key: result.get(key)
        for key in ("status", "exitCode", "role", "command", "error", "usage", "cacheDecision")
        if key in result
    }


def build_report(run_dir: Path, run_id: str) -> dict[str, Any]:
    run = ledger.read_json(run_dir / "run.json")
    events = ledger.load_events(run_dir / "events.jsonl")
    state = ledger.state_from(run, events)
    stages: dict[str, dict[str, Any]] = {}
    for event in events:
        task_id = event.get("taskId")
        if not isinstance(task_id, str):
            continue
        stage = stages.setdefault(task_id, {
            "taskId": task_id,
            "role": event.get("role"),
            "dispatches": 0,
        })
        if event["type"] == "dispatched":
            stage["dispatches"] += 1
            stage.setdefault("startedAt", event["timestamp"])
            stage["lastStartedAt"] = event["timestamp"]
        elif event["type"] == "resumed":
            stage["dispatches"] += 1
            stage["lastStartedAt"] = event["timestamp"]
        elif event["type"] in ("completed", "failed"):
            stage["finishedAt"] = event["timestamp"]
            stage["status"] = event["type"]
            result = load_result(event, run_dir)
            if result is not None:
                stage["result"] = result
    for stage in stages.values():
        stage.setdefault("status", "open")
    return {
        "runId": run_id,
        "worktree": run.get("worktree"),
        "status": state["status"],
        "eventCount": len(events),
        "ui": state.get("ui", False),
        "applicableStages": state.get("applicableStages", []),
        "readyForReview": state.get("readyForReview", False),
        "gates": state["gates"],
        "stages": list(stages.values()),
        "anomalies": state["anomalies"],
        "tokenUsage": state.get("tokenUsage", {"totalTokens": 0, "unknownStages": 0}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--worktree", default=".")
    args = parser.parse_args()
    run_dir = Path(args.worktree) / ".pipeline" / "runs" / args.run_id
    if not run_dir.is_dir():
        raise SystemExit(f"run no encontrado: {args.run_id}")
    print(json.dumps(build_report(run_dir, args.run_id),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
