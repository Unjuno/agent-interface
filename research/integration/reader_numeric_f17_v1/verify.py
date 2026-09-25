"""Re-audit immutable historical bytes, not a new CLI measurement."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unpack import restore

ROOT = Path(__file__).resolve().parent

def verify():
    if sys.version_info[:2] != (3, 13):
        raise ValueError('This historical auditor requires Python 3.13')
    with tempfile.TemporaryDirectory(prefix='reader-f17-review-') as temp:
        destination = Path(temp)/'retained'
        count = restore(destination)
        freeze = json.loads((destination/'FREEZE.json').read_text())
        for name, digest in freeze['files'].items():
            if hashlib.sha256((destination/name).read_bytes()).hexdigest() != digest:
                raise ValueError('frozen source mismatch: '+name)
            if (ROOT/name).read_bytes() != (destination/name).read_bytes():
                raise ValueError('readable source differs from retained source: '+name)
        if (ROOT/'FREEZE.json').read_bytes() != (destination/'FREEZE.json').read_bytes():
            raise ValueError('freeze publication mismatch')
        snapshot = {str(p.relative_to(destination)):p.read_bytes() for p in destination.rglob('*') if p.is_file()}
        spec = importlib.util.spec_from_file_location('retained_f17_audit', destination/'audit.py')
        auditor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auditor)
        # audit.py compares historical argv with sys.executable. Supply only the
        # recorded executable string in that module's historical-identity context.
        # The actual current interpreter is unchanged; no actor/CLI is launched.
        recorded = json.loads((destination/'ENVIRONMENT.json').read_text())['executable']
        auditor.sys = SimpleNamespace(executable=recorded)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = auditor.main(destination/'formal')
        raw = output.getvalue().encode()
        if code != 0 or raw != (destination/'AUDIT.json').read_bytes():
            raise ValueError('historical audit output differs')
        after = {str(p.relative_to(destination)):p.read_bytes() for p in destination.rglob('*') if p.is_file()}
        if snapshot != after:
            raise ValueError('retained bytes changed during review; use Python -B')
        result = {'status':'PASS_READONLY_RECONSTRUCTION', 'restored_files':count,
                  'freeze_members':len(freeze['files']), 'audit_byte_exact':True,
                  'retained_files_unchanged':True, 'new_cli_measurements':0,
                  'audit_sha256':hashlib.sha256(raw).hexdigest(),
                  'recorded_executable_context':recorded,
                  'actual_review_executable':sys.executable}
        return result

if __name__ == '__main__':
    print(json.dumps(verify(), sort_keys=True))
