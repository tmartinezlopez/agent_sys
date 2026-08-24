"""Ejecución de una única etapa externa y persistencia de su estado."""

from __future__ import annotations

import json
import os
import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _event(events_path: Path, run_id: str, event_type: str, **fields: Any) -> None:
    event = {"timestamp": _now(), "run_id": run_id, "type": event_type, **fields}
    with events_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")


def run_once(
    prompt: str,
    *,
    runs_dir: Path = Path("runs"),
    run_id: str | None = None,
    codex_command: str = "codex",
    model: str | None = None,
    profile: str | None = None,
    sandbox: str = "read-only",
    working_directory: Path | None = None,
    timeout_seconds: float = 300,
) -> dict[str, Any]:
    """Lanza Codex una vez y devuelve el resultado persistido.

    El estado final es ``passed`` si el proceso termina con código 0 y
    ``failed`` en cualquier otro caso, incluido un timeout o un binario ausente.
    """

    run_id = run_id or f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    events_path = run_dir / "events.jsonl"
    run_path = run_dir / "run.json"
    result_path = run_dir / "result.json"
    started_at = _now()
    state: dict[str, Any] = {
        "run_id": run_id,
        "prompt": prompt,
        "status": "pending",
        "created_at": started_at,
        "updated_at": started_at,
        "result_file": str(result_path),
    }
    _write_json(run_path, state)
    _event(events_path, run_id, "run_created", status="pending")

    command = [codex_command, "exec", "--json", "--sandbox", sandbox]
    if profile:
        command.extend(["--profile", profile])
    if model:
        command.extend(["--model", model])
    if working_directory:
        command.extend(["--cd", str(working_directory)])
    command.append(prompt)
    state["status"] = "running"
    state["updated_at"] = _now()
    state["command"] = command
    _write_json(run_path, state)
    _event(events_path, run_id, "agent_started", status="running", command=command)

    exit_code: int | None = None
    stdout = ""
    stderr = ""
    error: str | None = None
    try:
        process = subprocess.Popen(
            command,
            cwd=working_directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            error = f"timeout after {timeout_seconds} seconds"
            os.killpg(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate()
            exit_code = 124
    except OSError as exc:
        error = str(exc)

    (run_dir / "agent.stdout.log").write_text(stdout, encoding="utf-8")
    (run_dir / "agent.stderr.log").write_text(stderr, encoding="utf-8")
    finished_at = _now()
    status = "passed" if exit_code == 0 else "failed"
    result = {
        "run_id": run_id,
        "status": status,
        "exit_code": exit_code,
        "prompt": prompt,
        "stdout": stdout,
        "stderr": stderr,
        "error": error,
        "started_at": started_at,
        "finished_at": finished_at,
        "timeout_seconds": timeout_seconds,
    }
    _write_json(result_path, result)
    state.update({"status": status, "updated_at": finished_at, "exit_code": exit_code})
    _write_json(run_path, state)
    _event(events_path, run_id, "agent_finished", status=status, exit_code=exit_code, error=error)
    return result
