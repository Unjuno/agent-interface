# X11 backend conformance v0

Research Preview integration lane. This is a real private X11/XTEST backend experiment stacked on the portable semantic contract from PR #97. It is not the promoted runtime and does not imply Windows/macOS/Wayland support.

The backend separates admission, XTEST emission, fixture-observed effects, capture evidence and physical terminal release. The fixture ledger is not consulted by the backend during execution.

Reproduction after checking out the stacked dependency:

```bash
python3 -m unittest discover -s research/runtime_backend_x11_v0 -p 'test_*.py' -v
python3 research/runtime_backend_x11_v0/run_private_x11.py --out /tmp/x11-backend-v0
```
