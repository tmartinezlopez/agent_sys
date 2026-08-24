"""Entrada del coordinador para el primer pipeline."""

import argparse
import json
from pathlib import Path

from .operations import inspect_run, read_logs, status_runs
from .pipeline import resume_run, run_once, run_pipeline, run_stage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sistema de agentes")
    parser.add_argument("prompt", nargs="?", help="Texto de entrada")
    parser.add_argument("--run", action="store_true", help="Ejecutar el prompt mediante Codex")
    parser.add_argument("--stage", choices=("spec-writer", "implementer", "test-runner", "reviewer", "ui-reviewer", "qa"),
                        help="Ejecutar una etapa declarada del pipeline")
    parser.add_argument("--pipeline", action="store_true", help="Ejecutar las seis etapas en orden")
    parser.add_argument("--gate", choices=("spec-review",), help="Operar un gate humano pendiente")
    parser.add_argument("--status", action="store_true", help="Consultar el estado de uno o todos los runs")
    parser.add_argument("--logs", action="store_true", help="Consultar los eventos de un run")
    parser.add_argument("--inspect", action="store_true", help="Inspeccionar el estado y artefactos de un run")
    parser.add_argument("--decision", choices=("approve", "reject"))
    parser.add_argument("--operator", help="Identidad del operador del gate")
    parser.add_argument("--reason", help="Motivo de la decisión del gate")
    parser.add_argument("--no-tmux", action="store_true", help="Solo para pruebas del runtime")
    parser.add_argument("--tmux-session", default="agent-sys")
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    parser.add_argument("--run-id")
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--model")
    parser.add_argument("--profile")
    parser.add_argument("--sandbox", default="read-only")
    parser.add_argument("--cd", dest="working_directory", type=Path)
    parser.add_argument("--timeout", type=float, default=300)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    query_operations = sum((args.status, args.logs, args.inspect))
    if query_operations > 1:
        raise SystemExit("--status, --logs y --inspect son operaciones excluyentes")
    if args.status:
        if args.prompt or args.run or args.stage or args.pipeline or args.gate:
            raise SystemExit("--status no admite una operación de ejecución")
        print(json.dumps(status_runs(args.runs_dir, args.run_id), ensure_ascii=False, indent=2))
        return
    if args.logs:
        if not args.run_id:
            raise SystemExit("--logs requiere --run-id")
        print(json.dumps(read_logs(args.runs_dir, args.run_id), ensure_ascii=False, indent=2))
        return
    if args.inspect:
        if not args.run_id:
            raise SystemExit("--inspect requiere --run-id")
        print(json.dumps(inspect_run(args.runs_dir, args.run_id), ensure_ascii=False, indent=2))
        return
    if args.gate:
        if not args.run_id or not args.decision or not args.operator:
            raise SystemExit("--gate requiere --run-id, --decision y --operator")
        result = resume_run(args.run_id, runs_dir=args.runs_dir, decision=args.decision,
                            operator=args.operator, reason=args.reason,
                            codex_command=args.codex_command, profile=args.profile,
                            working_directory=args.working_directory,
                            timeout_seconds=args.timeout, tmux_session=args.tmux_session,
                            use_tmux=not args.no_tmux)
        print(f"{result['status']}: {result['run_id']}")
        raise SystemExit(0 if result["status"] == "passed" else 1)
    if args.pipeline:
        if not args.prompt:
            raise SystemExit("--pipeline requiere un objetivo")
        result = run_pipeline(args.prompt, runs_dir=args.runs_dir,
                              codex_command=args.codex_command, profile=args.profile,
                              working_directory=args.working_directory,
                              timeout_seconds=args.timeout, tmux_session=args.tmux_session,
                              use_tmux=not args.no_tmux)
        print(f"{result['status']}: {result['run_id']}")
        raise SystemExit(0 if result["status"] == "passed" else 1)
    if args.stage:
        if not args.prompt:
            raise SystemExit("--stage requiere un objetivo")
        result = run_stage(args.prompt, role=args.stage, runs_dir=args.runs_dir,
                           run_id=args.run_id, codex_command=args.codex_command,
                           profile=args.profile, working_directory=args.working_directory,
                           timeout_seconds=args.timeout, tmux_session=args.tmux_session,
                           use_tmux=not args.no_tmux)
        print(f"{result['status']}: {result['run_id']}")
        raise SystemExit(0 if result["status"] == "passed" else 1)
    if args.run:
        if not args.prompt:
            raise SystemExit("--run requiere un prompt")
        result = run_once(
            args.prompt,
            runs_dir=args.runs_dir,
            run_id=args.run_id,
            codex_command=args.codex_command,
            model=args.model,
            profile=args.profile,
            sandbox=args.sandbox,
            working_directory=args.working_directory,
            timeout_seconds=args.timeout,
        )
        print(f"{result['status']}: {result['run_id']}")
        raise SystemExit(0 if result["status"] == "passed" else 1)
    if args.prompt:
        print(f"Entrada recibida: {args.prompt}")
    else:
        print("agent_sys está preparado para comenzar")


if __name__ == "__main__":
    main()
