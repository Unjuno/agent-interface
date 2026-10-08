# Executed commands and first outcomes

D01: docker run --name timer-6067-linux-root-d01 --pull never --network none --read-only --cap-drop ALL --security-opt no-new-privileges --cpus 1 --memory 128m --memory-swap 128m --pids-limit 32 -e PYTHONDONTWRITEBYTECODE=1 -v /workspace/scratch/timer-diagnostic-6067-20261003-root:/source:ro -v /workspace/scratch/timer-diagnostic-6067-20261003-root:/output python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python /source/candidate.py /output/run-d01
Exit2: python: can't open file '/source/candidate.py': [Errno 13] Permission denied. Candidate0/auditor0. Owned directory0700/files0600; changed owned directory0755/files0644 and output0777 before D02. Root-mapping details remain unknown; only mount access failure is established.

D02: docker run --name timer-6067-linux-root-d02 --pull never --network none --read-only --cap-drop ALL --security-opt no-new-privileges --cpus 1 --memory 128m --memory-swap 128m --pids-limit 32 -e PYTHONDONTWRITEBYTECODE=1 -v /workspace/scratch/timer-diagnostic-6067-20261003-root:/source:ro -v /workspace/scratch/timer-diagnostic-6067-20261003-root/output:/output python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python /source/candidate.py /output/run-d02
Exit0. Docker inspect D01-container.json and D02-container.json retain actual start/finish/exit receipts. Both stopped. Candidate source unchanged. No consumed scientific allocation repeated.

python auditor.py output/run-d02: exit1 after checks, PermissionError writing output/run-d02/audit.json (container-owned directory). No audit result file produced. Preserved original auditor.py.
python auditor_v2.py output/run-d02 audit-v2.json: exit0; output-only destination repair, independent calculations unchanged. Raw not modified.

No CI/native cue acquisition invoked. Dedicated stopped containers hold no live input; they are retained locally for provenance. Image/source hashes and manifest readback retained.
