#!/usr/bin/env python3
"""Triage read-only de los ledgers locales del pipeline."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_STALL_SECONDS = 1800.0
LEDGER = Path(__file__).with_name("run-ledger.py")
spec = importlib.util.spec_from_file_location("pipeline_run_ledger", LEDGER)
if spec is None or spec.loader is None:
    raise SystemExit(f"no se pudo cargar el ledger: {LEDGER}")
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def stall_threshold_seconds() -> float:
    raw = os.environ.get("WATCHDOG_STALL_SECONDS")
    try:
        return float(raw) if raw is not None else DEFAULT_STALL_SECONDS
    except ValueError:
        return DEFAULT_STALL_SECONDS


def run_report(run_dir: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    try:
        run = ledger.read_json(run_dir / "run.json")
        events = ledger.load_events(run_dir / "events.jsonl")
        state = ledger.state_from(run, events)
    except (OSError, SystemExit, json.JSONDecodeError) as error:
        return None, {
            "severity": "error",
            "runId": run_dir.name,
            "kind": "ledger_unreadable",
            "evidence": str(error),
        }

    timestamps = [event["timestamp"] for event in events
                  if isinstance(event.get("timestamp"), str)]
    duration = None
    idle = None
    if timestamps:
        try:
            idle = (datetime.now(UTC) - parse_time(timestamps[-1])).total_seconds()
            if len(timestamps) >= 2:
                duration = (parse_time(timestamps[-1]) - parse_time(timestamps[0])).total_seconds()
        except ValueError as error:
            return None, {
                "severity": "error",
                "runId": run_dir.name,
                "kind": "invalid_timestamp",
                "evidence": str(error),
            }

    pending_gates = sum(gate.get("status") == "pending"
                        for gate in state.get("gates", []))
    report = {
        "runId": state["runId"],
        "status": state["status"],
        "eventCount": len(events),
        "durationSeconds": duration,
        "idleSeconds": idle,
        "pendingGates": pending_gates,
        "anomalies": len(state.get("anomalies", [])),
    }

    finding = None
    if report["status"] == "blocked" or report["anomalies"] or pending_gates:
        finding = {
            "severity": "warning",
            "runId": report["runId"],
            "kind": "run_blocked",
            "evidence": report,
        }

    terminal = report["status"] in ("completed", "failed") or (run_dir / "summary.json").exists()
    if not terminal and pending_gates == 0 and idle is not None and idle > stall_threshold_seconds():
        last = events[-1] if events else {}
        finding = {
            "severity": "warning",
            "runId": report["runId"],
            "kind": "run_stalled",
            "evidence": {
                "idleSeconds": idle,
                "lastEventTimestamp": timestamps[-1],
                "lastEventType": last.get("type"),
                "lastEventRole": last.get("role"),
            },
        }
    return report, finding


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", default=".")
    parser.add_argument("run_ids", nargs="*")
    args = parser.parse_args()

    root = Path(os.environ.get("PIPELINE_RUNS_DIR",
                               Path(args.worktree) / ".pipeline" / "runs"))
    candidates = [root / run_id for run_id in args.run_ids] if args.run_ids else sorted(
        path for path in root.glob("*") if path.is_dir()
    )
    if args.run_ids:
        missing = [run_id for run_id, path in zip(args.run_ids, candidates)
                   if not path.is_dir()]
        if missing:
            raise SystemExit(f"run no encontrado: {', '.join(missing)}")

    reports = []
    findings = []
    for run_dir in candidates:
        report, finding = run_report(run_dir)
        if report is not None:
            reports.append(report)
        if finding is not None:
            findings.append(finding)
    print(json.dumps({"runs": reports, "findings": findings},
                     ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
