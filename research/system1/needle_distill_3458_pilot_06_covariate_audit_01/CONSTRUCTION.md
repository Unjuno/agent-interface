# Construction checks — Issue #3892

No training or audit of the formal result occurred before freeze.

Local Docker Desktop image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64, network disabled, read-only root/source, 4 GiB memory and two CPUs:

- `python -m unittest -v`: 9/9 passed in 0.010s. The six-column mutation controls each rejected a changed feature; confidence/visibility and generator reconstruction controls passed.
- `python audit.py --self-test`: PASS; six shifted feature-column corruption cases rejected, unchanged vector accepted.

Nonfatal warning: the image has no NumPy, so Torch printed its optional NumPy-initialization warning. Neither audit nor tests use NumPy APIs.
