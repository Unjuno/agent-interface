#!/usr/bin/env python3
"""Mount-only probe. Never imports or invokes the frozen candidate/auditor."""
import json
import pathlib
import sys

role = sys.argv[1]
expected = set(sys.argv[2:])
seen = {p.name for p in pathlib.Path('/src').iterdir() if p.is_file()}
if seen != expected:
    raise SystemExit('source allowlist mismatch: ' + repr(sorted(seen ^ expected)))
readable = all((pathlib.Path('/src') / name).read_bytes() for name in expected if name != 'preflight_probe.py')
rejected = False
try:
    (pathlib.Path('/src') / 'preflight_probe.py').write_text('forbidden', encoding='utf-8')
except OSError:
    rejected = True
out = pathlib.Path('/out') / 'probe.txt'
out.write_text('output-mount-writable\n', encoding='utf-8')
output_ok = out.read_text(encoding='utf-8').strip() == 'output-mount-writable'
result = {'role': role, 'allowlist_exact': seen == expected, 'source_read': readable,
          'source_write_rejected': rejected, 'output_write_readback': output_ok}
print(json.dumps(result, sort_keys=True))
if not all(result.values()):
    raise SystemExit(1)
