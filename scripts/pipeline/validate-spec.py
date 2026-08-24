#!/usr/bin/env python3
"""Valida los artefactos OpenSpec producidos por spec-writer."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

MARKER = re.compile(r"AGENT_SYS_CHANGE:\s*([a-z0-9][a-z0-9-]*)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--stage-dir", required=True)
    args = parser.parse_args()
    worktree = Path(args.worktree)
    stage_dir = Path(args.stage_dir)
    stdout = (stage_dir / "stdout.log").read_text(encoding="utf-8")
    match = MARKER.search(stdout)
    result: dict[str, object] = {"valid": False, "changeName": None, "error": None}
    if not match:
        result["error"] = "la salida no contiene AGENT_SYS_CHANGE"
    else:
        name = match.group(1)
        change_dir = worktree / "openspec" / "changes" / name
        required = [change_dir / "proposal.md", change_dir / "design.md", change_dir / "tasks.md"]
        specs = list((change_dir / "specs").rglob("*.md")) if (change_dir / "specs").is_dir() else []
        missing = [str(path) for path in required if not path.is_file()]
        if not specs:
            missing.append(str(change_dir / "specs" / "**" / "*.md"))
        result["changeName"] = name
        result["changeDir"] = str(change_dir)
        if missing:
            result["missing"] = missing
            result["error"] = "faltan artefactos OpenSpec"
        else:
            validation = subprocess.run(["openspec", "validate", name, "--strict"],
                                        cwd=worktree, text=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        check=False)
            (stage_dir / "validation.stdout.log").write_text(validation.stdout, encoding="utf-8")
            (stage_dir / "validation.stderr.log").write_text(validation.stderr, encoding="utf-8")
            result.update(valid=validation.returncode == 0,
                          validationExitCode=validation.returncode)
            if validation.returncode != 0:
                result["error"] = "openspec validate --strict falló"
    (stage_dir / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
