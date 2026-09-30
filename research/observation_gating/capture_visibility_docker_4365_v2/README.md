# Docker capture-visibility successor (#4835)

New allocation after the fixture prerequisite STOP in #4827. Preserves all prior evidence unchanged. The fixture collects mapped child state, `win_class`, and geometry using Python-Xlib's verified reply fields rather than assuming a `class` attribute exists. See `FREEZE.md` for H/T/D/C/U, gates and pinned local Docker image.

Construction and formal experiments run locally inside Docker with network disabled. CI/workflows are not experiment runners.
