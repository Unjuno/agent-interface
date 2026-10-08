"""Import-only construction check. Never construct a server or invoke a tool."""
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import sys
import traceback

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'preflight-01'


def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / 'upstream').rglob('*.py'))}


def main():
    OUT.mkdir(exist_ok=False)
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    before = hashes()
    save('START.json', {'affinity': sorted(os.sched_getaffinity(0)),
        'rlimit_as': resource.getrlimit(resource.RLIMIT_AS),
        'rlimit_cpu': resource.getrlimit(resource.RLIMIT_CPU),
        'source_before': before, 'server_creations': 0, 'public_calls': 0})
    result = {'status': 'STOP_IMPORT', 'server_creations': 0, 'public_calls': 0}
    try:
        sys.path.insert(0, str(ROOT / 'upstream'))
        module = importlib.import_module('runtime.cli_v1.mcp_server')
        if Path(module.__file__).resolve() != ROOT / 'upstream/runtime/cli_v1/mcp_server.py':
            raise RuntimeError('wrong module origin')
        loaded = {}
        for name, mod in sorted(sys.modules.items()):
            path = getattr(mod, '__file__', None)
            if path and Path(path).is_file():
                p = Path(path).resolve()
                loaded[name] = {'path': str(p), 'bytes': p.stat().st_size,
                    'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        result.update(status='PASS_IMPORT_ONLY', python=sys.version,
            versions={n: importlib.metadata.version(n) for n in ('mcp', 'pydantic', 'pydantic-core', 'anyio')},
            loaded_files=loaded)
    except BaseException as error:
        result.update(error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    finally:
        result.update(source_after=hashes(), source_unchanged=before == hashes(),
            ru_maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save('RESULT.json', result)
    return 0 if result['status'] == 'PASS_IMPORT_ONLY' and result['source_unchanged'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
