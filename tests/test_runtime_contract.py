import json
import stat
import subprocess
from pathlib import Path

from agent_sys.contracts import ROLE_CATALOG, STAGES, predecessor_for, role_config
from agent_sys.ledger import RunLedger
from agent_sys.launcher import build_command
from agent_sys.pipeline import run_pipeline, run_stage
from agent_sys.tmux_runtime import TmuxRuntime


def fake_codex(tmp_path: Path, body: str) -> str:
    path = tmp_path / "fake-codex"
    path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return str(path)


def test_catalog_is_concrete_and_ordered() -> None:
    assert tuple(ROLE_CATALOG) == STAGES
    assert all(config.model and config.reasoning == "medium" and config.prompt_contract
               for config in ROLE_CATALOG.values())
    assert role_config("spec-writer").sandbox == "workspace-write"
    assert role_config("test-runner").sandbox == "read-only"
    assert predecessor_for("implementer") == "spec-writer"


def test_launcher_records_real_role_flags() -> None:
    command = build_command(role_config("reviewer"), "revisa esto", working_directory=Path("/tmp"))
    assert command[:6] == ["codex", "exec", "--json", "--sandbox", "read-only", "--model"]
    assert "gpt-5.6-luna" in command
    assert "model_reasoning_effort=medium" in command
    assert command[-2:] == ["--cd", "/tmp"] or command[-1] == "revisa esto"


def test_stage_persists_contract_and_can_be_reloaded(tmp_path: Path) -> None:
    command = fake_codex(tmp_path, "printf '{\\\"ok\\\":true}\\n'; exit 0\n")
    result = run_stage("crear una especificacion", runs_dir=tmp_path / "runs",
                       codex_command=command, use_tmux=False)
    run_dir = tmp_path / "runs" / result["run_id"]
    ledger = RunLedger.load(run_dir)
    assert result["status"] == "passed"
    assert ledger.state["stages"]["spec-writer"]["status"] == "passed"
    assert json.loads((run_dir / "stages/spec-writer/result.json").read_text())["exit_code"] == 0
    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
    assert "stage_command_recorded" in [event["type"] for event in events]


def test_tmux_uses_named_owned_window(tmp_path: Path) -> None:
    socket = "agent_sys_contract_test"
    wrapper = tmp_path / "tmux-wrapper"
    wrapper.write_text(f"#!/usr/bin/env bash\nexec tmux -L {socket} \"$@\"\n", encoding="utf-8")
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)
    runtime = TmuxRuntime("agent-sys-test", "run-123", tmux_command=str(wrapper))
    try:
        runtime.ensure_window("run-123-spec-writer")
        assert runtime.exists()
        windows = subprocess.run(["tmux", "-L", socket, "list-windows", "-t", "agent-sys-test", "-F", "#W"],
                                 text=True, capture_output=True, check=True).stdout.splitlines()
        assert "run-123-spec-writer" in windows
    finally:
        subprocess.run(["tmux", "-L", socket, "kill-server"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def test_stage_process_runs_inside_owned_tmux_window(tmp_path: Path) -> None:
    socket = "agent_sys_stage_test"
    tmux = tmp_path / "tmux-wrapper"
    tmux.write_text(f"#!/usr/bin/env bash\nexec tmux -L {socket} \"$@\"\n", encoding="utf-8")
    tmux.chmod(tmux.stat().st_mode | stat.S_IXUSR)
    command = fake_codex(tmp_path, "printf 'desde tmux\\n'; exit 0\n")
    try:
        result = run_stage("probar etapa", runs_dir=tmp_path / "runs", codex_command=command,
                           tmux_command=str(tmux), tmux_session="agent-sys-stage-test",
                           timeout_seconds=5)
        assert result["status"] == "passed"
        assert "desde tmux" in result["stdout"]
    finally:
        subprocess.run(["tmux", "-L", socket, "kill-server"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def test_pipeline_stops_after_failed_stage(tmp_path: Path) -> None:
    command = fake_codex(tmp_path, "case=\"$*\"; [[ \"$case\" == *implementer* ]] && exit 7; exit 0\n")
    result = run_pipeline("ejecutar pipeline", runs_dir=tmp_path / "runs",
                          codex_command=command, use_tmux=False)
    run_dir = tmp_path / "runs" / result["run_id"]
    state = json.loads((run_dir / "run.json").read_text())
    assert result["status"] == "failed"
    assert state["stages"]["spec-writer"]["status"] == "passed"
    assert state["stages"]["implementer"]["status"] == "failed"
    assert state["stages"]["test-runner"]["status"] == "blocked"
    assert not (run_dir / "stages/test-runner/stdout.log").exists()
    assert any(json.loads(line)["type"] == "pipeline_stopped"
               for line in (run_dir / "events.jsonl").read_text().splitlines())


def test_pipeline_runs_all_declared_stages(tmp_path: Path) -> None:
    command = fake_codex(tmp_path, "exit 0\n")
    result = run_pipeline("ejecutar todo", runs_dir=tmp_path / "runs",
                          codex_command=command, use_tmux=False)
    state = json.loads((tmp_path / "runs" / result["run_id"] / "run.json").read_text())
    assert result["status"] == "passed"
    assert all(stage["status"] == "passed" for stage in state["stages"].values())
