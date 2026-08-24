#!/usr/bin/env python3
"""Ledger durable y event-sourced para un run del pipeline."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STAGES = ("spec-writer", "implementer", "test-runner", "reviewer", "ui-reviewer", "qa")
SPEC_GATE = "gate_spec"


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def runs_root(worktree: str | None) -> Path:
    override = os.environ.get("PIPELINE_RUNS_DIR")
    return Path(override) if override else Path(worktree or os.getcwd()) / ".pipeline" / "runs"


def run_paths(run_id: str, worktree: str | None) -> tuple[Path, Path, Path, Path]:
    root = runs_root(worktree) / run_id
    return root, root / "run.json", root / "events.jsonl", root / "current-state.json"


def pointer_path(worktree: str | None) -> Path:
    return runs_root(worktree).parent / "current-run"


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"JSON inválido: {path}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"JSON no es objeto: {path}")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"ledger corrupto en línea {number}: {exc}") from exc
        if not isinstance(event, dict):
            raise SystemExit(f"ledger corrupto en línea {number}: evento no es objeto")
        events.append(event)
    return events


def state_from(run: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    tasks: dict[str, dict[str, Any]] = {}
    gates: dict[str, dict[str, Any]] = {SPEC_GATE: {"gateId": SPEC_GATE, "status": "pending"}}
    anomalies: list[dict[str, Any]] = []
    for event in events:
        event_type = event.get("type")
        task_id = event.get("taskId")
        role = event.get("role")
        if isinstance(task_id, str):
            task = tasks.setdefault(task_id, {"taskId": task_id, "status": "created"})
            if isinstance(role, str):
                task["role"] = role
            if event_type in ("dispatched", "resumed"):
                task["status"] = "dispatched"
            elif event_type in ("completed", "failed"):
                task["status"] = event_type
        gate_id = event.get("gateId")
        if isinstance(gate_id, str):
            gate = gates.setdefault(gate_id, {"gateId": gate_id, "status": "pending"})
            if isinstance(task_id, str):
                gate["taskId"] = task_id
            if event_type == "approved":
                gate.update(status="approved", approvedBy=event.get("aprobado_por"))
            elif event_type == "rejected":
                gate.update(status="rejected", reason=event.get("reason"))
        if event_type == "anomaly":
            anomalies.append(event)

    statuses = {task["status"] for task in tasks.values()}
    pending_gates = [gate for gate in gates.values() if gate["status"] == "pending"]
    if anomalies or pending_gates:
        status = "blocked"
    elif statuses and statuses <= {"completed"}:
        status = "completed"
    elif "failed" in statuses:
        status = "failed"
    else:
        status = "active"
    return {
        "runId": run["runId"],
        "status": status,
        "updatedAt": now(),
        "tasks": list(tasks.values()),
        "gates": list(gates.values()),
        "anomalies": anomalies,
        "eventCount": len(events),
    }


def rebuild(run_id: str, worktree: str | None) -> dict[str, Any]:
    root, run_path, events_path, state_path = run_paths(run_id, worktree)
    if not root.is_dir() or not run_path.exists():
        raise SystemExit(f"run no encontrado: {run_id}")
    state = state_from(read_json(run_path), load_events(events_path))
    atomic_write(state_path, state)
    return state


def command_init(args: argparse.Namespace) -> None:
    if any(char.isspace() for char in args.run_id):
        raise SystemExit("run_id inválido: no puede contener espacios")
    root, run_path, events_path, _ = run_paths(args.run_id, args.worktree)
    root.mkdir(parents=True, exist_ok=True)
    if run_path.exists():
        existing = read_json(run_path)
        if existing.get("runId") != args.run_id:
            raise SystemExit(f"run existente inválido: {run_path}")
    else:
        atomic_write(run_path, {"runId": args.run_id, "createdAt": now(),
                                "worktree": str(Path(args.worktree or os.getcwd()).resolve())})
    pointer_path(args.worktree).parent.mkdir(parents=True, exist_ok=True)
    pointer_path(args.worktree).write_text(args.run_id + "\n", encoding="utf-8")
    events_path.touch(exist_ok=True)
    if not load_events(events_path):
        append_event(args.run_id, "run_created", "ledger", {}, args.worktree)
    rebuild(args.run_id, args.worktree)


def append_event(run_id: str, event_type: str, emitter: str, payload: dict[str, Any],
                 worktree: str | None) -> None:
    root, run_path, events_path, _ = run_paths(run_id, worktree)
    if not root.is_dir() or not run_path.exists():
        raise SystemExit(f"run no encontrado: {run_id}")
    if not re.fullmatch(r"[a-zA-Z0-9_.:-]+", event_type):
        raise SystemExit("tipo de evento inválido")
    reserved = {"runId", "timestamp", "type", "emitter"}
    if reserved.intersection(payload):
        raise SystemExit("payload no puede sobrescribir campos reservados")
    event = {"runId": run_id, "timestamp": now(), "type": event_type,
             "emitter": emitter, **payload}
    with events_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def command_event(args: argparse.Namespace) -> None:
    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"payload JSON inválido: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("payload debe ser un objeto JSON")
    append_event(args.run_id, args.event_type, args.emitter, payload, args.worktree)
    rebuild(args.run_id, args.worktree)


def resume_plan(run_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    role_status: dict[str, str] = {}
    change: str | None = None
    gates: dict[str, dict[str, Any]] = {SPEC_GATE: {"status": "pending", "approvedBy": None}}
    for event in events:
        role = event.get("role")
        event_type = event.get("type")
        if isinstance(role, str) and role in STAGES and event_type in ("dispatched", "resumed", "completed", "failed"):
            role_status[role] = "dispatched" if event_type in ("dispatched", "resumed") else event_type
        if isinstance(event.get("change"), str):
            change = event["change"]
        gate_id = event.get("gateId")
        if isinstance(gate_id, str) and event_type in ("approved", "rejected"):
            gate = gates.setdefault(gate_id, {"status": "pending", "approvedBy": None})
            gate["status"] = "approved" if event_type == "approved" else "rejected"
            gate["approvedBy"] = event.get("aprobado_por")
    last_completed = next((stage for stage in reversed(STAGES) if role_status.get(stage) == "completed"), None)
    open_stage = next((stage for stage in STAGES if role_status.get(stage) == "dispatched"), None)
    if open_stage:
        resume_stage, mid_stage = open_stage, True
    elif role_status.get("spec-writer") == "completed" and gates[SPEC_GATE]["status"] != "approved":
        resume_stage, mid_stage = SPEC_GATE, False
    elif last_completed is None:
        resume_stage, mid_stage = STAGES[0], False
    else:
        index = STAGES.index(last_completed)
        resume_stage, mid_stage = (STAGES[index + 1], False) if index + 1 < len(STAGES) else (None, False)
    return {"runId": run_id, "change": change, "lastCompletedStage": last_completed,
            "resumeStage": resume_stage, "midStage": mid_stage,
            "midStageRole": open_stage, "gates": gates}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    for name in ("init", "event", "show", "summary", "rebuild", "resume-plan"):
        command = sub.add_parser(name)
        command.add_argument("run_id")
        command.add_argument("--worktree")
        if name == "event":
            command.add_argument("event_type")
            command.add_argument("--emitter", required=True)
            command.add_argument("--payload", default="{}")
        command.set_defaults(handler={"init": command_init, "event": command_event,
                                      "show": lambda a: print(json.dumps(rebuild(a.run_id, a.worktree), indent=2)),
                                      "summary": command_summary,
                                      "rebuild": lambda a: print(json.dumps(rebuild(a.run_id, a.worktree), indent=2)),
                                      "resume-plan": command_resume_plan}[name])
    return result


def command_summary(args: argparse.Namespace) -> None:
    state = rebuild(args.run_id, args.worktree)
    root, _, _, _ = run_paths(args.run_id, args.worktree)
    summary = {key: state[key] for key in ("runId", "status", "eventCount", "tasks", "gates", "anomalies")}
    summary["generatedAt"] = now()
    atomic_write(root / "summary.json", summary)
    pointer = pointer_path(args.worktree)
    if pointer.exists() and pointer.read_text(encoding="utf-8").strip() == args.run_id:
        pointer.unlink()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def command_resume_plan(args: argparse.Namespace) -> None:
    root, run_path, events_path, _ = run_paths(args.run_id, args.worktree)
    if not root.is_dir() or not run_path.exists():
        raise SystemExit(f"run no encontrado: {args.run_id}")
    print(json.dumps(resume_plan(args.run_id, load_events(events_path)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    arguments = parser().parse_args()
    arguments.handler(arguments)
