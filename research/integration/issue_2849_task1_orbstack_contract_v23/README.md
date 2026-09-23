# Issue #2849 OrbStack nested bind-mount probe v23

Seed 284923 tests only whether the pinned nested image can read one preregistered fixture through a host path bind when Docker is invoked inside the pinned outer container over the OrbStack socket. Both containers use `--network none`; the nested bind is read-only.

No task runtime, model broker, Codex CLI, model runner, or task allocation is started.
