import json
import stat
from pathlib import Path

from agent_sys.pipeline import run_once


def fake_codex(tmp_path: Path, body: str) -> str:
    path = tmp_path / "fake-codex"
    path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return str(path)


def read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_run_once_persists_success(tmp_path: Path) -> None:
    command = fake_codex(tmp_path, 'printf \'{"type":"message"}\\n\'; exit 0\n')

    result = run_once("haz una prueba", runs_dir=tmp_path / "runs", codex_command=command)
    run_dir = tmp_path / "runs" / result["run_id"]

    assert result["status"] == "passed"
    assert result["exit_code"] == 0
    assert json.loads((run_dir / "run.json").read_text())["command"] == [
        command, "exec", "--json", "--sandbox", "read-only", "haz una prueba"
    ]
    assert json.loads((run_dir / "run.json").read_text())["status"] == "passed"
    assert "message" in (run_dir / "agent.stdout.log").read_text()
    assert [event["type"] for event in read_events(run_dir / "events.jsonl")] == [
        "run_created", "agent_started", "agent_finished"
    ]


def test_run_once_records_process_failure(tmp_path: Path) -> None:
    command = fake_codex(tmp_path, "echo fallo >&2; exit 7\n")

    result = run_once("fallará", runs_dir=tmp_path / "runs", codex_command=command)

    assert result["status"] == "failed"
    assert result["exit_code"] == 7
    assert result["error"] is None
    assert "fallo" in result["stderr"]


def test_run_once_records_timeout(tmp_path: Path) -> None:
    command = fake_codex(tmp_path, "sleep 1\n")

    result = run_once("se bloqueará", runs_dir=tmp_path / "runs", codex_command=command, timeout_seconds=0.01)

    assert result["status"] == "failed"
    assert result["exit_code"] == 124
    assert result["error"] == "timeout after 0.01 seconds"
