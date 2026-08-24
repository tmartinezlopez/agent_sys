"""Contrato específico y evaluación del rol implementer."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def validate_handoff(stage_state: dict[str, Any], project_dir: Path) -> dict[str, Any]:
    change_name = stage_state.get("change_name")
    change_dir = stage_state.get("change_dir")
    if stage_state.get("status") != "passed":
        return {"valid": False, "error": "spec-writer no está en estado passed"}
    if not change_name or not change_dir:
        return {"valid": False, "error": "spec-writer no dejó nombre ni directorio del change"}
    expected_dir = (project_dir / "openspec" / "changes" / change_name).resolve()
    if Path(change_dir).resolve() != expected_dir:
        return {"valid": False, "error": "el change del handoff está fuera del checkout"}
    tasks_file = expected_dir / "tasks.md"
    if not tasks_file.is_file():
        return {"valid": False, "error": "falta tasks.md en el handoff"}
    git = subprocess.run(["git", "-C", str(project_dir), "rev-parse", "--show-toplevel"],
                         text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if git.returncode != 0:
        return {"valid": False, "error": "el directorio de trabajo no es un checkout Git"}
    return {"valid": True, "change_name": change_name, "change_dir": str(expected_dir),
            "tasks_file": str(tasks_file), "git_root": git.stdout.strip()}


def build_prompt(objective: str, handoff: dict[str, Any]) -> str:
    return f"""Rol: implementer
Objetivo del run: {objective}
Change OpenSpec: {handoff['change_name']}
Directorio del change: {handoff['change_dir']}
Tasks aprobadas: {handoff['tasks_file']}
Checkout escribible: {handoff['git_root']}

Implementa únicamente las tareas de {handoff['tasks_file']} en el checkout.
No cambies el contrato para ocultar errores, no crees otro change, no hagas
commit ni push y no trabajes fuera del checkout declarado. Ejecuta las
verificaciones que exijan las tareas. En la respuesta final resume los
archivos modificados y los comandos ejecutados.
"""


def evaluate(stage_dir: Path, project_dir: Path, change_name: str,
             *, openspec_command: str = "openspec") -> dict[str, Any]:
    command = [openspec_command, "validate", change_name, "--strict"]
    validation = subprocess.run(command, cwd=project_dir, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (stage_dir / "validation.stdout.log").write_text(validation.stdout, encoding="utf-8")
    (stage_dir / "validation.stderr.log").write_text(validation.stderr, encoding="utf-8")
    status = subprocess.run(["git", "-C", str(project_dir), "status", "--short"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    changed_files = status.stdout.splitlines()
    (stage_dir / "changed-files.txt").write_text("\n".join(changed_files) + "\n", encoding="utf-8")
    return {
        "valid": validation.returncode == 0,
        "change_name": change_name,
        "validation_command": command,
        "validation_exit_code": validation.returncode,
        "validation_stdout_file": str(stage_dir / "validation.stdout.log"),
        "validation_stderr_file": str(stage_dir / "validation.stderr.log"),
        "changed_files": changed_files,
        "changed_files_file": str(stage_dir / "changed-files.txt"),
        "error": None if validation.returncode == 0 else "openspec validate --strict falló después de implementar",
    }
