"""Restore and run only the historical read-only verifier; no live/candidate run."""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
from unpack import ROOT, restore

def main() -> int:
    with tempfile.TemporaryDirectory(prefix='r4m8-readonly-') as temp:
        out = Path(temp) / 'retained'
        report = restore(out)
        readable = sorted((ROOT / 'original').rglob('*'))
        for path in readable:
            if path.is_file() and path.read_bytes() != (out / path.relative_to(ROOT / 'original')).read_bytes():
                raise ValueError('readable copy mismatch')
        result = subprocess.run([sys.executable, '-B', 'verify_readonly.py'], cwd=out,
                                capture_output=True, timeout=40, check=False)
        expected = (ROOT / 'REVALIDATION.json').read_bytes()
        if result.returncode != 0 or result.stderr or result.stdout != expected:
            raise ValueError('original read-only verification mismatch')
        report.update(decision='PASS_COMPLETE_RETAINED_PUBLICATION_LOCAL',
                      original=json.loads(result.stdout),
                      readable_copies=sum(p.is_file() for p in readable),
                      new_gui_trials=0, new_finite_candidate_invocations=0)
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
