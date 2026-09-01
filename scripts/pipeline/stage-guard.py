#!/usr/bin/env python3
"""Comprueba si un rol puede ser despachado según el ledger."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

STAGES = ("spec-writer", "implementer", "test-runner", "reviewer", "ui-reviewer", "qa")
EXPECTED_SANDBOX = {"spec-writer": "workspace-write", "implementer": "workspace-write",
                    "test-runner": "read-only", "reviewer": "read-only",
                    "ui-reviewer": "read-only", "qa": "read-only"}


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--worktree", required=True)
    args = parser.parse_args()
    roles_path = Path(os.environ.get("PIPELINE_ROLES_FILE", Path(__file__).parent / "roles.json"))
    roles = json.loads(roles_path.read_text(encoding="utf-8"))
    if args.role not in roles or args.role not in STAGES:
        fail(f"rol no declarado: {args.role}")
    if roles[args.role].get("sandbox") != EXPECTED_SANDBOX[args.role]:
        fail(f"sandbox inválido para {args.role}")
    state_path = Path(args.worktree) / ".pipeline" / "runs" / args.run_id / "current-state.json"
    run_path = Path(args.worktree) / ".pipeline" / "runs" / args.run_id / "run.json"
    if not state_path.is_file():
        fail(f"ledger sin estado derivado: {args.run_id}")
    run = json.loads(run_path.read_text(encoding="utf-8")) if run_path.is_file() else {}
    if args.role == "ui-reviewer" and not run.get("ui", False):
        fail("ui-reviewer omitido: la feature no está marcada como UI")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    latest = {task.get("role"): task.get("status") for task in state.get("tasks", [])}
    gates = {gate.get("gateId"): gate.get("status") for gate in state.get("gates", [])}
    applicable = [stage for stage in STAGES
                  if stage != "ui-reviewer" or bool(run.get("ui", False))]
    index = applicable.index(args.role)
    if index:
        predecessor = applicable[index - 1]
        if latest.get(predecessor) != "completed":
            fail(f"{args.role} bloqueado: predecesora {predecessor} no está completada")
    if args.role == "implementer" and gates.get("gate_spec") != "approved":
        fail("implementer bloqueado: gate_spec no está aprobado")
    print(json.dumps({"allowed": True, "role": args.role,
                      "sandbox": roles[args.role]["sandbox"]}))


if __name__ == "__main__":
    main()
