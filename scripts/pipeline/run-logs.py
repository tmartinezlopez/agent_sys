#!/usr/bin/env python3
"""Muestra eventos y logs persistidos de una ejecución sin mutarla."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--worktree", default=".")
    parser.add_argument("--stage", help="filtra una etapa, por ejemplo implementer")
    args = parser.parse_args()

    run_dir = Path(args.worktree) / ".pipeline" / "runs" / args.run_id
    events_path = run_dir / "events.jsonl"
    if not run_dir.is_dir() or not events_path.exists():
        raise SystemExit(f"run no encontrado: {args.run_id}")

    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()
              if line.strip()]
    selected = [
        event for event in events
        if not args.stage or event.get("role") == args.stage
        or event.get("stage") == args.stage
    ]
    print(json.dumps({
        "runId": args.run_id,
        "events": selected,
        "logs": _stage_logs(run_dir, args.stage),
    }, ensure_ascii=False, indent=2))


def _stage_logs(run_dir: Path, stage_filter: str | None) -> list[dict[str, str]]:
    result = []
    stages_dir = run_dir / "stages"
    if not stages_dir.is_dir():
        return result
    for stage_dir in sorted(path for path in stages_dir.iterdir() if path.is_dir()):
        if stage_filter and stage_dir.name != stage_filter:
            continue
        for name in ("prompt.md", "stdout.log", "stderr.log"):
            path = stage_dir / name
            if path.exists():
                result.append({
                    "stage": stage_dir.name,
                    "file": name,
                    "content": path.read_text(encoding="utf-8"),
                })
    return result


if __name__ == "__main__":
    main()
