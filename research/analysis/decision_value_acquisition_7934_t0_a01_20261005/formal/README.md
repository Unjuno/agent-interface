# A01 formal outputs

`terminal.json` is the terminal disposition. The frozen one-launch WSLc
execution ran the simulator once and the independent auditor once; the auditor
returned exit 1 with the single recorded error `profile_choice_matrix`.

The exact large files are preserved both locally as
`raw_observations.jsonl` / `candidate_result.json` and as gzip transport
artifacts. When publishing through GitHub MCP, use the `.gz` files plus
`FORMAL_MANIFEST.json`; reconstruct and verify byte length/SHA-256 before
independent analysis. The stdout, stderr, independent audit, and terminal JSON
files are plain UTF-8 evidence.
