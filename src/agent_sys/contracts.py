"""Contratos estables del runtime del pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

STATES = ("pending", "running", "passed", "failed", "blocked")
STAGES = ("spec-writer", "implementer", "test-runner", "reviewer", "ui-reviewer", "qa")


@dataclass(frozen=True)
class RoleConfig:
    name: str
    model: str
    reasoning: str
    sandbox: str
    timeout_seconds: int
    retries: int
    prompt_contract: str
    required_artifacts: tuple[str, ...] = ("result.json",)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["required_artifacts"] = list(self.required_artifacts)
        return value


ROLE_CATALOG: dict[str, RoleConfig] = {
    "spec-writer": RoleConfig(
        "spec-writer", "gpt-5.6-luna", "medium", "workspace-write", 900, 1,
        "Define el change OpenSpec, sus requisitos verificables y artefactos de entrada para implementacion.",
    ),
    "implementer": RoleConfig(
        "implementer", "gpt-5.4", "medium", "workspace-write", 1800, 1,
        "Implementa las tareas aprobadas del change y deja evidencia reproducible.",
    ),
    "test-runner": RoleConfig(
        "test-runner", "gpt-5.3-codex", "medium", "read-only", 900, 1,
        "Ejecuta las pruebas declaradas, registra comandos, resultados y fallos sin modificar el codigo.",
    ),
    "reviewer": RoleConfig(
        "reviewer", "gpt-5.6-luna", "medium", "read-only", 1200, 1,
        "Revisa implementacion, contrato, riesgos y evidencia; no edita archivos.",
    ),
    "ui-reviewer": RoleConfig(
        "ui-reviewer", "gpt-5.4", "medium", "read-only", 1200, 1,
        "Revisa la interfaz solo cuando el change la afecta y registra evidencia visual o bloquea si falta.",
    ),
    "qa": RoleConfig(
        "qa", "gpt-5.4", "medium", "read-only", 1200, 1,
        "Valida el resultado completo frente al objetivo y decide si esta listo para entrega.",
    ),
}


def role_config(role: str) -> RoleConfig:
    try:
        return ROLE_CATALOG[role]
    except KeyError as exc:
        raise ValueError(f"rol no declarado: {role}") from exc


def validate_transition(current: str, target: str) -> None:
    if current not in STATES or target not in STATES:
        raise ValueError(f"estado no valido: {current!r} -> {target!r}")
    allowed = {
        "pending": {"running", "blocked"},
        "running": {"passed", "failed", "blocked"},
        "passed": set(),
        "failed": set(),
        "blocked": set(),
    }
    if target not in allowed[current]:
        raise ValueError(f"transicion no permitida: {current!r} -> {target!r}")


def predecessor_for(stage: str) -> str | None:
    if stage not in STAGES:
        raise ValueError(f"etapa no declarada: {stage}")
    index = STAGES.index(stage)
    return STAGES[index - 1] if index else None
