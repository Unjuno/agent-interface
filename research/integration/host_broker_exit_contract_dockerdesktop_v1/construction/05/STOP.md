# Construction 05 — Docker Desktop engine 29.8.0 import-path STOP

Classification: `STOP_CONSTRUCTION_IMPORT_PATH`; formal cases run: 0.

This excluded construction-only invocation used the cached pinned Python image, Docker Desktop context `desktop-linux`, engine `29.8.0 linux/x86_64`, `--network none`, a read-only root filesystem, read-only study/runtime mounts, bounded resources, dropped capabilities, and `no-new-privileges`. The container was created, inspected, and removed after evidence capture. Before running any fake child or broker, `construction_probe.py` imported `test_contract.py`, whose fallback default eagerly evaluates `Path(__file__).resolve().parents[3]`; with the study mounted at `/study`, this raised `IndexError: 3`.

No broker invocation, fake executable invocation, provider/model call, GUI, or formal case occurred. The formal allocations 01 and 02 are unchanged and untouched. Preserve this failed construction attempt; do not retry it under the same attempt identity. Any further construction must use a fresh path and an independent probe that does not import the formal runner.
