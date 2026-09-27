# Live identity allocation #2994

Allocation IDs:
- a1: stopped on missing `runtime.backends.x11_v1.capture_artifacts`
- a2: stopped on missing `PIL` after adding the exact main capture module
- a3: completed with the corrected Docker image

Final image: `agent-interface-2994:20260920`
Image digest: `sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c`
Network: `none`
Command:
```
docker run --rm --network none -v /tmp/agent-interface-2972:/repo:ro -v /tmp/lo2994-results-a3:/out agent-interface-2994:20260920 replacement_runner.py /out/allocation-a3
```

Final observations:
- useful control: real X11 dispatch completed, independent GTK effect and verified release were produced
- source mismatch: `STALE_BINDING`, native status `refused`, backend emissions `0`
- target replacement: original and replacement XIDs were both `2097155` because the X server reused the ID; dispatch completed against the replacement, so stale-target rejection was not demonstrated
- decision: `HOLD_IDENTITY_FAIL_CLOSED_NOT_PROVEN`

The a1/a2 failures are retained as infrastructure stop evidence, not merged into the final behavioral decision. No old result was edited or relabeled.

SHA-256:
- replacement_runner.py: `acfc4a2ba61018b20bfe98ebf176bc2c67dde8f40eeddc719f112dd044d82b84`
- Dockerfile: `ea8b5f827ed905c847f9b375d900814cbe7077f56ae80c36a1c529f1ba849975`
- capture_artifacts.py: `22f557ab45ae27a4c27e3c4f0c35a677a3fca82a48cbb3adda83e52384175e9a`
- a1 summary: `2462329f4b53e2aca80e750fc7e63e26f4cf8ec5f6804c0fe51ba395886d0de3`
- a2 summary: `de006a443713001743365d4620205db30e69253c8afd45ce0754eb925b5c00d2`
- a3 summary: `db59f509b1b5f92d16506a95c4373e38e685aa4e8e1022e1f8e997def3b49700`
