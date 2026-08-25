#!/usr/bin/env python3
"""Ejecuta un rol Codex y persiste su evidencia de proceso."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
ROLES_PATH = ROOT / "roles.json"
GIT_GUARD = ROOT / "git-guard.sh"


def load_roles() -> dict[str, dict[str, Any]]:
    return json.loads(ROLES_PATH.read_text(encoding="utf-8"))


def coerce_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run(args: argparse.Namespace) -> dict[str, Any]:
    roles = load_roles()
    if args.role not in roles:
        raise SystemExit(f"rol no declarado: {args.role}")
    role = roles[args.role]
    prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = output_dir / "stdout.log"
    stderr_path = output_dir / "stderr.log"
    result_path = output_dir / "result.json"
    guard_dir = output_dir / ".runtime-bin"
    guard_dir.mkdir(parents=True, exist_ok=True)
    guard_path = guard_dir / "git"
    if guard_path.exists() or guard_path.is_symlink():
        guard_path.unlink()
    guard_path.symlink_to(GIT_GUARD)
    environment = os.environ.copy()
    environment["PATH"] = f"{guard_dir}:{environment.get('PATH', '')}"
    command = [args.codex_command, "exec", "--json", "--sandbox", role["sandbox"],
               "--model", role["model"], "-c", f"model_reasoning_effort={role['reasoning']}",
               "--cd", str(Path(args.worktree).resolve()), prompt]
    exit_code: int | None = None
    error: str | None = None
    try:
        outcome = subprocess.run(command, cwd=args.worktree, text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 timeout=args.timeout or role["timeout_seconds"], check=False,
                                 env=environment)
        exit_code = outcome.returncode
        stdout = outcome.stdout
        stderr = outcome.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        error = f"timeout tras {args.timeout or role['timeout_seconds']} segundos"
        stdout = coerce_text(exc.stdout)
        stderr = coerce_text(exc.stderr)
    except OSError as exc:
        exit_code = 127
        error = str(exc)
        stdout = ""
        stderr = ""
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    status = "passed" if exit_code == 0 else "failed"
    document = {
        "runId": args.run_id,
        "role": args.role,
        "status": status,
        "exitCode": exit_code,
        "error": error,
        "command": command,
        "stdoutFile": str(stdout_path),
        "stderrFile": str(stderr_path),
        "gitGuard": "merge-push-blocked",
    }
    result_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return document


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--role", required=True)
    result.add_argument("--prompt-file", required=True)
    result.add_argument("--worktree", required=True)
    result.add_argument("--output-dir", required=True)
    result.add_argument("--run-id")
    result.add_argument("--codex-command", default="codex")
    result.add_argument("--timeout", type=float)
    return result


if __name__ == "__main__":
    result = run(parser().parse_args())
    print(json.dumps(result, ensure_ascii=False, indent=2))
