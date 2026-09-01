#!/usr/bin/env python3
"""Ejecuta un rol Codex y persiste su evidencia de proceso."""

from __future__ import annotations

import argparse
import json
import os
import selectors
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
ROLES_PATH = ROOT / "roles.json"
GIT_GUARD = ROOT / "git-guard.sh"


def load_roles() -> dict[str, dict[str, Any]]:
    path = Path(os.environ.get("PIPELINE_ROLES_FILE", ROLES_PATH))
    return json.loads(path.read_text(encoding="utf-8"))


def coerce_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def is_real_codex(command: str) -> bool:
    return Path(command).name == "codex"


def extract_usage(stdout: str) -> dict[str, Any] | None:
    """Extract the first usage-like object emitted by codex exec --json."""
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(value, dict):
            continue
        for key in ("usage", "tokenUsage", "token_usage"):
            usage = value.get(key)
            if isinstance(usage, dict):
                return usage
    return None


def run_live(command: list[str], args: argparse.Namespace, environment: dict[str, str]) -> tuple[int, str, str, str | None]:
    """Run in a tmux pane while preserving stdout/stderr evidence."""
    process = subprocess.Popen(command, cwd=args.worktree, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=environment)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    streams = {"stdout": [], "stderr": []}
    deadline = time.monotonic() + (args.timeout or 3600)
    timed_out = False
    while selector.get_map():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            process.kill()
            timed_out = True
            break
        for key, _ in selector.select(min(remaining, 0.25)):
            chunk = os.read(key.fileobj.fileno(), 65536)
            if not chunk:
                selector.unregister(key.fileobj)
                continue
            text = chunk.decode("utf-8", errors="replace")
            streams[key.data].append(text)
            print(text, end="", flush=True)
    process.wait()
    if timed_out:
        return 124, "".join(streams["stdout"]), "".join(streams["stderr"]), \
            f"timeout tras {args.timeout or 3600} segundos"
    return process.returncode, "".join(streams["stdout"]), "".join(streams["stderr"]), None


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
    usage_path = output_dir / "usage.json"
    guard_dir = output_dir / ".runtime-bin"
    guard_dir.mkdir(parents=True, exist_ok=True)
    guard_path = guard_dir / "git"
    if guard_path.exists() or guard_path.is_symlink():
        guard_path.unlink()
    guard_path.symlink_to(GIT_GUARD)
    environment = os.environ.copy()
    environment["PATH"] = f"{guard_dir}:{environment.get('PATH', '')}"
    command = [args.codex_command, "exec", "--json",
               "--dangerously-bypass-approvals-and-sandbox",
               "--model", role["model"], "-c", f"model_reasoning_effort={role['reasoning']}",
               "--cd", str(Path(args.worktree).resolve()), prompt]
    started = time.monotonic()
    exit_code: int | None = None
    error: str | None = None
    stdout = ""
    stderr = ""
    if is_real_codex(args.codex_command) and os.environ.get("PIPELINE_ALLOW_REAL_CODEX") != "1":
        exit_code = 126
        error = ("Codex real bloqueado por seguridad; usa un fake en pruebas o "
                 "PIPELINE_ALLOW_REAL_CODEX=1 para una ejecución explícita")
    else:
        try:
            if os.environ.get("PIPELINE_LIVE_OUTPUT") == "1":
                exit_code, stdout, stderr, error = run_live(command, args, environment)
            else:
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
    usage = extract_usage(stdout)
    if usage is not None:
        usage_path.write_text(json.dumps(usage, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    status = "passed" if exit_code == 0 else "failed"
    duration_seconds = round(time.monotonic() - started, 3)
    document = {
        "runId": args.run_id,
        "role": args.role,
        "status": status,
        "exitCode": exit_code,
        "durationSeconds": duration_seconds,
        "error": error,
        "command": command,
        "stdoutFile": str(stdout_path),
        "stderrFile": str(stderr_path),
        "usageFile": str(usage_path) if usage is not None else None,
        "usage": usage,
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
