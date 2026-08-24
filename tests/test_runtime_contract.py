import json
import shutil
import stat
import subprocess
from pathlib import Path

from agent_sys.contracts import ROLE_CATALOG, STAGES, predecessor_for, role_config
from agent_sys.ledger import RunLedger
from agent_sys.launcher import build_command
from agent_sys.pipeline import run_pipeline, run_stage
from agent_sys.spec_writer import build_prompt, change_name_for_run
from agent_sys import test_runner
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


def test_spec_writer_prompt_is_specific() -> None:
    prompt = build_prompt("definir autenticacion", "run-123")
    assert "openspec new change" in prompt
    assert "AGENT_SYS_CHANGE: agent-sys-run-123" in prompt
    assert "rol generico" in prompt
    assert role_config("spec-writer").required_artifacts[-1] == "specs/*.md"
    assert change_name_for_run("RUN-123") == "agent-sys-run-123"


def test_implementer_requires_spec_writer_handoff(tmp_path: Path) -> None:
    command = fake_codex(tmp_path, "touch should-not-run; exit 0\n")
    result = run_stage("implementar", role="implementer", run_id="no-handoff",
                       runs_dir=tmp_path / "runs", codex_command=command, use_tmux=False)
    assert result["status"] == "blocked"
    assert result["reason"] == "spec-writer no está en estado passed"
    assert not (tmp_path / "should-not-run").exists()


def test_test_runner_prompt_is_read_only() -> None:
    prompt = test_runner.build_prompt("validar", {"git_root": "/tmp/project",
                                                   "change_name": "agent-sys-x"})
    assert "PYTHONPATH=src pytest -q" in prompt
    assert "No modifiques" in prompt
    assert role_config("test-runner").sandbox == "read-only"


def test_test_runner_requires_implementer_handoff(tmp_path: Path) -> None:
    command = fake_codex(tmp_path, "touch should-not-run; exit 0\n")
    result = run_stage("probar", role="test-runner", run_id="no-implementer",
                       runs_dir=tmp_path / "runs", codex_command=command, use_tmux=False)
    assert result["status"] == "blocked"
    assert result["reason"] == "implementer no está en estado passed"
    assert not (tmp_path / "should-not-run").exists()


def test_launcher_records_real_role_flags() -> None:
    command = build_command(role_config("reviewer"), "revisa esto", working_directory=Path("/tmp"))
    assert command[:6] == ["codex", "exec", "--json", "--sandbox", "read-only", "--model"]
    assert "gpt-5.6-luna" in command
    assert "model_reasoning_effort=medium" in command
    assert command[-2:] == ["--cd", "/tmp"] or command[-1] == "revisa esto"


