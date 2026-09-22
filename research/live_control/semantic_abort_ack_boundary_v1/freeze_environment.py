"""One-time pre-formal metadata capture. Never launches GUI or model work."""
from pathlib import Path
import sys, platform, json, hashlib, shutil, datetime, importlib.metadata, inspect
import tkinter, _tkinter, Xlib
from Xlib.protocol import rq
p = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

paths = [Path(sys.executable).resolve(), Path(shutil.which('Xvfb')), Path(inspect.getfile(rq)),
         Path(inspect.getfile(_tkinter)), Path('/usr/share/tcltk/tk8.6/button.tcl')]
paths += list(Path('/usr/lib/x86_64-linux-gnu').glob('libtcl8.6.so'))
paths += list(Path('/usr/lib/x86_64-linux-gnu').glob('libtk8.6.so'))
try:
    package = importlib.metadata.version('python-xlib')
except importlib.metadata.PackageNotFoundError:
    package = 'DISTRIBUTION_METADATA_UNAVAILABLE; module version separately retained'
env = {
    'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'runtime': 'provided Linux execution container; no Docker/OrbStack identity attested',
    'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
    'machine': platform.machine(), 'docker_cli': shutil.which('docker'),
    'xvfb': shutil.which('Xvfb'), 'python_xlib_distribution': package,
    'python_xlib_module_version': getattr(Xlib, '__version__', 'unavailable'),
    'tcl': tkinter.Tcl().call('info', 'patchlevel'),
    'tk_live_version': '8.6.16 from construction05 ready receipts',
    'binary_and_runtime_sha256': {str(x): sha(x) for x in paths if x.is_file()},
    'xlib_module_sha256': {str(x.relative_to(Path(Xlib.__file__).parent)): sha(x)
                          for x in sorted(Path(Xlib.__file__).parent.rglob('*.py'))},
    'image_bytes_parser': 'String8 decodes valid UTF-8; invert exactly using utf-8 encoding, otherwise keep bytes',
    'network_scope': 'Xvfb -nolisten tcp, private auth; experiment makes no network calls; container network isolation not attested',
    'authority': 'owned private Xvfb only; no inherited display or production runtime/model calls',
    'metadata_construction_incident': 'initial metadata attempt raised PackageNotFoundError before writing ENVIRONMENT or FREEZE; no formal invocation'
}
with open(p/'ENVIRONMENT.json', 'x') as f:
    f.write(json.dumps(env, sort_keys=True, indent=2)+'\n')
(p/'results').mkdir(exist_ok=True)
freeze = {
    'issue': 3930, 'allocation': 'semantic-abort-ack-20260922-01',
    'intake_main': 'b2457b746a6df06f6536585dfe2ab937aff639f4',
    'sources': {x: sha(p/x) for x in ['study.py', 'audit.py', 'PLAN.json']},
    'environment_sha256': sha(p/'ENVIRONMENT.json'),
    'metadata_collector_sha256': sha(__file__),
    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'formal_invocations_at_freeze': 0,
    'formal_output_absent': not (p/'results/semantic-abort-ack-20260922-01').exists(),
    'formal_command': 'python study.py run --out results/semantic-abort-ack-20260922-01',
    'audit_command': 'python audit.py results/semantic-abort-ack-20260922-01/RAW.json --freeze FREEZE.json',
    'schedule_rows': 18, 'corruption_controls': 14,
    'construction_final_raw_sha256': sha(p/'construction05/RAW.json'),
    'construction_final_audit_sha256': sha(p/'construction05.audit.json'),
    'construction_failures_preserved': [
        'construction01: inherited Xauthority absent; no task input',
        'construction02: FamilyWild-only client auth failed; no task input; partial-raw mutation audit also failed',
        'construction03: normal case complete; applied case zero callbacks but String8 pixel recording TypeError; all input released'],
    'claims_excluded': ['model performance', 'latency improvement', 'generic Tk cancellation', 'XI2 equivalence',
                        'Docker/OrbStack validation', 'production runtime promotion', 'full #2197 closure']
}
with open(p/'FREEZE.json', 'x') as f:
    f.write(json.dumps(freeze, sort_keys=True, indent=2)+'\n')
for name in ['study.py', 'audit.py', 'PLAN.json']:
    with open(p/'construction05'/('SOURCE_'+name), 'xb') as f:
        f.write((p/name).read_bytes())
print(json.dumps(freeze, indent=2, sort_keys=True))
print('FREEZE_SHA256', sha(p/'FREEZE.json'))
