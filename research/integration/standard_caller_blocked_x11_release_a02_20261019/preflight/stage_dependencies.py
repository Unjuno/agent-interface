"""Stage immutable A02 dependencies and Xvfb smoke evidence into /out."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

repo = Path('/repo')
out = Path('/out')
deps = out / 'site-packages'
out.mkdir(parents=True, exist_ok=True)
report = {'status':'RUNNING', 'python':sys.version, 'xvfb':shutil.which('Xvfb')}
try:
    deps.mkdir(parents=True, exist_ok=False)
    install = subprocess.run([sys.executable, '-m', 'pip', 'install',
        '--disable-pip-version-check', '--no-warn-script-location',
        '--target', str(deps), '-r', str(repo / 'preflight/requirements.lock')],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / 'pip-install.log').write_text(install.stdout, encoding='utf-8')
    report['pip_install_exit_code'] = install.returncode
    if install.returncode:
        raise RuntimeError('pinned dependency install failed')
    env = os.environ.copy()
    env['PYTHONPATH'] = str(deps)
    freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze', '--path', str(deps)],
        env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / 'pip-freeze.txt').write_text(freeze.stdout, encoding='utf-8')
    report['pip_freeze_exit_code'] = freeze.returncode
    if freeze.returncode:
        raise RuntimeError('pip freeze failed')
    versions = subprocess.run([sys.executable, '-c',
        'import importlib.metadata as m,json; print(json.dumps({n:m.version(n) for n in ("mcp","python-xlib","Pillow")},sort_keys=True))'],
        env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    report['dependency_versions_stdout'] = versions.stdout
    report['dependency_versions_exit_code'] = versions.returncode
    if versions.returncode:
        raise RuntimeError('dependency import/version smoke failed')
    xvfb = subprocess.Popen([shutil.which('Xvfb'), ':120', '-screen', '0',
        '800x600x24', '-nolisten', 'tcp', '-ac', '-noreset'],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError('Xvfb exited before client smoke')
            try:
                client = subprocess.run([sys.executable, '-c',
                    'from Xlib import display; d=display.Display(":120"); print(d.screen().root.get_geometry().width, d.screen().root.get_geometry().height); d.close()'],
                    env={**env, 'DISPLAY':':120'}, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if client.returncode == 0:
                    report['xvfb_client_stdout'] = client.stdout
                    report['xvfb_client_exit_code'] = client.returncode
                    break
            except Exception:
                pass
            time.sleep(0.025)
        else:
            raise TimeoutError('Xvfb client did not connect')
    finally:
        xvfb.terminate(); xvfb.wait(timeout=3)
        report['xvfb_exit_code'] = xvfb.returncode
    manifest = []
    for path in sorted(deps.rglob('*')):
        if path.is_file():
            data = path.read_bytes()
            manifest.append({'path':str(path.relative_to(deps)).replace('\\','/'),
                'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest()})
    report['dependency_file_count'] = len(manifest)
    report['dependency_tree_sha256'] = hashlib.sha256(json.dumps(
        manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (out / 'dependency-files.json').write_text(json.dumps(manifest,
        sort_keys=True, indent=2)+'\n', encoding='utf-8')
    report['status'] = 'PASS_STAGE_XVFB_AND_LOCKED_DEPENDENCIES'
except BaseException as error:
    report.update(status='FAIL_STAGE', error_type=type(error).__name__, error=str(error),
        traceback=traceback.format_exc())
(out / 'stage-result.json').write_text(json.dumps(report, sort_keys=True, indent=2)+'\n',
    encoding='utf-8')
raise SystemExit(0 if report['status'].startswith('PASS') else 1)
