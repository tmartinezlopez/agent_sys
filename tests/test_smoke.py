from agent_sys import __version__
from agent_sys.cli import build_parser


def test_version_exists() -> None:
    assert __version__ == "0.1.0"


def test_cli_accepts_prompt() -> None:
    args = build_parser().parse_args(["hola"])
    assert args.prompt == "hola"

