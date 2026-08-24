"""Contrato específico y ejecución objetiva del rol test-runner."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any


TEST_COMMAND = ["pytest", "-q"]


def validate_handoff(stage_state: dict[str, Any], project_dir: Path) -> dict[str, Any]:
    if stage_state.get("status") != "passed":
        return {"valid": False, "error": "implementer no está en estado passed"}
    git_root = stage_state.get("git_root")
    if not git_root or Path(git_root).resolve() != project_dir.resolve():
        return {"valid": False, "error": "el checkout del implementer no coincide"}
    if not (project_dir / "src").exists() or not (project_dir / "tests").exists():
        return {"valid": False, "error": "el checkout no contiene src/ y tests/"}
    return {"valid": True, "git_root": git_root, "change_name": stage_state.get("change_name")}


def build_prompt(objective: str, handoff: dict[str, Any]) -> str:
    return f"""Rol: test-runner
Objetivo del run: {objective}
Checkout de implementer: {handoff['git_root']}
Change: {handoff.get('change_name') or 'no disponible'}
Comando obligatorio: PYTHONPATH=src pytest -q

Ejecuta solo las pruebas declaradas y analiza sus resultados. No modifiques
codigo, pruebas ni configuracion. No corrijas fallos. Registra en tu respuesta
el comando exacto, codigo de salida, pruebas ejecutadas y fallos encontrados.
El coordinador repetirá el comando para verificar objetivamente tu resultado.
"""


def _git_status(project_dir: Path) -> list[str]:
    result = subprocess.run(["git", "-C", str(project_dir), "status", "--short"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return result.stdout.splitlines()


def execute_tests(stage_dir: Path, project_dir: Path, *, timeout_seconds: float) -> dict[str, Any]:
    stage_dir.mkdir(parents=True, exist_ok=True)
    before = _git_status(project_dir)
    started = time.monotonic()
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "src"
    command = ["env", "PYTHONPATH=src", *TEST_COMMAND]
    error: str | None = None
    try:
        result = subprocess.run(TEST_COMMAND, cwd=project_dir, env=environment, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=timeout_seconds, check=False)
        exit_code = result.returncode
        stdout, stderr = result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        error = f"timeout after {timeout_seconds} seconds"
    after = _git_status(project_dir)
    (stage_dir / "tests.stdout.log").write_text(stdout, encoding="utf-8")
    (stage_dir / "tests.stderr.log").write_text(stderr, encoding="utf-8")
    changed = after != before
    summary = {
        "command": command,
        "exit_code": exit_code,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout_file": str(stage_dir / "tests.stdout.log"),
        "stderr_file": str(stage_dir / "tests.stderr.log"),
        "git_status_before": before,
        "git_status_after": after,
        "checkout_modified_by_test_runner": changed,
        "error": error or ("test-runner modificó el checkout" if changed else None),
    }
    return {"valid": exit_code == 0 and not changed, **summary}
