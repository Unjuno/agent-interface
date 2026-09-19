"""Dependency discovery for the existing native path; no app input or model call."""
import importlib
import json
import platform
import shutil
import subprocess


def main():
    report = {'platform': platform.platform(), 'python': platform.python_version(),
              'modules': {}, 'executables': {}, 'input_dispatched': False,
              'model_calls': 0}
    for name in ('PIL', 'numpy', 'openpyxl', 'Xlib', 'native_handle_bridge_v1',
                 'native_exchange_v1', 'agent_review', 'run_native_calc_self_use_v1'):
        module = importlib.import_module(name)
        report['modules'][name] = {'path': module.__file__,
                                  'version': getattr(module, '__version__', None)}
    for name in ('Xvfb', 'openbox', 'wmctrl', 'inkscape', 'libreoffice'):
        path = shutil.which(name)
        if path is None:
            raise RuntimeError('missing executable: '+name)
        report['executables'][name] = path
    for name in ('inkscape', 'libreoffice'):
        result = subprocess.run([name, '--version'], capture_output=True, text=True,
                                timeout=15, check=True)
        report['executables'][name] = {'path': report['executables'][name],
                                       'version': result.stdout.strip()}
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
