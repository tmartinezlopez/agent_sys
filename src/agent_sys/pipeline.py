"""Coordinador de etapas externas Codex con estado y tmux observables."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .contracts import STAGES, predecessor_for, role_config
from .launcher import build_command, execute
from .ledger import RunLedger, now, write_json
from .implementer import build_prompt as build_implementer_prompt, evaluate as evaluate_implementer, validate_handoff
from .spec_writer import build_prompt as build_spec_writer_prompt, evaluate as evaluate_spec_writer
from .tmux_runtime import TmuxRuntime


def new_run_id() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"


def run_stage(objective: str, *, role: str = "spec-writer", runs_dir: Path = Path("runs"),
              run_id: str | None = None, codex_command: str = "codex",
              profile: str | None = None, working_directory: Path | None = None,
              timeout_seconds: float | None = None, tmux_session: str = "agent-sys",
              tmux_command: str = "tmux", use_tmux: bool = True,
              _ledger: RunLedger | None = None) -> dict[str, Any]:
    """Ejecuta una etapa declarada; el resultado queda reconstruible en disco."""
    config = role_config(role)
    run_id = _ledger.run_id if _ledger else (run_id or new_run_id())
    ledger = _ledger or RunLedger(runs_dir / run_id, run_id, objective)
    stage_dir = ledger.run_dir / "stages" / role
    stage_dir.mkdir(parents=True, exist_ok=True)
    ledger.ensure_stage(role, config.to_dict())
    handoff: dict[str, Any] = {}
    if role == "spec-writer":
        prompt = build_spec_writer_prompt(objective, run_id)
    elif role == "implementer":
        handoff = validate_handoff(ledger.state["stages"].get("spec-writer", {}),
                                   working_directory or Path.cwd())
        if not handoff["valid"]:
            reason = handoff["error"]
            ledger.transition(role, "blocked", reason=reason)
            ledger.state["status"] = "blocked"
            ledger._save()
            ledger.record("stage_blocked", stage=role, reason=reason)
            return {"run_id": run_id, "stage": role, "status": "blocked", "reason": reason}
        prompt = build_implementer_prompt(objective, handoff)
    else:
        prompt = (f"Rol: {config.name}\nContrato: {config.prompt_contract}\n"
                  f"Objetivo del run: {objective}\n"
                  "Escribe tu resultado final de forma concisa y cita los artefactos creados.")
    (stage_dir / "prompt.md").write_text(prompt + "\n", encoding="utf-8")
    predecessor = predecessor_for(role)
    predecessor_status = ledger.state["stages"].get(predecessor, {}).get("status") if predecessor else None
    if predecessor is not None and predecessor_status != "passed":
        reason = f"predecesora {predecessor} no superada"
        ledger.transition(role, "blocked", reason=reason)
        ledger.state["status"] = "blocked"
        ledger._save()
        ledger.record("stage_blocked", stage=role, reason=reason)
        return {"run_id": run_id, "stage": role, "status": "blocked", "reason": reason}
    runtime = TmuxRuntime(tmux_session, run_id, tmux_command=tmux_command)
    window = f"run-{run_id}-{role}"
    if use_tmux:
        runtime.ensure_window(window)
    command = build_command(config, prompt, codex_command=codex_command,
                            working_directory=working_directory, profile=profile)
    stage = ledger.state["stages"][role]
    stage.update({"prompt_file": str(stage_dir / "prompt.md"), "command": command,
                  "tmux_window": window if use_tmux else None,
                  "working_directory": str(working_directory) if working_directory else None})
    if handoff:
        stage.update({"change_name": handoff["change_name"],
                      "change_dir": handoff["change_dir"],
                      "tasks_file": handoff["tasks_file"],
                      "git_root": handoff["git_root"]})
    ledger._save()
    ledger.record("stage_command_recorded", stage=role, command=command,
                  model=config.model, reasoning=config.reasoning, sandbox=config.sandbox,
                  tmux_window=window if use_tmux else None)
    ledger.transition(role, "running", started_at=now())
    if use_tmux:
        result = runtime.run_in_window(window, command, cwd=working_directory,
                                       stdout_path=stage_dir / "stdout.log",
                                       stderr_path=stage_dir / "stderr.log",
                                       timeout_seconds=timeout_seconds or config.timeout_seconds)
    else:
        result = execute(command, cwd=working_directory,
                         stdout_path=stage_dir / "stdout.log", stderr_path=stage_dir / "stderr.log",
                         timeout_seconds=timeout_seconds or config.timeout_seconds)
    evaluation: dict[str, Any] = {}
    if result["exit_code"] == 0 and role == "spec-writer":
        evaluation = evaluate_spec_writer(stage_dir, working_directory or Path.cwd(), run_id)
    elif result["exit_code"] == 0 and role == "implementer":
        evaluation = evaluate_implementer(stage_dir, working_directory or Path.cwd(),
                                           handoff["change_name"])
    status = "passed" if result["exit_code"] == 0 and evaluation.get("valid", True) else "failed"
    finished_at = now()
    result_document = {"run_id": run_id, "stage": role, "status": status, **result,
                       **evaluation,
                       "finished_at": finished_at, "stdout_file": str(stage_dir / "stdout.log"),
                       "stderr_file": str(stage_dir / "stderr.log")}
    write_json(stage_dir / "result.json", result_document)
    fields = {k: v for k, v in result.items() if k not in ("stdout", "stderr")}
    fields.update(evaluation)
    ledger.transition(role, status, **fields, result_file=str(stage_dir / "result.json"),
                      finished_at=finished_at)
    ledger.state["status"] = status
    ledger._save()
    ledger.record("stage_finished", stage=role, status=status, exit_code=result["exit_code"],
                  result_file=str(stage_dir / "result.json"))
    return {"run_id": run_id, "stage": role, "status": status, **result,
            "result_file": str(stage_dir / "result.json")}


def run_pipeline(objective: str, *, runs_dir: Path = Path("runs"),
                 codex_command: str = "codex", profile: str | None = None,
                 working_directory: Path | None = None, timeout_seconds: float | None = None,
                 tmux_session: str = "agent-sys", tmux_command: str = "tmux",
                 use_tmux: bool = True, stages: tuple[str, ...] = STAGES) -> dict[str, Any]:
    """Ejecuta las etapas declaradas en orden y detiene el run ante un fallo."""
    unknown = set(stages) - set(STAGES)
    if unknown:
        raise ValueError(f"etapas no declaradas: {sorted(unknown)}")
    run_id = new_run_id()
    ledger = RunLedger(runs_dir / run_id, run_id, objective)
    for stage in stages:
        ledger.ensure_stage(stage, role_config(stage).to_dict())
    for index, stage in enumerate(stages):
        predecessor = predecessor_for(stage)
        if predecessor and ledger.state["stages"].get(predecessor, {}).get("status") != "passed":
            reason = f"predecesora {predecessor} no superada"
            ledger.transition(stage, "blocked", reason=reason)
            for remaining in stages[index + 1:]:
                ledger.transition(remaining, "blocked", reason=f"pipeline detenido: {reason}")
            ledger.state["status"] = "blocked"
            ledger._save()
            ledger.record("pipeline_stopped", stage=stage, status="blocked", reason=reason)
            return {"run_id": run_id, "status": "blocked", "stopped_at": stage, "reason": reason}
        result = run_stage(objective, role=stage, run_id=run_id, codex_command=codex_command,
                           profile=profile, working_directory=working_directory,
                           timeout_seconds=timeout_seconds, tmux_session=tmux_session,
                           tmux_command=tmux_command, use_tmux=use_tmux, _ledger=ledger)
        if result["status"] != "passed":
            reason = f"etapa {stage} terminó en {result['status']}"
            for remaining in stages[index + 1:]:
                ledger.transition(remaining, "blocked", reason=reason)
            ledger.state["status"] = result["status"]
            ledger._save()
            ledger.record("pipeline_stopped", stage=stage, status=result["status"], reason=reason)
            return {"run_id": run_id, "status": result["status"], "stopped_at": stage,
                    "reason": reason}
    ledger.state["status"] = "passed"
    ledger._save()
    ledger.record("pipeline_finished", status="passed", stages=list(stages))
    return {"run_id": run_id, "status": "passed", "stages": list(stages)}


def run_once(prompt: str, *, runs_dir: Path = Path("runs"), run_id: str | None = None,
             codex_command: str = "codex", model: str | None = None,
             profile: str | None = None, sandbox: str = "read-only",
             working_directory: Path | None = None, timeout_seconds: float = 300) -> dict[str, Any]:
    """Compatibilidad con el prototipo inicial."""
    run_id = run_id or new_run_id()
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    events_path, run_path, result_path = run_dir / "events.jsonl", run_dir / "run.json", run_dir / "result.json"
    started_at = now()
    state: dict[str, Any] = {"run_id": run_id, "prompt": prompt, "status": "pending",
                             "created_at": started_at, "updated_at": started_at,
                             "result_file": str(result_path)}
    write_json(run_path, state)
    def event(event_type: str, **fields: Any) -> None:
        with events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"timestamp": now(), "run_id": run_id,
                                     "type": event_type, **fields}, ensure_ascii=False) + "\n")
    event("run_created", status="pending")
    command = [codex_command, "exec", "--json", "--sandbox", sandbox]
    if profile: command.extend(["--profile", profile])
    if model: command.extend(["--model", model])
    if working_directory: command.extend(["--cd", str(working_directory)])
    command.append(prompt)
    state.update(status="running", updated_at=now(), command=command)
    write_json(run_path, state)
    event("agent_started", status="running", command=command)
    outcome = execute(command, cwd=working_directory, stdout_path=run_dir / "agent.stdout.log",
                      stderr_path=run_dir / "agent.stderr.log", timeout_seconds=timeout_seconds)
    status = "passed" if outcome["exit_code"] == 0 else "failed"
    result = {"run_id": run_id, "status": status, "prompt": prompt, **outcome,
              "started_at": started_at, "finished_at": now(), "timeout_seconds": timeout_seconds}
    write_json(result_path, result)
    state.update(status=status, updated_at=result["finished_at"], exit_code=outcome["exit_code"])
    write_json(run_path, state)
    event("agent_finished", status=status, exit_code=outcome["exit_code"], error=outcome["error"])
    return result
