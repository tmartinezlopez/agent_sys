"""Entrada del coordinador para el primer pipeline."""

import argparse
from pathlib import Path

from .pipeline import run_once


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sistema de agentes")
    parser.add_argument("prompt", nargs="?", help="Texto de entrada")
    parser.add_argument("--run", action="store_true", help="Ejecutar el prompt mediante Codex")
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
