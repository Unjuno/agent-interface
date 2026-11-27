"""Launch one privately isolated east-return attempt and seal retired evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import stat
import sys
import time

root = Path(__file__).resolve().parent
os.umask(0o077)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(name, value):
    with (root/name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def status(unit):
    try:
        p = subprocess.run(["systemctl","--user","show",unit,"--property=Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result"],
                           capture_output=True,text=True,timeout=4)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"observed_ns":time.perf_counter_ns(), "exit_code":None, "stdout":"",
                "stderr":"", "observation":"unknown", "error_type":type(error).__name__}
    return {"observed_ns":time.perf_counter_ns(),"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr}


def regular_bytes(path):
    descriptor=os.open(path,os.O_RDONLY | getattr(os,'O_NOFOLLOW',0))
    with os.fdopen(descriptor,'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('registered file is not regular')
        return stream.read()


registration = root / "registration.json"
external = sys.argv[1]
initial={'driver.py','launcher.py','evidence.json','registration.json','visual_guard.py',
         'reference.png','east-reference.png','audit.py','preflight.py'}
if set(path.name for path in root.iterdir())!=initial:
    raise SystemExit('allocation is not unspent')
registration_bytes=regular_bytes(registration)
if hashlib.sha256(registration_bytes).hexdigest()!=external:
    raise SystemExit('wrong registration digest')
spec=json.loads(registration_bytes)
launcher_bytes=regular_bytes(root/'launcher.py')
preflight_path=root/'preflight.py';preflight_bytes=regular_bytes(preflight_path)
if (Path(spec.get('root',''))!=root
        or hashlib.sha256(launcher_bytes).hexdigest()!=spec.get('launcher_sha256')
        or hashlib.sha256(preflight_bytes).hexdigest()!=spec.get('preflight_sha256')):
    raise SystemExit('wrong launcher or preflight digest')
# Execute exactly the bytes already checked; no import cache or second path read.
preflight={'__name__':'registered_east_preflight'}
exec(compile(preflight_bytes,str(preflight_path),'exec'),preflight)
try:
    preflight['validate_unspent'](root,spec,expected_east_sha='89a58ce4069bc4aff69805479164ed2cc9c96a61edb768a6685c1d6ad2fcc9cc',
        expected_initial_sha='c3f196d116c370b3d34daa47cafa73b400fd3fb8537b9c70d4a093b15a4b7988',
        expected_guard_sha='8ec9b693c15fa881096f429b71333cbb93c107976ace02cbe5cb96eb35612afa')
    preflight['validate_runtime_inputs'](root,spec,expected_checkout=preflight['registered_checkout'](spec),
        baseline_path=Path('/home/user/issue59-grandchild-bound-setup-yzkdlh9q/registration.json'),
        baseline_sha256='4dbe44082da117dde60a7713157065bcc5d490bf720a9a988b1e0e7707b4ee6d')
except (ValueError,OSError) as error:
    raise SystemExit(str(error)) from error
unit = spec["unit"]
before = status(unit)
if "LoadState=not-found" not in before["stdout"]:
    raise SystemExit("unique transient service name is already active or unverified")
cmd = ["systemd-run","--user","--wait","--pipe","--collect","--unit="+unit,
       *[s for option in spec["unit_options"] for s in ("-p",option)],
       spec["python"],"-B",str(root/"driver.py"),external]
record("claim.json",{"registration_sha256":external,"claimed_ns":time.perf_counter_ns(),"unit":unit,"before":before})
record("launch.json",{"argv":cmd,"started_ns":time.perf_counter_ns()})
print(json.dumps({"unit":unit,"state":"claimed","root":str(root)}),flush=True)
with (root/"service.stdout").open("xb") as out, (root/"service.stderr").open("xb") as err:
    try:
        result = subprocess.run(cmd,stdout=out,stderr=err,stdin=subprocess.DEVNULL,timeout=77)
        exit_code = result.returncode
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
        exit_code = None
        # The service's own RuntimeMaxSec is the stop mechanism. Never stop a
        # possibly reused unit name without proving the instance identity.
    except OSError:
        timed_out = False
        exit_code = None
after = status(unit)
service_active = root / "service-active.json"
group = f"/user.slice/user-{os.getuid()}.slice/user@{os.getuid()}.service/app.slice/{unit}"
service_row,service_marker_status=preflight['read_marker'](service_active)
properties=service_row.get('properties') if isinstance(service_row,dict) else None
service_observed=(isinstance(properties,dict) and properties.get('Id')==unit
                  and properties.get('ControlGroup')==group
                  and type(properties.get('MainPID')) is str and properties['MainPID'].isdigit()
                  and int(properties['MainPID'])>0
                  and type(properties.get('InvocationID')) is str and len(properties['InvocationID'])==32)
if service_marker_status=='valid' and not service_observed:
    service_marker_status='invalid_shape'
cgroup = Path("/sys/fs/cgroup") / group.lstrip("/")
retired,service_retirement_observed = preflight['retirement_disposition'](
    "LoadState=not-found" in after["stdout"],not cgroup.exists(),service_observed)
worker_row,worker_marker_status=preflight['read_marker'](root/'worker-outcome.json')
passed = (exit_code == 0 and service_retirement_observed and worker_marker_status=='valid'
          and worker_row.get('passed') is True)
record("launcher-outcome.json",{"unit":unit,"exit_code":exit_code,"timed_out":timed_out,
       "retired":retired,"service_retirement_observed":service_retirement_observed,
       "service_marker_status":service_marker_status,"worker_marker_status":worker_marker_status,
       "control_group":group,"service_after":after})
if retired:
    files = sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink())
    record("seal.json",{"schema":"map01-clock-preflight-local-seal-v1","passed":passed,
          "complete_service_retirement":service_retirement_observed,
          "files":{p.relative_to(root).as_posix():{"sha256":sha(p),"bytes":p.stat().st_size} for p in files}})
print(json.dumps({"root":str(root),"unit":unit,"service_exit_code":exit_code,"timed_out":timed_out,
                  "unit_and_cgroup_absent":retired,"service_retired":service_retirement_observed,"passed":passed,"seal_sha256":sha(root/"seal.json") if retired else None}),
      flush=True)
sys.exit(0 if passed else 2)
