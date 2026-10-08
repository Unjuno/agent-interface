"""Capture the task-owned guest and pinned X11 construction dependencies."""
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent

def command(args):
    try:
        p = subprocess.run(args, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=10, check=False)
        return {"argv": args, "exit_code": p.returncode,
                "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as exc:
        return {"argv": args, "error": repr(exc)}

os_release = Path('/etc/os-release').read_text(encoding='utf-8') if Path('/etc/os-release').exists() else ''
socket_dir = Path('/tmp/.X11-unix')
result = {
    "schema": "map01-v39-owner-keymap-environment-v1",
    "captured_at_utc": datetime.now(timezone.utc).isoformat(),
    "machine_name": platform.node(),
    "machine_id": "01M4283HRND5FW9AG9FXYX0B7H",
    "task_owned_guest": "research-59-per-key-telemetry-01a0ff52-20261004",
    "platform": platform.platform(),
    "uname": platform.uname()._asdict(),
    "os_release": os_release,
    "python_executable": sys.executable,
    "python_version": sys.version,
    "python_packages": subprocess.run([sys.executable, '-m', 'pip', 'freeze'],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False).stdout.splitlines(),
    "python_xlib_version": importlib.metadata.version('python-xlib'),
    "six_version": importlib.metadata.version('six'),
    "xvfb_path": shutil.which('Xvfb'),
    "xvfb_package": command(['dpkg-query', '-W', '-f=${Status} ${Version}', 'xvfb']),
    "x11_socket_directory_mode": oct(stat.S_IMODE(socket_dir.stat().st_mode)) if socket_dir.exists() else None,
    "x11_socket_directory_is_tmpfs": False,
    "xvfb_processes_before_candidate": command(['pgrep', '-a', '-x', 'Xvfb']),
    "unshare_network_namespace_preflight": command(['unshare', '-n', 'true']),
    "network_namespace_preflight_exit": subprocess.run(['unshare', '-n', 'true'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode,
    "network_route": "guest networking remains enabled; candidate makes no network calls and Xvfb uses -nolisten tcp",
    "cpu_count": os.cpu_count(),
    "meminfo": Path('/proc/meminfo').read_text(encoding='utf-8'),
    "repo_mount": str(ROOT),
    "candidate_network_isolation": "none; no candidate code performs network access; Xvfb TCP disabled",
}
try:
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left, sep, right = line.partition(' - ')
        if sep and left.split()[4] == '/tmp' and right.split()[0] == 'tmpfs':
            result['x11_socket_directory_is_tmpfs'] = True
except Exception:
    pass
(ROOT / 'ENVIRONMENT.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n',
                                       encoding='utf-8')
print(json.dumps({k: result[k] for k in ('python_executable','python_xlib_version','six_version','xvfb_path','xvfb_package','x11_socket_directory_mode','network_namespace_preflight_exit','cpu_count','repo_mount')}, sort_keys=True))
