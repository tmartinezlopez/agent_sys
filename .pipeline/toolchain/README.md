# Toolchain declarativo

Este directorio contiene contratos versionados por área del proyecto. Cada
fichero `*.sh` puede definir `root`, `prepare`, `lint`, `typecheck`,
`test_targeted`, `test_full` y `build`.

El runtime sourceará cada área en un subshell aislado. La ausencia de una
función equivale a no-op. El estado efímero de runs vive en `.pipeline/runs/`
y permanece ignorado por Git.