def test_stage_persists_contract_and_can_be_reloaded(tmp_path: Path) -> None:
    name = "agent-sys-persist-run"
    project = prepare_valid_change(tmp_path, name)
    command = fake_codex(tmp_path, f"printf 'AGENT_SYS_CHANGE: {name}\\n'; exit 0\n")
    result = run_stage("crear una especificacion", runs_dir=tmp_path / "runs",
                       run_id="persist-run", codex_command=command,
                       working_directory=project, use_tmux=False)
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
    name = "agent-sys-tmux-run"
    project = prepare_valid_change(tmp_path, name)
    command = fake_codex(tmp_path, f"printf 'AGENT_SYS_CHANGE: {name}\\n'; printf 'desde tmux\\n'; exit 0\n")
    try:
        result = run_stage("probar etapa", run_id="tmux-run", runs_dir=tmp_path / "runs", codex_command=command,
                           working_directory=project,
                           tmux_command=str(tmux), tmux_session="agent-sys-stage-test",
                           timeout_seconds=5)
        assert result["status"] == "passed"
        assert "desde tmux" in result["stdout"]
    finally:
        subprocess.run(["tmux", "-L", socket, "kill-server"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def prepare_valid_change(tmp_path: Path, name: str) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(["openspec", "init", "--tools", "codex", "--no-animation",
                    "--no-copilot-cloud", str(project)], check=True,
                   stdout=subprocess.DEVNULL)
    subprocess.run(["git", "init", "-b", "main", str(project)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    source = Path(__file__).parents[1] / "openspec/changes/spec-writer-stage"
    target = project / "openspec/changes" / name
    shutil.copytree(source, target)
    return project


def prepare_valid_project(tmp_path: Path) -> Path:
    project = tmp_path / "pipeline-project"
    project.mkdir()
    subprocess.run(["openspec", "init", "--tools", "codex", "--no-animation",
                    "--no-copilot-cloud", str(project)], check=True,
                   stdout=subprocess.DEVNULL)
    subprocess.run(["git", "init", "-b", "main", str(project)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / "tests/test_generated.py").write_text("def test_generated():\n    assert True\n")
    return project


def test_spec_writer_requires_validated_handoff(tmp_path: Path) -> None:
    name = "agent-sys-test-run"
    project = prepare_valid_change(tmp_path, name)
    command = fake_codex(tmp_path, f"printf 'AGENT_SYS_CHANGE: {name}\\n'; exit 0\n")
    result = run_stage("definir autenticacion", role="spec-writer", run_id="test-run",
                       runs_dir=tmp_path / "runs", codex_command=command,
                       working_directory=project, use_tmux=False)
    stage_dir = tmp_path / "runs/test-run/stages/spec-writer"
    document = json.loads((stage_dir / "result.json").read_text())
    assert result["status"] == "passed"
    assert document["change_name"] == name
    assert document["validation_exit_code"] == 0
    assert (stage_dir / "validation.stdout.log").exists()


def test_spec_writer_rejects_missing_artifact(tmp_path: Path) -> None:
    name = "agent-sys-bad-run"
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(["openspec", "init", "--tools", "codex", "--no-animation",
                    "--no-copilot-cloud", str(project)], check=True,
                   stdout=subprocess.DEVNULL)
    change_dir = project / "openspec/changes" / name
    change_dir.mkdir(parents=True)
    (change_dir / "proposal.md").write_text("incompleto\n")
    command = fake_codex(tmp_path, f"printf 'AGENT_SYS_CHANGE: {name}\\n'; exit 0\n")
    result = run_stage("objetivo incompleto", role="spec-writer", run_id="bad-run",
                       runs_dir=tmp_path / "runs", codex_command=command,
                       working_directory=project, use_tmux=False)
    document = json.loads((tmp_path / "runs/bad-run/stages/spec-writer/result.json").read_text())
    assert result["status"] == "failed"
    assert document["error"] == "faltan artefactos OpenSpec"


def test_spec_writer_rejects_failed_strict_validation(tmp_path: Path) -> None:
    name = "agent-sys-invalid-run"
    project = prepare_valid_change(tmp_path, name)
    spec_path = project / "openspec/changes" / name / "specs/spec-writer-stage/spec.md"
    spec_path.write_text(spec_path.read_text().replace("#### Scenario:", "### Scenario:"))
    command = fake_codex(tmp_path, f"printf 'AGENT_SYS_CHANGE: {name}\\n'; exit 0\n")
    result = run_stage("objetivo invalido", role="spec-writer", run_id="invalid-run",
                       runs_dir=tmp_path / "runs", codex_command=command,
                       working_directory=project, use_tmux=False)
    document = json.loads((tmp_path / "runs/invalid-run/stages/spec-writer/result.json").read_text())
    assert result["status"] == "failed"
    assert document["validation_exit_code"] != 0
    assert (tmp_path / "runs/invalid-run/stages/spec-writer/validation.stderr.log").exists()


def test_pipeline_stops_after_failed_stage(tmp_path: Path) -> None:
    project = prepare_valid_project(tmp_path)
    source = Path(__file__).parents[1] / "openspec/changes/spec-writer-stage"
    command = fake_codex(tmp_path, f"prompt=\"$*\"; name=$(printf '%s' \"$prompt\" | sed -n 's/.*Nombre exacto del change: \\([^ ]*\\).*/\\1/p'); "
                         f"mkdir -p openspec/changes/$name; cp -r {source}/proposal.md {source}/design.md {source}/tasks.md openspec/changes/$name/; cp -r {source}/specs openspec/changes/$name/; "
                         "[[ \"$prompt\" == *implementer* ]] && exit 7; printf 'AGENT_SYS_CHANGE: %s\\n' \"$name\"; exit 0\n")
    result = run_pipeline("ejecutar pipeline", runs_dir=tmp_path / "runs",
                          codex_command=command, working_directory=project, use_tmux=False)
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
    project = prepare_valid_project(tmp_path)
    source = Path(__file__).parents[1] / "openspec/changes/spec-writer-stage"
    command = fake_codex(tmp_path, f"prompt=\"$*\"; name=$(printf '%s' \"$prompt\" | sed -n 's/.*Nombre exacto del change: \\([^ ]*\\).*/\\1/p'); "
                         f"if [[ -n \"$name\" ]]; then mkdir -p openspec/changes/$name; cp -r {source}/proposal.md {source}/design.md {source}/tasks.md openspec/changes/$name/; cp -r {source}/specs openspec/changes/$name/; printf 'AGENT_SYS_CHANGE: %s\\n' \"$name\"; else printf 'implementado\\n' > implementado.txt; fi; exit 0\n")
    result = run_pipeline("ejecutar todo", runs_dir=tmp_path / "runs",
                          codex_command=command, working_directory=project, use_tmux=False)
    state = json.loads((tmp_path / "runs" / result["run_id"] / "run.json").read_text())
    assert result["status"] == "passed"
    assert all(stage["status"] == "passed" for stage in state["stages"].values())
    implementer = state["stages"]["implementer"]
    assert implementer["tasks_file"].endswith("tasks.md")
    assert implementer["change_name"].startswith("agent-sys-")
    assert (project / "implementado.txt").read_text() == "implementado\n"


def test_implementer_stops_on_post_validation_failure(tmp_path: Path) -> None:
    project = prepare_valid_project(tmp_path)
    source = Path(__file__).parents[1] / "openspec/changes/spec-writer-stage"
    command = fake_codex(tmp_path, f"prompt=\"$*\"; name=$(printf '%s' \"$prompt\" | sed -n 's/.*Nombre exacto del change: \\([^ ]*\\).*/\\1/p'); "
                         f"if [[ -n \"$name\" ]]; then mkdir -p openspec/changes/$name; cp -r {source}/proposal.md {source}/design.md {source}/tasks.md openspec/changes/$name/; cp -r {source}/specs openspec/changes/$name/; printf 'AGENT_SYS_CHANGE: %s\\n' \"$name\"; "
                         "else printf 'implementado\\n' > implementado.txt; spec=$(find openspec/changes -name spec.md | head -1); sed -i 's/^#### Scenario:/### Scenario:/' \"$spec\"; fi; exit 0\n")
    result = run_pipeline("invalidar implementacion", runs_dir=tmp_path / "runs",
                          codex_command=command, working_directory=project,
                          use_tmux=False, stages=("spec-writer", "implementer"))
    assert result["status"] == "failed"
    assert result["stopped_at"] == "implementer"


def test_test_runner_records_pass_fail_and_timeout(tmp_path: Path, monkeypatch) -> None:
    project = prepare_valid_project(tmp_path)
    stage_dir = tmp_path / "stage"
    passing = test_runner.execute_tests(stage_dir, project, timeout_seconds=5)
    assert passing["valid"] is True
    assert passing["exit_code"] == 0
    (project / "tests/test_generated.py").write_text("def test_generated():\n    assert False\n")
    failing = test_runner.execute_tests(stage_dir, project, timeout_seconds=5)
    assert failing["valid"] is False
    assert failing["exit_code"] != 0
    monkeypatch.setattr(test_runner, "TEST_COMMAND", ["bash", "-c", "sleep 1"])
    timed_out = test_runner.execute_tests(stage_dir, project, timeout_seconds=0.01)
    assert timed_out["valid"] is False
    assert timed_out["exit_code"] == 124


def test_pipeline_stops_after_test_failure(tmp_path: Path) -> None:
    project = prepare_valid_project(tmp_path)
    source = Path(__file__).parents[1] / "openspec/changes/spec-writer-stage"
    command = fake_codex(tmp_path, f"prompt=\"$*\"; name=$(printf '%s' \"$prompt\" | sed -n 's/.*Nombre exacto del change: \\([^ ]*\\).*/\\1/p'); "
                         f"if [[ -n \"$name\" ]]; then mkdir -p openspec/changes/$name; cp -r {source}/proposal.md {source}/design.md {source}/tasks.md openspec/changes/$name/; cp -r {source}/specs openspec/changes/$name/; printf 'AGENT_SYS_CHANGE: %s\\n' \"$name\"; "
                         "elif [[ \"$prompt\" == *test-runner* ]]; then printf 'def test_generated():\\n    assert False\\n' > tests/test_generated.py; else printf 'implementado\\n' > implementado.txt; fi; exit 0\n")
    result = run_pipeline("fallar pruebas", runs_dir=tmp_path / "runs",
                          codex_command=command, working_directory=project,
                          use_tmux=False)
    state = json.loads((tmp_path / "runs" / result["run_id"] / "run.json").read_text())
    assert result["status"] == "failed"
    assert result["stopped_at"] == "test-runner"
    assert state["stages"]["reviewer"]["status"] == "blocked"
