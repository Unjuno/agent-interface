"""Run the repaired test's origin assertions in real isolated archive imports."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

root, output = map(lambda value: Path(value).resolve(), sys.argv[1:3])
output.mkdir(parents=True, exist_ok=False)
test_path = root / 'runtime/guarded_x11_v1/test_archive.py'
test_raw = test_path.read_bytes()
test_ast = ast.parse(test_raw)
child_code = next(node.value.value for node in ast.walk(test_ast)
                  if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'code' for t in node.targets))
child_ast = ast.parse(child_code)
origin_asserts = {}
prefix = []
for node in child_ast.body:
    if isinstance(node, ast.Assert):
        text = ast.unparse(node)
        for module in ('bridge', 'compiled'):
            if module + '.__file__' in text:
                origin_asserts[module] = text
    elif not origin_asserts:
        prefix.append(ast.unparse(node))
assert set(origin_asserts) == {'bridge', 'compiled'}
spec = importlib.util.spec_from_file_location('archive_builder', root / 'runtime/distribution_v2/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
archive = output / 'runtime.pyz'
manifest = builder.build(root, archive, output / 'build-manifest.json', output / 'SHA256SUMS')
cases = ('actual', 'alternate_separator', 'inside_subdirectory', 'sibling_archive', 'prefix_adjacent', 'external')
rows = []
for module in ('bridge', 'compiled'):
    for case in cases:
        code = '\n'.join(prefix) + f'''
import json
from pathlib import Path
module = {module}
original = module.__file__
case = {case!r}
archive = sys.argv[1]
member = "runtime/guarded_x11_v1/{module}.py"
if case == 'alternate_separator':
    module.__file__ = original.replace('\\\\', '/')
elif case == 'inside_subdirectory':
    module.__file__ = str(Path(archive) / 'nested' / member)
elif case == 'sibling_archive':
    module.__file__ = str(Path(archive + '.evil') / member)
elif case == 'prefix_adjacent':
    module.__file__ = str(Path(archive + '-neighbor') / member)
elif case == 'external':
    module.__file__ = str(Path(archive).parent / 'outside' / member)
print(json.dumps({{'archive': archive, 'original': original, 'candidate': module.__file__}}), flush=True)
{origin_asserts[module]}
print('origin accepted')
'''
        started = datetime.now(timezone.utc).isoformat()
        command = [sys.executable, '-I', '-c', code, str(archive)]
        result = subprocess.run(command, cwd=output, capture_output=True, text=True, timeout=30)
        rows.append({'module': module, 'case': case, 'started_utc': started,
                     'ended_utc': datetime.now(timezone.utc).isoformat(),
                     'argv': command, 'cwd': str(output), 'exit_code': result.returncode,
                     'stdout': result.stdout, 'stderr': result.stderr})
record = {'schema': 'archive-origin-probe-v1', 'platform': sys.platform,
          'python': sys.version, 'base_sha': manifest['source_revision'],
          'test_sha256': hashlib.sha256(test_raw).hexdigest(),
          'archive_sha256': manifest['sha256'], 'rows': rows}
(output / 'raw.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'raw_rows': len(rows), 'test_sha256': record['test_sha256'],
                  'archive_sha256': record['archive_sha256']}))
