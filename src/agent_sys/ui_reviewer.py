"""Contrato condicional del rol ui-reviewer sin navegador simulado."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

UI_SUFFIXES = {".html", ".css", ".scss", ".sass", ".less", ".jsx", ".tsx", ".vue", ".svelte"}
UI_PARTS = {"frontend", "front-end", "web", "ui", "pages", "components", "templates"}


def affects_ui(changed_files: list[str], change_text: str = "") -> bool:
    for entry in changed_files:
        path = entry[3:].strip() if len(entry) > 3 and entry[2] == " " else entry
        parts = set(Path(path).parts)
        if Path(path).suffix.lower() in UI_SUFFIXES or parts & UI_PARTS:
            return True
    text = change_text.lower()
    return any(term in text for term in ("frontend", "front-end", "interfaz", "componente ui", "página web"))


def validate_handoff(stages: dict[str, Any], project_dir: Path) -> dict[str, Any]:
    reviewer = stages.get("reviewer", {})
    if reviewer.get("status") != "passed":
        return {"valid": False, "error": "reviewer no está en estado passed"}
    git_root = reviewer.get("git_root") or stages.get("implementer", {}).get("git_root")
    if not git_root or Path(git_root).resolve() != project_dir.resolve():
        return {"valid": False, "error": "el checkout de reviewer no coincide"}
    return {"valid": True, "git_root": git_root,
            "change_name": reviewer.get("change_name"),
            "review_result": reviewer.get("result_file")}


def check_prerequisites(project_dir: Path, *, base_url: str | None = None,
                        codex_command: str = "codex") -> dict[str, Any]:
    bridge = subprocess.run([codex_command, "mcp", "list"], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    bridge_available = bridge.returncode == 0 and bool(bridge.stdout.strip()) and "No MCP servers" not in bridge.stdout
    if not bridge_available:
        return {"available": False, "reason": "NO_VERIFICABLE: no hay bridge MCP de navegador configurado",
                "bridge_output": bridge.stdout or bridge.stderr}
    if not base_url:
        return {"available": False, "reason": "NO_VERIFICABLE: falta URL base del servidor de desarrollo"}
    try:
        with urlopen(base_url, timeout=3) as response:
            reachable = 200 <= response.status < 500
    except (OSError, URLError) as exc:
        return {"available": False, "reason": f"NO_VERIFICABLE: servidor no accesible ({exc})"}
    return {"available": reachable, "base_url": base_url,
            "reason": None if reachable else "NO_VERIFICABLE: respuesta no utilizable"}


def build_prompt(objective: str, handoff: dict[str, Any], base_url: str) -> str:
    return f"""Rol: ui-reviewer
Objetivo del run: {objective}
Checkout read-only: {handoff['git_root']}
Change: {handoff.get('change_name')}
Reviewer result: {handoff['review_result']}
URL base: {base_url}

Usa exclusivamente un bridge de navegador real configurado en Codex. Crea una
pestaña nueva, no uses ni cierres pestañas ajenas, revisa los escenarios de UI
del change, captura evidencia y cierra solo la pestaña creada. No modifiques
checkout, navegador del usuario, commits ni configuración.

Termina con exactamente una de estas decisiones:
AGENT_SYS_UI_REVIEW: passed
AGENT_SYS_UI_REVIEW: blocked
Cada escenario debe incluir ruta y evidencia real.
"""


def write_unverifiable(stage_dir: Path, reason: str, details: dict[str, Any]) -> dict[str, Any]:
    summary = {"valid": False, "decision": "NO_VERIFICABLE", "reason": reason, **details}
    stage_dir.mkdir(parents=True, exist_ok=True)
    import json
    (stage_dir / "ui-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {**summary, "summary_file": str(stage_dir / "ui-summary.json")}
