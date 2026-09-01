# Actualizar la metodología instalada

## 1. Cambiar la copia maestra

Los cambios se realizan en el checkout de `agent_sys`, se prueban con
`bash tests/check-all.sh` y se validan con:

```bash
openspec validate --all --strict
```

No se deben modificar manualmente las copias `metodologia/` de los proyectos.

## 2. Propagar el cambio

Desde la raíz de cada proyecto consumidor:

```bash
metodologia/scripts/pipeline/methodology-update.sh --project "$PWD"
```

El comando usa `metodologia/.config/source-path`, actualiza únicamente los
archivos de la metodología y conserva la configuración del proyecto.

Si esa ruta no existe, configurarla una sola vez:

```bash
metodologia/scripts/pipeline/methodology-configure.sh \
  --project "$PWD" --source /ruta/agent_sys
```

## 3. Validar y registrar

```bash
PIPELINE_REPO_ROOT="$PWD" \
PIPELINE_SCRIPT_DIR="$PWD/metodologia/scripts/pipeline" \
metodologia/scripts/pipeline/preflight.sh --worktree "$PWD"
bash metodologia/tests/check-all.sh
git diff -- metodologia
git add metodologia
git commit -m "Actualiza la metodología"
```

Si la validación falla, no se usa esa copia: se revisa el diff y se corrige la
copia maestra antes de repetir la actualización.
