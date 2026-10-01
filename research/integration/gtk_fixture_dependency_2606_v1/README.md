# GTK fixture dependency diagnosis (#2741)

This additive successor isolates the fixture startup failure from #2606. It
does not rerun the eight-case allocation.

## Local Docker result

Image: `codex-gtk-model:local` (the existing local image used for the #2606
attempt). The exact main fixture entrypoint was run once under private Xvfb
`:144` with no input, model, provider, or network call:

```text
EXIT=1
ModuleNotFoundError: No module named 'gi'
```

The fixture therefore exits before writing `meta.json`, explaining the formal
runner's `useful fixture timeout`. Decision:
`PASS_GTK_FIXTURE_DEPENDENCY_DIAGNOSIS`. This identifies the missing PyGObject
dependency; installing it and rerunning a fresh, immutably frozen allocation
remain separate work. No #2606 result is reinterpreted.
