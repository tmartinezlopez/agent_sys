"""Construccion y ejecucion controlada de procesos externos Codex."""

from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path
from typing import Any

from .contracts import RoleConfig


def build_command(
    role: RoleConfig,
    prompt: str,
    *,
    codex_command: str = "codex",
    working_directory: Path | None = None,
    profile: str | None = None,
) -> list[str]:
    command = [codex_command, "exec", "--json", "--sandbox", role.sandbox,
               "--model", role.model, "-c", f"model_reasoning_effort={role.reasoning}"]
    if profile:
        command.extend(["--profile", profile])
    if working_directory:
        command.extend(["--cd", str(working_directory)])
    command.append(prompt)
    return command


def execute(command: list[str], *, cwd: Path | None, stdout_path: Path,
            stderr_path: Path, timeout_seconds: float) -> dict[str, Any]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    exit_code: int | None = None
    error: str | None = None
    stdout = stderr = ""
    try:
        process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True,
                                   start_new_session=True)
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
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr, "error": error}
