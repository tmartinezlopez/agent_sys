"""Contrato específico y evaluación read-only del rol qa."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

DECISION = re.compile(r"AGENT_SYS_QA:\s*(passed|blocked)\b")
FINDING = re.compile(r"AGENT_SYS_QA_FINDING:\s*([^|]+)\|([^|]+)\|(.+)")


def _git_status(project_dir: Path) -> list[str]:
    result = subprocess.run(["git", "-C", str(project_dir), "status", "--short"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=False)
    return result.stdout.splitlines()


def validate_handoff(stages: dict[str, Any], project_dir: Path) -> dict[str, Any]:
    required_names = ("spec-writer", "implementer", "test-runner", "reviewer")
    missing_or_bad = [name for name in required_names
                      if stages.get(name, {}).get("status") != "passed"]
    if missing_or_bad:
        return {"valid": False,
                "error": f"etapas previas no superadas: {', '.join(missing_or_bad)}"}
    ui_status = stages.get("ui-reviewer", {}).get("status")
    if ui_status not in ("passed", "skipped"):
        return {"valid": False, "error": "ui-reviewer no está en estado passed o skipped"}
    implementer = stages["implementer"]
    git_root = implementer.get("git_root")
    if not git_root or Path(git_root).resolve() != project_dir.resolve():
        return {"valid": False, "error": "el checkout de implementer no coincide"}
    names = list(required_names) + (["ui-reviewer"] if ui_status == "passed" else [])
    evidence = {name: stages[name].get("result_file") for name in names}
    missing = [path for path in evidence.values() if not path or not Path(path).is_file()]
    if missing:
        return {"valid": False, "error": "falta evidencia de una etapa previa", "missing": missing}
    return {"valid": True, "git_root": git_root, "ui_status": ui_status,
            "evidence": evidence, "git_status_before": _git_status(project_dir)}


def build_prompt(objective: str, handoff: dict[str, Any]) -> str:
    evidence = "\n".join(f"- {name}: {path}" for name, path in handoff["evidence"].items())
    return f"""Rol: qa
Objetivo del run: {objective}
Checkout read-only: {handoff['git_root']}
Estado de ui-reviewer: {handoff['ui_status']}
Evidencia de etapas anteriores:
{evidence}

Valida el resultado completo frente al objetivo original. Lee el diff, las
tareas, los resultados y los resúmenes de todas las etapas. Comprueba que las
pruebas y revisiones cubren el cambio y que no quedan riesgos críticos.
No edites archivos, no hagas commit ni push.

Termina con una línea exacta:
AGENT_SYS_QA: passed
o, si el resultado no está listo:
AGENT_SYS_QA: blocked
Para cada hallazgo usa:
AGENT_SYS_QA_FINDING: severity|evidence-path|explanation
"""


def evaluate(stage_dir: Path, project_dir: Path, handoff: dict[str, Any]) -> dict[str, Any]:
    stdout = (stage_dir / "stdout.log").read_text(encoding="utf-8") \
        if (stage_dir / "stdout.log").exists() else ""
    decision_match = DECISION.search(stdout)
    findings = [{"severity": match.group(1).strip(), "evidence": match.group(2).strip(),
                 "explanation": match.group(3).strip()}
                for match in FINDING.finditer(stdout)]
    after = _git_status(project_dir)
    unchanged = after == handoff["git_status_before"]
    decision = decision_match.group(1) if decision_match else "invalid"
    error = None if decision_match else "la salida no contiene una decisión AGENT_SYS_QA"
    if not unchanged:
        error = "qa modificó el checkout"
    valid = decision in ("passed", "blocked") and unchanged
    summary = {"valid": valid, "decision": decision, "findings": findings,
               "git_status_before": handoff["git_status_before"],
               "git_status_after": after, "checkout_unchanged": unchanged,
               "error": error}
    summary_file = stage_dir / "qa-summary.json"
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return {**summary, "summary_file": str(summary_file)}
