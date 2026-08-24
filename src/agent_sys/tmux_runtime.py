"""Operaciones tmux limitadas a una sesion propiedad del proyecto."""

from __future__ import annotations

import subprocess
import shlex
import time
from pathlib import Path
from typing import Any


class TmuxRuntime:
    def __init__(self, session: str, owner: str, *, tmux_command: str = "tmux") -> None:
        self.session = session
        self.owner = owner
        self.tmux_command = tmux_command

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([self.tmux_command, *args], text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=False)

    def exists(self) -> bool:
        return self._run("has-session", "-t", self.session).returncode == 0

    def ensure_session(self) -> None:
        if not self.exists():
            self._run("new-session", "-d", "-s", self.session, "-n", "coordinator")
        marker = self._run("show-environment", "-t", self.session).stdout
        owners = [line.split("=", 1)[1] for line in marker.splitlines()
                  if line.startswith("AGENT_SYS_OWNER=")]
        if owners and owners[0] != self.owner:
            raise RuntimeError(f"sesion tmux ocupada por otro owner: {owners[0]}")
        if not owners:
            result = self._run("set-environment", "-t", self.session,
                               "AGENT_SYS_OWNER", self.owner)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "no se pudo marcar la sesion tmux")

    def ensure_window(self, name: str) -> None:
        if ":" in name or not name or name.isdigit():
            raise ValueError("el nombre de ventana debe ser textual y no contener ':'")
        self.ensure_session()
        windows = self._run("list-windows", "-t", self.session, "-F", "#W").stdout.splitlines()
        if name not in windows:
            result = self._run("new-window", "-t", self.session, "-n", name)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "no se pudo crear ventana tmux")

    def window_target(self, name: str) -> str:
        self.ensure_window(name)
        return f"{self.session}:{name}"

    def run_in_window(self, name: str, command: list[str], *, cwd: Path | None,
                      stdout_path: Path, stderr_path: Path,
                      timeout_seconds: float) -> dict[str, Any]:
        """Ejecuta el proceso dentro de la ventana propia y espera su marcador."""
        target = self.window_target(name)
        marker = stdout_path.parent / "exit.code"
        command_text = shlex.join(command)
        directory = shlex.quote(str(cwd)) if cwd else "."
        script = (f"cd {directory} && {command_text} > {shlex.quote(str(stdout_path))} "
                  f"2> {shlex.quote(str(stderr_path))}; code=$?; "
                  f"printf '%s' \"$code\" > {shlex.quote(str(marker))}")
        sent = self._run("send-keys", "-t", target,
                         f"sh -lc {shlex.quote(script)}", "Enter")
        if sent.returncode != 0:
            return {"exit_code": None, "stdout": "", "stderr": "", "error": sent.stderr.strip()}
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if marker.exists():
                try:
                    exit_code = int(marker.read_text(encoding="utf-8"))
                except ValueError:
                    exit_code = 1
                return {"exit_code": exit_code,
                        "stdout": stdout_path.read_text(encoding="utf-8") if stdout_path.exists() else "",
                        "stderr": stderr_path.read_text(encoding="utf-8") if stderr_path.exists() else "",
                        "error": None}
            time.sleep(0.05)
        self._run("kill-window", "-t", target)
        return {"exit_code": 124, "stdout": stdout_path.read_text(encoding="utf-8") if stdout_path.exists() else "",
                "stderr": stderr_path.read_text(encoding="utf-8") if stderr_path.exists() else "",
                "error": f"timeout after {timeout_seconds} seconds"}
