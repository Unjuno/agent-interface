# Allocation 03 environment and exact commands

- Frozen repository commit: `d077494b50341f638e6d66f63e817ec48923768d`.
- Host: WSL2 Linux `6.18.40.1-microsoft-standard-WSL2`, Ubuntu 24.04.4 LTS x86_64.
- Python: CPython 3.12.3; python-xlib 0.33; Xvfb provisioned by `xvfb-run`.
- GUI fixture: repository `runtime.backends.x11_v1.fixture_app`, isolated temporary metadata/effect paths; one private Xvfb (`800x600x24`), no real desktop window.
- Docker Desktop last observed at context `desktop-linux`, server 28.5.1 linux/amd64, empty `docker ps`. #5085 explicitly retains/coordinates shared lanes and no lease was granted to this run; no container/image was started or inspected for the formal experiment.
- Preformal: auditor/record assembly construction tests 10/10; no-input Xvfb/Tk preflight reported a 32-byte keymap and 0 backend emissions.

Formal command (one invocation):

```sh
xvfb-run -a -s "-screen 0 800x600x24" env PYTHONPATH=/mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001_v3 python3 /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001_v3/experiment.py --formal /tmp/agent-interface-2437-backend-restart-d077494b-v3-20261001/RAW.json
```

Candidate exit: 0. Raw length: 2,144 bytes. One separate auditor command (one invocation):

```sh
python3 /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_2437_backend_restart_20261001_v3/experiment.py --audit /tmp/agent-interface-2437-backend-restart-d077494b-v3-20261001/RAW.json --receipt /tmp/agent-interface-2437-backend-restart-d077494b-v3-20261001/AUDIT.json
```

Auditor receipt: `FAIL_BACKEND_RESTART_STALE_REQUEST_ADMITTED`, `errors=[]`, raw SHA-256 `375a41d1d7489dbbc9305d4d8fe58a36212fa066928b509d3af8e47dc0a7e4ef`. No retry. Post-audit transport reads, if any, are only opaque byte-copy operations for Git publication; no second interpretation or raw hash pass is performed.
