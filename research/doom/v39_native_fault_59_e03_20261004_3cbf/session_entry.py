"""Import custody instrumentation; invokes unchanged native session main once."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args, remaining = parser.parse_known_args()
    source = args.source.resolve()
    namespace = runpy.run_path(str(source / 'research/doom/session_map01_v12.py'),
                              run_name='e03_instrumented_session')
    loaded = []
    for name, module in sorted(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if path is None:
            continue
        path = Path(path).resolve()
        if path.is_relative_to(source):
            loaded.append({'module': name, 'path': str(path.relative_to(source)),
                           'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    backend = namespace['Backend']
    receipt = {'loaded': loaded, 'backend_module': backend.__module__,
               'session_sha256': hashlib.sha256((source / 'research/doom/session_map01_v12.py').read_bytes()).hexdigest(),
               'scope': 'actual imported module paths and file bytes before unchanged session main; not authenticated loaded machine code'}
    args.receipt.write_text(json.dumps(receipt, sort_keys=True) + '\n')
    sys.argv = [str(source / 'research/doom/session_map01_v12.py'), *remaining]
    namespace['main']()


if __name__ == '__main__':
    main()
