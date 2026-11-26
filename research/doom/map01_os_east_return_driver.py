"""Registered one-time zero-model MAP01 east-return candidate."""
import hashlib
import json
import os
from pathlib import Path
import select
import selectors
import subprocess
import sys
import time
from copy import deepcopy

root = Path(__file__).resolve().parent
AUTHORIZED_SERVICE = False
registration_path = root / "registration.json"
begin_ns = time.perf_counter_ns()
status = {"stage": "registration", "passed": False, "start_ns": begin_ns,
          "model_calls": 0, "keyed_commands": 0}


def record(name, value):
    with (root / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def emit(log, **fields):
    log.write(json.dumps({"recorded_ns": time.perf_counter_ns(), **fields}, allow_nan=False) + "\n")
    log.flush()


def require(proof, message):
    if not proof:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def uptime_ns():
    return time.perf_counter_ns()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cgroup_path():
    rows = Path("/proc/self/cgroup").read_text().splitlines()
    require(len(rows) == 1 and rows[0].startswith("0::/"), "expected one cgroup v2 identity")
    return rows[0][3:]


def group_pids(path):
    return sorted(map(int, Path("/sys/fs/cgroup", path.lstrip("/"), "cgroup.procs").read_text().split()))


def display_retirement_evidence(descriptors, group, lock, auth, *, poll_timeout_ms=250):
    signaled = {}
    for pid, descriptor in descriptors.items():
        poller = select.poll()
        poller.register(descriptor, select.POLLIN)
        signaled[pid] = any(event & select.POLLIN for _, event in poller.poll(poll_timeout_ms))
    return {"observed_ns": uptime_ns(), "pidfds_signaled": signaled,
            "cgroup_pids_after_runtime": group_pids(group),
            "lock_absent": not lock.exists(), "xauthority_absent": not auth.exists()}


def require_complete_cleanup_evidence(status, pending_error):
    cleanup_failures = ('cleanup_stdin_error_type', 'cleanup_drain_error_type',
                        'cleanup_log_error_type', 'cleanup_raw_error_type',
                        'failure_display_observation_error_type', 'descriptor_close_error_types')
    if pending_error is None and any(key in status for key in cleanup_failures):
        status['passed'] = False
        raise RuntimeError('runtime cleanup evidence incomplete')


def process_lineage(pid):
    proc = Path("/proc") / str(pid)
    fields = (proc / "stat").read_text().rpartition(") ")[2].split()
    return {"name": (proc / "comm").read_text().strip(), "ppid": int(fields[1]),
            "start_ticks": int(fields[19]), "cgroup": (proc / "cgroup").read_text().strip()}


def capture_display(runtime, group, process, ready, fds):
    from Xlib import display as xdisplay

    gate_rows = [json.loads(line) for line in (runtime / "post-load-clock-gate.jsonl").read_text().splitlines()]
    display = next(row["display"] for row in gate_rows if row["event"] == "loaded")
    label = display["display"]
    number = int(label.removeprefix(":"))
    xvfb_pid = display["xvfb_pid"]
    lock = Path(f"/tmp/.X{number}-lock")
    require(lock.read_text().strip() == str(xvfb_pid), "X lock differs from gate identity")
    cmdline = Path(f"/proc/{xvfb_pid}/cmdline").read_bytes().rstrip(b"\0").split(b"\0")
    auth = Path(os.fsdecode(cmdline[cmdline.index(b"-auth") + 1]))
    require(auth.parent.parent == Path("/tmp") and auth.name == "Xauthority"
            and auth.lstat().st_mode & 0o777 == 0o600 and auth.lstat().st_uid == os.getuid()
            and not auth.is_symlink(), "private Xauthority changed")
    runtime_env = read_json(runtime / "environment.json")
    require(runtime_env.get("dbus_session_bus_address") == "disabled:",
            "private session bus policy missing after runtime setup")
    pids = group_pids(group)
    owned = read_json(runtime / "session-owner-service-startup.json")
    require(xvfb_pid in pids and owned["spawn_pid"] in pids and process.pid in pids,
            "runtime, Xvfb or owner not in the effective service cgroup")
    lineage = {pid: process_lineage(pid) for pid in pids}
    require(all(row["cgroup"] == "0::"+group for row in lineage.values()),
            "captured process left the effective service cgroup")
    names = {pid: row["name"] for pid, row in lineage.items()}
    require(sum(name == "openbox" for name in names.values()) == 1, "expected one owned Openbox")
    for pid, name in names.items():
        if pid != os.getpid():
            fds[pid] = os.pidfd_open(pid)
    prior = os.environ.get("XAUTHORITY")
    os.environ["XAUTHORITY"] = str(auth)
    try:
        connection = xdisplay.Display(label)
        try:
            bitmap = connection.query_keymap()
            pointer = connection.screen().root.query_pointer().mask
            neutral = len(bitmap) == 32 and not any(bitmap) and pointer == 0
            require(connection.has_extension("XTEST") and neutral, "private X11 neutral read failed")
        finally:
            connection.close()
    finally:
        if prior is None:
            os.environ.pop("XAUTHORITY", None)
        else:
            os.environ["XAUTHORITY"] = prior
    record("display-active.json", {"observed_ns": uptime_ns(), "ready_emit_ns": ready["emit_ns"],
           "unit_cgroup": group, "display": label, "pid": xvfb_pid, "lock": str(lock),
           "xauthority": str(auth), "xauthority_mode": "0600", "xtest_available": True,
           "absolute_owned_pid_names": names, "process_lineage": lineage,
           "physical_keys_down": [], "pointer_mask": pointer})
    return lock, auth


def read_stream(process, raw, log, buffer, selector, deadline):
    remaining = (deadline - uptime_ns()) / 1e9
    require(remaining > 0, "bounded runtime protocol read timed out")
    if b"\n" not in buffer:
        require(bool(selector.select(remaining)), "bounded runtime protocol read timed out")
        chunk = os.read(process.stdout.fileno(), 65536)
        if not chunk:
            return None, buffer
        raw.write(chunk)
        raw.flush()
        buffer += chunk
        require(len(buffer) < 2_000_000, "bounded runtime frame exceeded")
        if b"\n" not in buffer:
            return {}, buffer
    line, buffer = buffer.split(b"\n", 1)
    try:
        row = json.loads(line)
    except json.JSONDecodeError:
        raise ValueError("unexpected non-JSON runtime line") from None
    require(type(row) is dict and type(row.get("event")) is str, "unexpected runtime event")
    emit(log, phase="received", event=row["event"], id=row.get("id"), emit_ns=row.get("emit_ns"))
    return row, buffer


def send(process, log, command, *, on_written=None, before_write=None):
    payload = (json.dumps(command, allow_nan=False) + "\n").encode()
    require(len(payload) < 4096, "unexpected command size")
    if before_write is not None:before_write()
    require(os.write(process.stdin.fileno(), payload) == len(payload), "partial inputless command")
    if on_written is not None:
        on_written()
    emit(log, phase="sent", command=command)


def expected_runtime_argv(spec):
    checkout=Path(spec['checkout'])
    candidate=Path('/home/user/issue59-grandchild-bound-setup-yzkdlh9q/candidate/fixture.json')
    evidence_sha='40ef78b09f62fcd1b66cc6dc08257aa7d9d3f75fa0fe0797160c3d8fd48b58dc'
    manifest_sha='16f2bcf78b1d7739afd1fa0c141f1bbaee9dd2c9e3ff8e356ef3df743899d8d5'
    save_sha='4e5b990cba8a86ca8a526ecdc59798c1869ea23c8f53468369e811f41d057ddc'
    wad_sha='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
    if (spec.get('candidate_evidence_sha256')!=evidence_sha
            or spec.get('candidate_manifest_sha256')!=manifest_sha
            or spec.get('candidate_save_sha256')!=save_sha):
        raise ValueError('registered candidate is not the fixed trial candidate')
    return [spec['python'],str(checkout/'research/doom/session_map01_v15.py'),
      '--out',str(root/'runtime'),'--seed','990619','--timeout-seconds','75','--skill','1',
      '--load-fixture-manifest',str(candidate),'--target-process-identity','--owned-input-service',
      '--renewal-passive-observer','--post-load-clock-gate','--door-task-arm','use','--door-task-traverse','--door-task-reverse-arm',spec['arm'],
      '--candidate-setup-evidence',str(root/'evidence.json'),'--candidate-setup-evidence-sha256',evidence_sha,
      '--door-expected-manifest-sha256',manifest_sha,'--door-expected-save-sha256',save_sha,
      '--door-expected-iwad-sha256',wad_sha,'--door-expected-restore-tic','870']


def run():
    global AUTHORIZED_SERVICE
    registered=read_json(registration_path)
    expected_digest=sys.argv[1]
    require(Path(registered.get('root',''))==root and sha(registration_path)==expected_digest,
            'registered allocation differs')
    require(sha(root/'driver.py')==registered['driver_sha256']
            and sha(root/'evidence.json')==registered['candidate_evidence_sha256']
            and sha(root/'visual_guard.py')==registered['visual_guard_sha256']
            and sha(root/'reference.png')==registered['reference_png_sha256']
            and sha(root/'east-reference.png')==registered['east_reference_sha256']
            and sha(root/'audit.py')==registered['auditor_sha256']
            and read_json(root/'claim.json')['registration_sha256']==expected_digest,
            'driver, evidence or claim differs')
    require(registered.get('east_reference_sha256')=='89a58ce4069bc4aff69805479164ed2cc9c96a61edb768a6685c1d6ad2fcc9cc',
            'east reference differs from recorded USE endpoint')
    require(registered['arm']=='east-return' and registered['repeat_limit']==1
            and registered['model_calls']==0 and registered['candidate_restore_tic']==870,
            'registered trial bounds differ')
    checkout=Path(registered['checkout'])
    expected_pythonpath=':'.join(str(checkout/p) for p in ('','research/doom','research/live_control',
                                 'research/observation_gating','research/observation_tiles'))
    require(registered['runtime_argv']==expected_runtime_argv(registered)
            and registered['pythonpath']==expected_pythonpath,'runtime arguments differ from fixed contract')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip()==registered['revision'],
            'checkout revision differs')
    required=[checkout/'research/doom'/name for name in
              ('session_map01_v12.py','session_map01_v15.py','map01_door_driver_protocol.py',
               'map01_door_coordinator.py','map01_door_journal.py','map01_door_task_contract.py',
               'map01_door_sector_scorer.py','map01_reverse_program.py','map01_candidate_setup_evidence_v1.py','map01_post_load_gate_v1.py',
               'map01_east_return_caller_gate.py','map01_east_return_visual_guard.py')]
    require(type(registered.get('files')) is dict and all(str(path) in registered['files'] for path in required)
            and all(sha(Path(name))==digest for name,digest in registered['files'].items()),'pinned bytes differ')
    require(not subprocess.check_output(['git','status','--porcelain'],cwd=checkout,text=True).strip(),
            'checkout has uncommitted changes')
    cgroup=cgroup_path()
    require(cgroup.endswith('/'+registered['unit']) and group_pids(cgroup)==[os.getpid()],
            'exclusive transient service required')
    properties=('Id','MainPID','ControlGroup','ActiveState','PrivateTmp','PrivateNetwork','KillMode',
                'RuntimeMaxUSec','TimeoutStopUSec','UMask','InvocationID')
    observed=dict(line.split('=',1) for line in subprocess.check_output(
        ['systemctl','--user','show',registered['unit'],*('--property='+k for k in properties)],
        timeout=3,text=True).splitlines())
    expected={'Id':registered['unit'],'MainPID':str(os.getpid()),'ControlGroup':cgroup,
              'PrivateTmp':'yes','PrivateNetwork':'yes','KillMode':'control-group',
              'RuntimeMaxUSec':'1min','TimeoutStopUSec':'5s','UMask':'0077'}
    require(all(observed.get(k)==v for k,v in expected.items()),'service isolation differs')
    record('service-active.json',{'observed_ns':uptime_ns(),'properties':observed,
                                 'uid':os.getuid(),'initial_pids':group_pids(cgroup)})
    AUTHORIZED_SERVICE=True
    sys.path[:0]=[str(checkout/'research/doom'),str(checkout/'research/live_control'),str(checkout)]
    import map01_door_driver_protocol as protocol_module
    require(Path(protocol_module.__file__).resolve()==(checkout/'research/doom/map01_door_driver_protocol.py').resolve(),
            'protocol module source differs')
    DoorDriverProtocol=protocol_module.DoorDriverProtocol
    import map01_east_return_caller_gate as east_gate_module
    require(Path(east_gate_module.__file__).resolve()==(checkout/'research/doom/map01_east_return_caller_gate.py').resolve(),
            'east gate module source differs')
    protocol=DoorDriverProtocol('use',registered['candidate_manifest_sha256'],
       registered['candidate_save_sha256'],registered['candidate_evidence_sha256'],870,traverse=True,reverse_arm=registered['arm'])
    env={'PATH':'/usr/bin:/bin','LC_ALL':'C.UTF-8','PYTHONPATH':registered['pythonpath'],
         'PYTHONDONTWRITEBYTECODE':'1','SDL_VIDEODRIVER':'x11'}
    for key in ('HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME','XDG_RUNTIME_DIR'):
        folder=root/'private-profile'/key.lower();folder.mkdir(parents=True,mode=0o700);env[key]=str(folder)
    runtime=root/'runtime';game=None;descriptors={};lock=auth=None;pending_dispatched=None
    status.update(stage='runtime-start',arm=registered['arm'],model_calls=0,
                  keyed_commands=0,keyed_submit_attempted=[],keyed_submit_written=[],
                  input_admissions_observed=[])
    deadline=begin_ns+48_000_000_000
    with (root/'runtime.stderr').open('xb') as stderr, (root/'runtime.stdout').open('xb',buffering=0) as raw, \
         (root/'driver.jsonl').open('x',encoding='utf-8') as log, selectors.DefaultSelector() as selector:
        try:
            game=subprocess.Popen(registered['runtime_argv'],cwd=checkout,env=env,stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,stderr=stderr,bufsize=0)
            os.set_blocking(game.stdin.fileno(),False);selector.register(game.stdout,selectors.EVENT_READ)
            buffer=b'';ready_seen=False;finish_sent=False;settle_waits=0;east_gate=None
            while True:
                row,buffer=read_stream(game,raw,log,buffer,selector,deadline)
                if row is None:
                    require(finish_sent and protocol.stage=='finish' and not buffer,'premature runtime EOF')
                    break
                if not row:continue
                if row.get('event')=='terminal' and row.get('id')==pending_dispatched:
                    pending_dispatched=None
                if row.get('event')=='input_admission':
                    status['input_admissions_observed'].append(row.get('id'))
                if row.get('event')=='ready':
                    require(not ready_seen,'duplicate ready')
                    lock,auth=capture_display(runtime,cgroup,game,row,descriptors)
                    ready_seen=True
                command=protocol.receive(row,uptime_ns())
                if east_gate is None and protocol.identity is not None:
                    surface,owner,generation,process_digest,window_digest=protocol.identity
                    observed=protocol.typed if protocol.typed is not None else protocol.latest
                    identity={'surface':surface,'owner':owner,'generation':generation,
                              'process_digest':process_digest,'window_digest':window_digest,
                              'geometry':deepcopy(observed['pointer_binding']['geometry'])}
                    east_gate=east_gate_module.EastReturnCallerGate(
                        reference=root/'east-reference.png',reference_sha256=registered['east_reference_sha256'],
                        runtime_dir=runtime,identity=identity)
                if east_gate is not None and east_gate.state=='collecting':
                    east_gate.receive(row)
                if command is not None:
                    if command.get('op')=='door-settle' and row.get('status')=='WAIT':
                        settle_waits+=1
                        require(settle_waits<=250,'settlement poll bound exceeded')
                        time.sleep(.02)
                    else:
                        settle_waits=0
                    require(uptime_ns()<deadline,'absolute trial deadline expired before send')
                    if command.get('op')=='submit' and command.get('id')=='reverse-probe':
                        require(not (root/'visual-guard.json').exists(),'visual gate already consumed')
                        import importlib.util
                        guard_spec=importlib.util.spec_from_file_location('registered_visual_guard',root/'visual_guard.py')
                        guard=importlib.util.module_from_spec(guard_spec);guard_spec.loader.exec_module(guard)
                        try:
                            east_gate_module.require_new_frame(protocol.latest,'reverse-turn-3')
                            receipt=guard.check(protocol.latest,reference=root/'reference.png',
                                reference_sha256=registered['reference_png_sha256'],runtime_dir=runtime,clock=uptime_ns)
                        except Exception as error:
                            record('visual-guard.json',{'passed':False,'error_type':type(error).__name__,'observed_ns':uptime_ns()})
                            raise
                        record('visual-guard.json',receipt)
                        require(receipt['passed'] is True and command['expected_sequence']==receipt['sequence']
                                and uptime_ns()<command['valid_until_ns']
                                and 0<=uptime_ns()-receipt['capture_ns']<2_000_000_000,'visual gate failed or source expired')
                    if command.get('op')=='submit' and command.get('id')=='east-turn-1':
                        require(east_gate is not None and not (root/'east-visual-guard.json').exists(),
                                'east visual gate unavailable or already consumed')
                        east_gate_module.require_no_pending_output(buffer,selector)
                        try:
                            east_receipt=east_gate.prepare(command,protocol,clock=uptime_ns)
                        except Exception as error:
                            failure=deepcopy(east_gate.receipt) if east_gate.receipt is not None else {'passed':False}
                            failure.update(error_type=type(error).__name__,observed_ns=uptime_ns())
                            record('east-visual-guard.json',failure)
                            raise
                        record('east-visual-guard.json',east_receipt)
                    if command.get('op')=='finish':finish_sent=True
                    keyed=(command.get('op')=='submit' and
                           any(step.get('op')=='hold' for step in command.get('steps',[])))
                    if keyed:status['keyed_submit_attempted'].append(command['id'])
                    def mark_written():
                        if keyed:
                            status['keyed_submit_written'].append(command['id'])
                            status['keyed_commands']=len(status['keyed_submit_written'])
                    def check_before_write():
                        nonlocal pending_dispatched
                        now=uptime_ns()
                        require(now<deadline,'absolute trial deadline expired before write')
                        if command.get('op')=='submit':
                            require(now<command['valid_until_ns'],'command expired before write')
                            if command.get('id')=='reverse-probe':
                                require(0<=now-receipt['capture_ns']<2_000_000_000,'visual source expired before write')
                            if command.get('id')=='east-turn-1':
                                east_gate_module.require_no_pending_output(buffer,selector)
                                now=uptime_ns()
                                east_gate.before_write(command,protocol,now=now,absolute_deadline=deadline)
                            pending_dispatched=command['id']
                    send(game,log,command,on_written=mark_written,before_write=check_before_write)
            status['runtime_exit_code']=game.wait(timeout=2)
            require(status['runtime_exit_code']==0,'runtime failed')
            end=read_json(runtime/'session-owner-service-close.json')
            require(end.get('verified') is True and end.get('startup_sha256')==sha(runtime/'session-owner-service-startup.json'),
                    'owner close receipt differs')
            require(protocol.index==24,'settled operation count differs')
            retirement=display_retirement_evidence(descriptors,cgroup,lock,auth)
            record('display-retired.json',retirement)
            require(retirement['pidfds_signaled'] and all(retirement['pidfds_signaled'].values())
                    and retirement['cgroup_pids_after_runtime']==[os.getpid()]
                    and retirement['lock_absent'] and retirement['xauthority_absent'],'display not retired')
            status.update(stage='retired',passed=True,settled_operations=protocol.index,task_effect='not_evaluated')
        finally:
            try:
                if game is not None:
                    if game.poll() is None:
                        status['cleanup_release_status']='unknown'
                        if protocol.pending is not None and pending_dispatched==protocol.pending:
                            status['cleanup_cancel_attempted']=True
                            status['cleanup_cancel_written']=False
                            def mark_cancel_written():
                                status['cleanup_cancel_written']=True
                            try:
                                send(game,log,{'op':'cancel','id':protocol.pending},
                                     on_written=mark_cancel_written)
                            except Exception as error:
                                status['cleanup_cancel_error_type']=type(error).__name__
                        try:game.stdin.close()
                        except Exception as error:status['cleanup_stdin_close_error_type']=type(error).__name__
                    drain_deadline=uptime_ns()+4_000_000_000
                    status['cleanup_drain_eof']=False
                    while uptime_ns()<drain_deadline:
                        remaining=max(0,(drain_deadline-uptime_ns())/1e9)
                        try:
                            selected=selector.select(min(remaining,.1))
                            if not selected:
                                continue
                            chunk=os.read(game.stdout.fileno(),65536)
                            if not chunk:
                                status['cleanup_drain_eof']=True
                                break
                            raw.write(chunk);raw.flush()
                        except Exception as error:
                            status['cleanup_drain_error_type']=type(error).__name__
                            break
                    if game.poll() is None:
                        try:game.wait(timeout=1)
                        except subprocess.TimeoutExpired:status['cleanup_wait']='delegated_to_service'
            finally:
                if status.get('cleanup_drain_error_type') or not status.get('cleanup_drain_eof',False):
                    status['passed']=False
                if status.get('cleanup_release_status')=='unknown' and game is not None:
                    try:
                        from map01_east_return_audit import validate_failure_cleanup
                        validate_failure_cleanup(runtime,process_exited=game.poll() is not None,
                                                 drain_eof=status.get('cleanup_drain_eof') is True)
                    except Exception as error:
                        status['cleanup_receipt_error_type']=type(error).__name__
                    else:
                        status['cleanup_release_status']='verified'
                try:
                    if not status['passed'] and descriptors and lock is not None and auth is not None:
                        try:
                            record('failure-display-retired.json',display_retirement_evidence(descriptors,cgroup,lock,auth))
                        except Exception as error:
                            status['failure_display_observation_error_type']=type(error).__name__
                finally:
                    for descriptor in descriptors.values():
                        try:os.close(descriptor)
                        except OSError:status['passed']=False;status['descriptor_close_error']=True



try:
    run()
except BaseException as error:
    status.update(passed=False,error_type=type(error).__name__,error=str(error))
finally:
    status['finish_ns']=uptime_ns()
    if AUTHORIZED_SERVICE:
        record('worker-outcome.json',status)
sys.exit(0 if status['passed'] else 2)
