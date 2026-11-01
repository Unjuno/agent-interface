# Event lock fault injection r541

This is the same two-arm fault-injection question, setup, fixed order, one-second
observation, negative control and cleanup as r540, but uses `spawn` instead of
`fork` to match the draft's process creation method. Script is mounted read-only
inside the same Docker image (sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425)
with network disabled, one CPU, 1 GiB RAM and no image pull. Run exactly once.
The lock is directly held as a controlled failure injection, not evidence that
a natural child was killed inside Event.is_set. No GUI or user input is used.
