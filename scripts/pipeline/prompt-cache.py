#!/usr/bin/env python3
"""Caché local, opt-in y segura para resultados de etapas read-only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

FORMAT_VERSION = 1
READ_ONLY_ROLES = {"test-runner", "reviewer", "ui-reviewer", "qa"}
MODES = {"off", "read-only", "read-write"}


def mode() -> str:
    value = os.environ.get("PIPELINE_PROMPT_CACHE_MODE", "off")
    if value not in MODES:
        raise ValueError("PIPELINE_PROMPT_CACHE_MODE debe ser off, read-only o read-write")
    return value


def cache_dir(worktree: str) -> Path:
    configured = os.environ.get("PIPELINE_PROMPT_CACHE_DIR")
    return Path(configured) if configured else Path(worktree) / ".pipeline" / "prompt-cache"


def max_bytes() -> int:
    try:
        value = int(os.environ.get("PIPELINE_PROMPT_CACHE_MAX_BYTES", "52428800"))
    except ValueError as exc:
        raise ValueError("PIPELINE_PROMPT_CACHE_MAX_BYTES debe ser entero") from exc
    if value < 1:
        raise ValueError("PIPELINE_PROMPT_CACHE_MAX_BYTES debe ser >= 1")
    return value


def _checkout_fingerprint(worktree: str) -> str:
    listing = subprocess.run(
        ["git", "-C", worktree, "ls-files", "-co", "--exclude-standard", "-z"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.split(b"\0")
    digest = hashlib.sha256()
    for raw_path in sorted(path for path in listing if path):
        path = Path(worktree) / os.fsdecode(raw_path)
        if not path.is_file():
            continue
        digest.update(raw_path)
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _key(role: str, role_config: dict[str, Any], prompt: str, worktree: str) -> str:
    identity = {
        "format": FORMAT_VERSION,
        "role": role,
        "config": role_config,
        "promptSha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "checkoutSha256": _checkout_fingerprint(worktree),
    }
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def lookup(role: str, role_config: dict[str, Any], prompt: str, worktree: str) -> dict[str, Any]:
    current_mode = mode()
    if current_mode == "off":
        return {"decision": "cache_bypass", "reason": "disabled"}
    max_bytes()
    if role not in READ_ONLY_ROLES:
        return {"decision": "cache_bypass", "reason": "role_not_read_only"}
    key = _key(role, role_config, prompt, worktree)
    path = cache_dir(worktree) / f"{key}.json"
    if not path.exists():
        return {"decision": "cache_miss", "key": key}
    try:
        entry = json.loads(path.read_text(encoding="utf-8"))
        if (entry.get("format") != FORMAT_VERSION or entry.get("key") != key
                or entry.get("status") != "passed"):
            return {"decision": "cache_bypass", "reason": "invalid_entry", "key": key}
    except (OSError, json.JSONDecodeError):
        return {"decision": "cache_bypass", "reason": "unreadable_entry", "key": key}
    return {"decision": "cache_hit", "key": key, "entry": entry, "path": str(path)}


def store(decision: dict[str, Any], result: dict[str, Any], worktree: str) -> dict[str, Any]:
    if mode() != "read-write" or decision.get("decision") != "cache_miss":
        return decision
    key = decision["key"]
    directory = cache_dir(worktree)
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    path = directory / f"{key}.json"
    entry = {"format": FORMAT_VERSION, "key": key, "status": "passed",
             "exitCode": result.get("exitCode"), "role": result.get("role")}
    encoded = (json.dumps(entry, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    current_size = sum(p.stat().st_size for p in directory.glob("*.json"))
    if max_bytes() < len(encoded) or current_size + len(encoded) > max_bytes():
        return {**decision, "stored": False, "reason": "size_limit"}
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes(encoded)
    os.chmod(temporary, 0o600)
    temporary.replace(path)
    return {**decision, "stored": True, "path": str(path)}


def clear(worktree: str, force: bool) -> int:
    directory = cache_dir(worktree)
    entries = sorted(path for path in directory.glob("*.json")
                     if path.is_file() and not path.is_symlink())
    if not force:
        for path in entries:
            print(path)
        return len(entries)
    for path in entries:
        path.unlink()
    for path in directory.glob("*.tmp"):
        if path.is_file() and not path.is_symlink():
            path.unlink()
    return len(entries)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("clear",))
    parser.add_argument("--worktree", default=".")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    count = clear(str(Path(args.worktree).resolve()), args.force)
    print(f"cache_entries={'cleared' if args.force else 'found'}:{count}")


if __name__ == "__main__":
    main()
