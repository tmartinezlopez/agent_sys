#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"
PYTHONPATH="${project_root}/src${PYTHONPATH:+:${PYTHONPATH}}" exec python3 -m agent_sys.cli "$@"
