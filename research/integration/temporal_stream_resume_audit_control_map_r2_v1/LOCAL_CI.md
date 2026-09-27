# Local CI for #4926

Run after both frozen Docker allocations and before evidence delivery, using the same pinned image and networkless/read-only policy as construction 01.

Command: `docker run --rm --pull=never --platform linux/amd64 --network none --read-only --cpus=1 --memory=1g --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,noexec,size=16m -v <study-path>:/study:ro --entrypoint python sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419 -B -S -m unittest discover -s /study -p test_contract.py -v`

Exit code 0; 4/4 contract tests passed. No historical evidence is needed by this CI command. The formal auditor's independent corruption controls also rejected 8/8 controls in its separate Docker invocation.
