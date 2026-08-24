"""Contrato específico y evaluación objetiva del rol spec-writer."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

CHANGE_MARKER = re.compile(r"(?:AGENT_SYS_CHANGE|change_name)\s*:\s*([a-z0-9][a-z0-9-]*)")


def change_name_for_run(run_id: str) -> str:
    return f"agent-sys-{run_id.lower()}"


def build_prompt(objective: str, run_id: str) -> str:
    change_name = change_name_for_run(run_id)
    return f"""Rol: spec-writer
Objetivo del run: {objective}
Nombre exacto del change: {change_name}

Debes trabajar como spec-writer real del sistema. Crea el change con:
openspec new change \"{change_name}\"
Completa proposal.md, al menos un spec en specs/, design.md y tasks.md.
Usa las instrucciones y el esquema OpenSpec del repositorio. No implementes
codigo de producto, no uses un rol generico y no inventes una configuracion
alternativa. Valida al final con:
openspec validate \"{change_name}\" --strict

En tu respuesta final incluye exactamente una linea con este formato:
AGENT_SYS_CHANGE: {change_name}
Después resume los artefactos creados y el resultado de la validación.
"""


def evaluate(stage_dir: Path, project_dir: Path, run_id: str,
             *, openspec_command: str = "openspec") -> dict[str, Any]:
    stdout = (stage_dir / "stdout.log").read_text(encoding="utf-8") if (stage_dir / "stdout.log").exists() else ""
    match = CHANGE_MARKER.search(stdout)
    if not match:
        return {"valid": False, "error": "la salida no contiene AGENT_SYS_CHANGE"}
    change_name = match.group(1)
    change_dir = project_dir / "openspec" / "changes" / change_name
    required = [change_dir / "proposal.md", change_dir / "design.md", change_dir / "tasks.md"]
    spec_files = list((change_dir / "specs").rglob("*.md")) if (change_dir / "specs").exists() else []
    missing = [str(path) for path in required if not path.is_file()]
    if not spec_files:
        missing.append(str(change_dir / "specs" / "**" / "*.md"))
    if missing:
        return {"valid": False, "change_name": change_name, "change_dir": str(change_dir),
                "missing_artifacts": missing, "error": "faltan artefactos OpenSpec"}
    command = [openspec_command, "validate", change_name, "--strict"]
    validation = subprocess.run(command, cwd=project_dir, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (stage_dir / "validation.stdout.log").write_text(validation.stdout, encoding="utf-8")
    (stage_dir / "validation.stderr.log").write_text(validation.stderr, encoding="utf-8")
    return {
        "valid": validation.returncode == 0,
        "change_name": change_name,
        "change_dir": str(change_dir),
        "artifacts": [str(path) for path in required] + [str(path) for path in spec_files],
        "validation_command": command,
        "validation_exit_code": validation.returncode,
        "validation_stdout_file": str(stage_dir / "validation.stdout.log"),
        "validation_stderr_file": str(stage_dir / "validation.stderr.log"),
        "error": None if validation.returncode == 0 else "openspec validate --strict falló",
    }
