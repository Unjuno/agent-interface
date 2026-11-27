# Current-main Calc public composition rerun

This packet records a read-only-source Docker rerun of the existing current
main provider-to-public-Calc composition module, in normal and optimized Python.
It supports the offline seam crosswalk in the parent directory; it is not a new
live Calc attempt or a replay of archived G10.

## Result

- Source: `bd5f574e8bfda33deca5117d6f2bd2709edd8016` (current main after PR
  #10193).
- Image: `agent-interface-xvfb-mcp:late-input-r19`,
  `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`.
- Network disabled; source mounted read-only; evidence directory mounted
  read-write; 2 CPUs, 4 GiB memory+swap total, 256 PIDs; `--rm` container.
- `test_mcp_endpoint_composition.py`: 16/16 pass in normal mode (18.427 s)
  and 16/16 under `python -O` (18.248 s). Docker exit 0.
- The module includes the synthetic provider-wait → stale-refusal → fresh
  registered Calc call → verified close → independent FODS score path. The
  model/provider and GUI are fixtures in this test; these results do not supply
  live token accounting, a new allocation, WSLc/MAP01 evidence, or efficiency
  and reliability estimates.

`conditions.json` and `command.txt` define the run; `run.sh`, per-mode logs,
container output, exit files and `docker-runtime-after.json` preserve the raw
result and post-run engine state. `g10-live-summary.json` and
`source-diff.txt` are read-only extracts from the retained G10 Git blobs and
current-main source comparison. `SHA256SUMS.txt` covers each packet member
except itself.
