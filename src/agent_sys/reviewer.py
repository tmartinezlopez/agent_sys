"""Contrato específico y evaluación read-only del rol reviewer."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any


DECISION = re.compile(r"AGENT_SYS_REVIEW:\s*(passed|failed|blocked)\b")
FINDING = re.compile(r"AGENT_SYS_FINDING:\s*([^|]+)\|([^|]+)\|(.+)")


def _git_status(project_dir: Path) -> list[str]:
    result = subprocess.run(["git", "-C", str(project_dir), "status", "--short"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return result.stdout.splitlines()


def validate_handoff(stages: dict[str, Any], project_dir: Path) -> dict[str, Any]:
    implementer = stages.get("implementer", {})
    tests = stages.get("test-runner", {})
    if implementer.get("status") != "passed":
        return {"valid": False, "error": "implementer no está en estado passed"}
    if tests.get("status") != "passed":
        return {"valid": False, "error": "test-runner no está en estado passed"}
    git_root = implementer.get("git_root")
    if not git_root or Path(git_root).resolve() != project_dir.resolve():
        return {"valid": False, "error": "el checkout de implementer no coincide"}
    required = [implementer.get("result_file"), tests.get("result_file"),
                implementer.get("tasks_file"), tests.get("stdout_file")]
    missing = [path for path in required if not path or not Path(path).is_file()]
    if missing:
        return {"valid": False, "error": "falta evidencia de implementer o test-runner", "missing": missing}
    return {"valid": True, "git_root": git_root,
            "change_name": implementer.get("change_name"),
            "implementer_result": implementer["result_file"],
            "test_runner_result": tests["result_file"],
            "tasks_file": implementer["tasks_file"],
            "test_stdout": tests["stdout_file"],
            "git_status_before": _git_status(project_dir)}


def build_prompt(objective: str, handoff: dict[str, Any]) -> str:
    return f"""Rol: reviewer
Objetivo del run: {objective}
Checkout read-only: {handoff['git_root']}
Change: {handoff.get('change_name')}
Implementer result: {handoff['implementer_result']}
Test-runner result: {handoff['test_runner_result']}
Tasks: {handoff['tasks_file']}
Tests stdout: {handoff['test_stdout']}

Revisa el diff, las tareas, la evidencia de implementer y los resultados de
test-runner. No edites archivos, no hagas commit ni push. Comprueba contrato,
calidad, seguridad, regresiones y suficiencia de evidencia.

Termina con una línea exacta:
AGENT_SYS_REVIEW: passed
o, si hay un bloqueo:
AGENT_SYS_REVIEW: blocked
Para cada hallazgo usa:
AGENT_SYS_FINDING: severity|evidence-path|explanation
"""


def evaluate(stage_dir: Path, project_dir: Path, handoff: dict[str, Any]) -> dict[str, Any]:
    stdout = (stage_dir / "stdout.log").read_text(encoding="utf-8") if (stage_dir / "stdout.log").exists() else ""
    decision_match = DECISION.search(stdout)
    findings = [{"severity": m.group(1).strip(), "evidence": m.group(2).strip(),
                 "explanation": m.group(3).strip()} for m in FINDING.finditer(stdout)]
    after = _git_status(project_dir)
    unchanged = after == handoff["git_status_before"]
    if not decision_match:
        error = "la salida no contiene una decisión AGENT_SYS_REVIEW"
        decision = "invalid"
    else:
        decision = decision_match.group(1)
        error = None
    if not unchanged:
        error = "reviewer modificó el checkout"
    valid = decision == "passed" and unchanged
    summary = {
        "valid": valid,
        "decision": decision,
        "findings": findings,
        "git_status_before": handoff["git_status_before"],
        "git_status_after": after,
        "checkout_unchanged": unchanged,
        "error": error,
    }
    (stage_dir / "review-summary.json").write_text(
        __import__("json").dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {**summary, "summary_file": str(stage_dir / "review-summary.json")}
