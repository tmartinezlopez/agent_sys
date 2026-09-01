#!/usr/bin/env bash
# Verificación local/CI sin llamadas al Codex real.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash -n "$root/scripts/pipeline"/*.sh "$root/tests"/*.sh
python3 -m py_compile "$root/scripts/pipeline"/*.py
for test in \
  contract-runtime.sh prompt-cache.sh token-budget.sh full-pipeline.sh operations-readonly.sh runtime-guard.sh \
  stop-run.sh operations-lifecycle.sh vertical-slice.sh installed-copy.sh; do
  bash "$root/tests/$test"
done
openspec validate --all --strict
echo "check-all: PASS"
