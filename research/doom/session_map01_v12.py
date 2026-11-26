"""MAP01 v12 publishes lease-bound physical release before terminal closure."""

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import threading
import time
from copy import deepcopy
from pathlib import Path

import vizdoom as vd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "observation_gating"))
sys.path.insert(0, str(HERE.parent / "live_control"))
from executor_v12 import Executor
from executor_v11 import program_sha256
from lease import Expired
from doom_typed_release_backend_v1 import Backend, suite
from doom_hud_signal_v3 import DoomStatusNumberReader
from doom_cover_renewal_probe_v1 import (
    IDENTIFIER as RENEWAL_ID, PassiveProbeDelivery, settled_cover_probe_source)
from input_owner_generation_protocol_v1 import InputOwnerGenerationProtocol
from doom_controller_failure_cleanup_v1 import operation_release_verified
from map01_synthetic_exit_refresh import synchronize_terminal


FIXTURE_SCHEMA = "map01_os_input_fixture_v1"
CANDIDATE_FIXTURE_SCHEMA = "map01_os_input_fixture_candidate_v1"
SETUP_INPUT_CONTRACT = ("fixture state reached through the same X11 Executor and "
                        "recorded OS-input/coast programs; save is setup-only")


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def door_game_variables(variable, traverse):
    result=[variable.DEATHCOUNT,variable.KILLCOUNT]
    if traverse:
        result.extend((variable.POSITION_X,variable.POSITION_Y,variable.ANGLE,variable.HEALTH))
    return result


SYNTHETIC_EXIT_PWAD_SHA256 = 'bd634d97942e6c88f5474d58f4181245d0f7475c9c2ec4595952f3657c5681f3'


def copy_pinned_calibration_file(source, destination, expected_sha256):
    source=Path(source);destination=Path(destination)
    if source.is_symlink() or not source.is_file():raise ValueError('synthetic scenario unavailable')
    data=source.read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected_sha256:
        raise ValueError('calibration input bytes differ')
    with destination.open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    if file_sha256(destination)!=expected_sha256:
        raise ValueError('private calibration input differs')
    return destination


def copy_synthetic_exit_scenario(source, destination):
    return copy_pinned_calibration_file(source,destination,SYNTHETIC_EXIT_PWAD_SHA256)


def validate_synthetic_exit_calibration(args, post_load_gate):
    path=getattr(args,'synthetic_exit_pwad',None)
    arm=getattr(args,'synthetic_exit_arm',None)
    if path is None:
        if arm is not None or getattr(args, 'synthetic_exit_refresh', False):raise ValueError('synthetic exit options require the fixed scenario')
        return None
    if (arm not in ('control','use') or post_load_gate is not None
            or args.door_task_arm is not None or getattr(args,'door_task_traverse',False)
            or getattr(args,'door_task_exit',False) or getattr(args,'door_task_exit_arm',None) is not None
            or args.load_fixture_manifest is not None or args.fixture_out is not None
            or args.verified_fixture_setup or args.fresh_neutral_fixture_setup
            or getattr(args,'candidate_setup_evidence',None) is not None
            or getattr(args,'candidate_setup_evidence_sha256',None) is not None
            or not args.renewal_passive_observer or args.timeout_seconds!=75 or args.seed!=990619 or args.skill!=1
            or not Path(path).is_file() or Path(path).is_symlink()
            or file_sha256(path)!=SYNTHETIC_EXIT_PWAD_SHA256):
        raise ValueError('synthetic exit calibration requires fixed isolated scenario and arm')
    return None


def synthetic_neutral_heartbeat(backend, gate, session, source, *, clock=time.perf_counter_ns, started=None, expected_revision=None):
    """Read owner and physical input state without a lease or input authority."""
    if started is None:started=clock()
    try:
        owner=backend.owner;service=backend.owned_service
        binding=source['pointer_binding'];identity=source['target_process_identity']
        if (type(started) is not int or type(source) is not dict or type(binding) is not dict
                or type(identity) is not dict or type(source.get('sequence')) is not int
                or source['sequence']!=backend.sequence or identity.get('sequence')!=source['sequence']
                or identity.get('surface')!=binding.get('surface') or binding.get('focus')!=binding.get('surface')
                or backend._source_identity!=(source['sequence'],binding['surface'],identity.get('digest'))
                or source.get('input_owner_generation')!=backend._owner_generation
                or source.get('renewal_owner_id')!=owner.owner_id or owner.service_id!=service.service_id
                or service.process is None or not service.process.is_alive() or owner.obligation_snapshot() is not None):
            raise ValueError('owner or source identity differs')
        state=owner.call('input_state')
        if (type(state) is not dict or state.get('owner_id')!=owner.owner_id
                or type(state.get('revision')) is not int or state['revision']<0
                or expected_revision is not None and (type(expected_revision) is not int or state['revision']!=expected_revision)
                or state.get('owned_keycodes')!=[] or state.get('owned_buttons')!=[]
                or type(state.get('physical_pointer_mask')) is not int or state['physical_pointer_mask']!=0
                or type(state.get('focus')) is not int or state['focus']!=binding['surface']
                or state.get('release_pending') is not False or state.get('cancel_requested') is not False
                or 'active_lease_deadline_ns' not in state or state['active_lease_deadline_ns'] is not None
                or type(state.get('sample_started_ns')) is not int or type(state.get('sample_finished_ns')) is not int
                or not started<=state['sample_started_ns']<=state['sample_finished_ns']
                or gate.neutral(session) is not True):
            raise ValueError('owner or physical state is not neutral')
        ended=clock()
        if (type(ended) is not int or not state['sample_finished_ns']<=ended<started+1_000_000_000
                or not service.process.is_alive() or owner.obligation_snapshot() is not None):
            raise ValueError('owner heartbeat timed out or lost custody')
        return {'verified':True,'started_ns':started,'finished_ns':ended,'owner_id':owner.owner_id,
                'owner_generation':backend._owner_generation,'source_sequence':source['sequence'],
                'owner_state':state,'physical_neutral':True,'grants_input_authority':False}
    except Exception as error:
        raise RuntimeError('synthetic neutral heartbeat unavailable') from error


def validate_verified_fixture_setup(args, post_load_gate):
    fresh = getattr(args, 'fresh_neutral_fixture_setup', False)
    loaded = args.verified_fixture_setup
    candidate_evidence = getattr(args, 'candidate_setup_evidence', None)
    candidate_evidence_sha = getattr(args, 'candidate_setup_evidence_sha256', None)
    door_arm=getattr(args,'door_task_arm',None)
    traverse=getattr(args,'door_task_traverse',False)
    exit_probe=getattr(args,'door_task_exit',False)
    exit_arm=getattr(args,'door_task_exit_arm',None)
    if (type(exit_probe) is not bool or exit_probe and (not traverse or exit_arm not in ('control','use'))
            or not exit_probe and exit_arm is not None):
        raise ValueError('exit probe requires explicit door traversal')
    if type(traverse) is not bool or traverse and door_arm is None:
        raise ValueError('door traversal requires explicit door task mode')
    if door_arm is not None:
        if (door_arm not in ('control','use') or fresh or loaded or post_load_gate is None
                or args.load_fixture_manifest is None or args.fixture_out is not None
                or candidate_evidence is None or type(candidate_evidence_sha) is not str
                or re.fullmatch(r'[0-9a-f]{64}',candidate_evidence_sha) is None
                or type(getattr(args,'timeout_seconds',None)) is not int or args.timeout_seconds!=75
                or type(getattr(args,'seed',None)) is not int or args.seed!=990619
                or type(getattr(args,'skill',None)) is not int or args.skill!=1
                or any(type(getattr(args,name,None)) is not str or
                       re.fullmatch(r'[0-9a-f]{64}',getattr(args,name,'')) is None
                       for name in ('door_expected_manifest_sha256','door_expected_save_sha256','door_expected_iwad_sha256'))
                or args.door_expected_iwad_sha256!='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
                or type(getattr(args,'door_expected_restore_tic',None)) is not int
                or args.door_expected_restore_tic<1
                or not getattr(args,'renewal_passive_observer',False)):
            raise ValueError('door task requires a fixed candidate proof, owner and clock gate')
        return None
    if any(getattr(args,name,None) is not None for name in
           ('door_expected_manifest_sha256','door_expected_save_sha256','door_expected_iwad_sha256','door_expected_restore_tic')):
        raise ValueError('door candidate pins require explicit door task mode')
    if candidate_evidence is not None or candidate_evidence_sha is not None:
        if (not loaded or fresh or candidate_evidence is None
                or type(candidate_evidence_sha) is not str
                or re.fullmatch(r'[0-9a-f]{64}', candidate_evidence_sha) is None
                or type(getattr(args, 'timeout_seconds', None)) is not int
                or args.timeout_seconds != 75):
            raise ValueError('candidate evidence is restricted to verified loaded setup with a fixed hash')
    if not fresh and not loaded:
        if post_load_gate is not None and (args.load_fixture_manifest is None or args.fixture_out is not None):
            raise ValueError("post-load clock gate requires a fixed loaded fixture")
        return
    if fresh:
        if loaded or post_load_gate is not None or args.load_fixture_manifest is not None or args.fixture_out is None:
            raise ValueError("fresh fixture setup requires a new game and new output")
    elif post_load_gate is None or args.load_fixture_manifest is None or args.fixture_out is None:
        raise ValueError("verified fixture setup requires a loaded fixture, clock gate and new output")
    if not args.renewal_passive_observer:
        raise ValueError("fixture setup requires renewal owner identity")
    if (type(args.fixture_setup_program_sha256) is not str or
            re.fullmatch(r'[0-9a-f]{64}', args.fixture_setup_program_sha256) is None):
        raise ValueError("verified fixture setup requires a fixed program hash")
    if os.path.lexists(args.fixture_out):
        raise ValueError("verified fixture output already exists")
    destination = Path(os.path.abspath(args.fixture_out))
    parent = destination.parent
    if parent.resolve() != parent:
        raise ValueError("verified fixture directory must not use symlinks")
    info = parent.stat(follow_symlinks=False)
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("verified fixture directory must be private and owned")
    for path in (destination, destination.with_suffix('.json'),
                 destination.with_name(destination.stem + '.source.png')):
        if os.path.lexists(path):
            raise ValueError("verified fixture output already exists")
    return info.st_dev, info.st_ino


def validate_door_candidate_binding(args, binding, iwad_sha):
    if (type(binding) is not dict
            or binding.get('candidate_manifest_sha256')!=args.door_expected_manifest_sha256
            or binding.get('candidate_save_sha256')!=args.door_expected_save_sha256
            or binding.get('expected_restore_tic')!=args.door_expected_restore_tic
            or iwad_sha!=args.door_expected_iwad_sha256):
        raise ValueError('door candidate differs from preregistered binding')


def copy_file_exclusive(source, destination):
    with Path(source).open('rb') as src, Path(destination).open('xb') as dst:
        shutil.copyfileobj(src, dst)


def load_setup_candidate(game, source, destination, binding, before_tic, init_started_ns):
    expected_tic = binding.get('expected_restore_tic') if type(binding) is dict else None
    expected_sha = binding.get('candidate_save_sha256') if type(binding) is dict else None
    if (type(expected_tic) is not int or expected_tic < 0 or type(expected_sha) is not str
            or re.fullmatch(r'[0-9a-f]{64}', expected_sha) is None
            or type(before_tic) is not int or before_tic < 0 or before_tic >= expected_tic
            or type(init_started_ns) is not int or init_started_ns <= 0):
        raise ValueError('candidate load binding is invalid')
    copy_file_exclusive(source, destination)
    if file_sha256(destination) != expected_sha:
        raise ValueError('candidate save changed after setup preflight')
    load_started_ns = time.perf_counter_ns()
    game.load(str(destination))
    load_returned_ns = time.perf_counter_ns()
    observed_tic = game.get_episode_time()
    finished_ns = time.perf_counter_ns()
    natural_upper = before_tic + ((finished_ns - init_started_ns)*45 + 999_999_999)//1_000_000_000 + 1
    if (type(observed_tic) is not int or observed_tic != expected_tic or finished_ns < init_started_ns
            or natural_upper >= expected_tic):
        raise ValueError('candidate restored tic differs or load effect is unverified')
    return observed_tic, {'before_load_tic': before_tic, 'init_started_ns': init_started_ns,
        'load_started_ns': load_started_ns, 'load_returned_ns': load_returned_ns,
        'getter_finished_ns': finished_ns, 'observed_restore_tic': observed_tic,
        'natural_progress_upper_tic': natural_upper, 'assumed_max_tics_per_second': 45}


def admit_verified_setup_program(steps, expected_hash, input_claimed):
    if type(steps) is not list or not steps or any(type(step) is not dict for step in steps):
        raise ValueError('invalid verified fixture setup program')
    if any(step.get('op') not in ('hold', 'coast', 'observe') for step in steps):
        raise ValueError('verified fixture setup only permits movement and passive steps')
    holds = [step for step in steps if step.get('op') == 'hold']
    if not holds:
        return input_claimed
    if (input_claimed or len(holds) != 1 or type(holds[0].get('keys')) is not list
            or holds[0]['keys'] not in ([key] for key in ('a', 'd', 'Up', 'Down', 'Left', 'Right'))
            or type(holds[0].get('duration_ms')) is not int
            or not 1 <= holds[0]['duration_ms'] <= 600
            or program_sha256(steps) != expected_hash):
        raise ValueError('fixture setup movement is not the one predeclared attempt')
    return True


def admit_fresh_neutral_program(steps, expected_hash, claimed):
    if (claimed or type(steps) is not list or not steps or len(steps) > 16
            or any(type(step) is not dict or set(step) != {'op', 'duration_ms', 'sample_ms'}
                   or step['op'] != 'coast' or type(step['duration_ms']) is not int
                   or not 1 <= step['duration_ms'] <= 5000
                   or type(step['sample_ms']) is not int or not 50 <= step['sample_ms'] <= 1000
                   for step in steps)
            or sum(step['duration_ms'] for step in steps) > 12000
            or program_sha256(steps) != expected_hash):
        raise ValueError('fresh fixture requires one fixed passive coast')
    return True


def validate_fresh_neutral_completed(events, sources, program_hash, last_accepted, last_terminal, backend):
    accepted = [row for row in events if row.get('event') == 'accepted']
    terminals = [row for row in events if row.get('event') == 'terminal']
    forbidden = {'input_admission', 'pointer_admission', 'input_release_transition', 'input_released'}
    if (len(accepted) != 1 or len(terminals) != 1
            or type(last_accepted) is not dict or type(last_terminal) is not dict
            or accepted[0] != {k: v for k, v in last_accepted.items() if k != 'emit_ns'}
            or terminals[0] != {k: v for k, v in last_terminal.items() if k != 'emit_ns'} or accepted[0].get('program_sha256') != program_hash
            or any(row.get('event') in forbidden for row in events)):
        raise ValueError('fresh fixture coast or input evidence differs')
    identifier = accepted[0].get('id')
    source = sources.get(identifier)
    terminal = terminals[0]
    if (type(identifier) is not str or not identifier or terminal.get('id') != identifier
            or terminal.get('status') != 'completed' or type(source) is not dict
            or type(source.get('renewal_owner_id')) is not str or not source['renewal_owner_id']
            or type(source.get('input_owner_generation')) is not int
            or getattr(getattr(backend, 'owner', None), 'owner_id', None) != source['renewal_owner_id']
            or type(getattr(backend, '_owner_generation', None)) is not int
            or backend._owner_generation != source['input_owner_generation']
            or terminal.get('input_owner_id') != source['renewal_owner_id']
            or type(terminal.get('input_owner_generation')) is not int
            or terminal['input_owner_generation'] != source['input_owner_generation']
            or not operation_release_verified(identifier, events)):
        raise ValueError('fresh fixture coast completion or release is unverified')


def require_fresh_neutral_deadline(source, owner_state, checked_ns, clock_deadline_ns, *, now):
    capture = source.get('capture_ns') if type(source) is dict else None
    sampled = owner_state.get('sample_finished_ns') if type(owner_state) is dict else None
    if (any(type(value) is not int for value in (capture, sampled, checked_ns, clock_deadline_ns, now))
            or not capture <= checked_ns <= sampled <= now
            or now >= min(clock_deadline_ns, checked_ns + 1_000_000_000,
                          sampled + 1_000_000_000, capture + 2_000_000_000)):
        raise ValueError('fresh fixture source or owner evidence expired')


def validate_fresh_neutral_snapshot(events, latest):
    typed = [row for row in events if row.get('event') == 'typed_observation']
    frames = [row for row in events if row.get('event') == 'observation']
    if (len(typed) < 2 or len(typed) != len(frames) or type(latest) is not dict
            or frames[-1] != {k: v for k, v in latest.items() if k != 'emit_ns'}
            or frames[0].get('id') != 'initial' or frames[-1].get('id') != 'fixture-source'):
        raise ValueError('fresh fixture observation coverage incomplete')
    baseline = None
    previous_capture = previous_sequence = None
    owner = generation = surface = process_digest = window_digest = None
    for early, frame in zip(typed, frames):
        fields = ('id', 'sequence', 'capture_ns', 'frame_rgb_sha256', 'pointer_binding',
                  'input_owner_generation', 'renewal_owner_id', 'target_process_identity',
                  'target_renewal_window_identity')
        if any(early.get(key) != frame.get(key) for key in fields):
            raise ValueError('fresh fixture typed and full observations differ')
        seq, capture = frame.get('sequence'), frame.get('capture_ns')
        binding, identity = frame.get('pointer_binding'), frame.get('target_process_identity')
        window = frame.get('target_renewal_window_identity')
        rgb = frame.get('frame_rgb_sha256')
        if (type(seq) is not int or type(capture) is not int or capture <= 0
                or type(rgb) is not str or re.fullmatch('[0-9a-f]{64}', rgb) is None
                or type(binding) is not dict or type(binding.get('surface')) is not int
                or binding.get('focus') != binding['surface'] or type(identity) is not dict
                or identity.get('sequence') != seq or identity.get('surface') != binding['surface']
                or type(identity.get('digest')) is not str or re.fullmatch('[0-9a-f]{64}', identity['digest']) is None
                or type(window) is not dict or window.get('sequence') != seq
                or window.get('surface') != binding['surface'] or type(window.get('digest')) is not str
                or re.fullmatch('[0-9a-f]{64}', window['digest']) is None or frame.get('exact') is not True
                or frame.get('focus_samples_match') is not True
                or frame.get('input_focus_before') != binding['focus']
                or frame.get('input_focus_after') != binding['focus']
                or type(frame.get('renewal_owner_id')) is not str or not frame['renewal_owner_id']
                or type(frame.get('input_owner_generation')) is not int):
            raise ValueError('fresh fixture observation identity is invalid')
        if previous_capture is not None and (seq != previous_sequence + 1 or capture <= previous_capture
                                             or capture - previous_capture > 3_000_000_000):
            raise ValueError('fresh fixture observation sequence has a gap')
        if owner is None:
            owner, generation, surface = frame['renewal_owner_id'], frame['input_owner_generation'], binding['surface']
            process_digest, window_digest = identity['digest'], window['digest']
        if (frame['renewal_owner_id'], frame['input_owner_generation'], binding['surface']) != (owner, generation, surface) or identity['digest'] != process_digest or window['digest'] != window_digest:
            raise ValueError('fresh fixture owner, target or surface changed')
        signals = early.get('signals', {})
        for name in ('health', 'ammo'):
            signal = signals.get(name, {})
            if (signal.get('status') != 'observed' or type(signal.get('value')) is not int
                    or signal.get('signal_id') != name or signal.get('sequence') != seq
                    or signal.get('capture_ns') != capture or signal.get('binding') != binding):
                raise ValueError('fresh fixture HUD is unreadable or mismatched')
        health = signals['health']['value']
        if health <= 0 or (baseline is not None and health < baseline):
            raise ValueError('fresh fixture health decreased')
        if baseline is None:
            baseline = health
        previous_capture, previous_sequence = capture, seq


def fixture_clock_fields(candidate_setup, post_save_refresh_tic):
    if type(post_save_refresh_tic) is not int or post_save_refresh_tic < 0:
        raise ValueError('post-save refresh tic must be a nonnegative integer')
    if not candidate_setup:
        return {'episode_tic': post_save_refresh_tic}
    return {'episode_tic': None, 'post_save_refresh_episode_tic': post_save_refresh_tic,
            'restored_episode_tic': None, 'restored_episode_tic_status': 'unmeasured'}


def write_verified_fixture(save_path, expected_directory, engine_save, source_image, fixture):
    parent = save_path.parent
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(parent, flags)
    try:
        current = os.fstat(fd)
        if (current.st_dev, current.st_ino) != expected_directory:
            raise ValueError('verified fixture directory changed')
        pinned = Path('/proc/self/fd') / str(fd)
        saved = pinned / save_path.name
        source = pinned / (save_path.stem + '.source.png')
        manifest = pinned / save_path.with_suffix('.json').name
        copy_file_exclusive(engine_save, saved)
        copy_file_exclusive(source_image, source)
        fixture['save_sha256'] = file_sha256(saved)
        fixture['source_frame_sha256'] = file_sha256(source)
        with manifest.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(fixture, stream, indent=2)
            stream.write('\n')
        current_path = parent.stat(follow_symlinks=False)
        if (current_path.st_dev, current_path.st_ino) != expected_directory:
            raise ValueError('verified fixture directory changed before publication')
    finally:
        os.close(fd)


def validate_setup_completed(events, sources, gate, program_hash, last_accepted, last_terminal, backend):
    if getattr(gate, 'first_press_observed', False) is not True:
        raise ValueError("verified fixture setup requires a confirmed first press")
    matches = [row for row in events if row.get('event') == 'accepted'
               and row.get('program_sha256') == program_hash]
    if len(matches) != 1:
        raise ValueError("verified fixture setup requires the exact accepted movement")
    accepted = matches[0]
    identifier = accepted.get('id')
    terminal_rows = [row for row in events if row.get('event') == 'terminal' and row.get('id') == identifier]
    source = sources.get(identifier)
    admissions = [row for row in events if row.get('event') == 'input_admission' and row.get('id') == identifier]
    if (len(terminal_rows) != 1 or terminal_rows[0].get('status') != 'completed'
            or type(source) is not dict or type(source.get('renewal_owner_id')) is not str
            or not source['renewal_owner_id'] or type(source.get('input_owner_generation')) is not int
            or getattr(getattr(backend, 'owner', None), 'owner_id', None) != source['renewal_owner_id']
            or type(getattr(backend, '_owner_generation', None)) is not int
            or backend._owner_generation != source['input_owner_generation']
            or type(getattr(gate, 'first_press', None)) is not tuple
            or len(gate.first_press) != 3 or gate.first_press[:2] != (identifier, source['renewal_owner_id'])
            or getattr(gate, 'first_press_intent', None) != accepted.get('intent_token')
            or terminal_rows[0].get('input_owner_id') != source['renewal_owner_id']
            or type(terminal_rows[0].get('input_owner_generation')) is not int
            or terminal_rows[0]['input_owner_generation'] != source['input_owner_generation']
            or any(row.get('event') == 'input_admission' and row.get('id') != identifier for row in events)
            or not admissions or any(row.get('owner_id') != source['renewal_owner_id'] for row in admissions)
            or not operation_release_verified(identifier, events, require_intent=True)):
        raise ValueError("verified fixture movement or its release is unverified")
    last_source = sources.get(last_terminal.get('id')) if type(last_terminal) is dict else None
    last_has_input = any(row.get('id') == last_terminal.get('id') and
                         row.get('event') in ('input_admission', 'input_release_transition', 'input_released')
                         for row in events) if type(last_terminal) is dict else False
    if (type(last_accepted) is not dict or type(last_terminal) is not dict
            or last_accepted.get('id') != last_terminal.get('id')
            or last_terminal.get('status') != 'completed'
            or type(last_source) is not dict or type(last_source.get('renewal_owner_id')) is not str
            or not last_source['renewal_owner_id']
            or type(last_source.get('input_owner_generation')) is not int
            or type(last_terminal.get('input_owner_generation')) is not int
            or last_terminal.get('input_owner_id') != last_source['renewal_owner_id']
            or last_terminal['input_owner_generation'] != last_source['input_owner_generation']
            or not operation_release_verified(last_terminal.get('id'), events, require_intent=last_has_input)):
        raise ValueError("last fixture setup program did not complete and release")


def make_executor_factory(emit):
    if not callable(emit):
        raise TypeError("executor event sink must be callable")
    return lambda backend: Executor(backend, emit)


def wait_for_stable_file(path, timeout=5):
    path = Path(path)
    deadline = time.monotonic() + timeout
    previous = None
    while time.monotonic() < deadline:
        if path.is_file() and path.stat().st_size > 0:
            current = (path.stat().st_size, path.stat().st_mtime_ns)
            if current == previous:
                return current[0]
            previous = current
        time.sleep(.05)
    raise TimeoutError(f"save file did not stabilize: {path}")


def validate_fixture_manifest(manifest_path, vizdoom_version, iwad_sha256, skill):
    manifest_path = Path(manifest_path).resolve()
    fixture = json.loads(manifest_path.read_text(encoding="utf-8"))
    if fixture.get('schema') == CANDIDATE_FIXTURE_SCHEMA:
        raise ValueError('fixture candidate is not qualified for loading')
    if fixture.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("unsupported fixture manifest")
    if fixture.get('setup_mode') == 'verified_loaded_fixture_setup_v1':
        raise ValueError('fixture candidate is not qualified for loading')
    if fixture.get("map") != "MAP01" or fixture.get("skill") != skill:
        raise ValueError("fixture map/skill mismatch")
    if fixture.get("vizdoom") != vizdoom_version or fixture.get("iwad_sha256") != iwad_sha256:
        raise ValueError("fixture engine/IWAD mismatch")
    save_name = fixture.get("save_file")
    if (not isinstance(save_name, str) or Path(save_name).name != save_name or
            Path(save_name).suffix.lower() != ".png"):
        raise ValueError("fixture save_file must be a sibling PNG basename")
    save_path = (manifest_path.parent / save_name).resolve()
    if file_sha256(save_path) != fixture.get("save_sha256"):
        raise ValueError("fixture save hash mismatch")
    frame_name = fixture.get("source_frame")
    if not isinstance(frame_name, str) or Path(frame_name).name != frame_name:
        raise ValueError("fixture source_frame must be a sibling basename")
    frame_path = (manifest_path.parent / frame_name).resolve()
    if file_sha256(frame_path) != fixture.get("source_frame_sha256"):
        raise ValueError("fixture source-frame hash mismatch")
    if fixture.get("setup_input_contract") != SETUP_INPUT_CONTRACT:
        raise ValueError("fixture setup-input contract mismatch")
    source = fixture.get("source_observation")
    if not isinstance(fixture.get("episode_tic"), int) or fixture["episode_tic"] < 0:
        raise ValueError("fixture episode tic missing")
    if not isinstance(source, dict) or source.get("event") != "observation" or source.get("exact") is not True:
        raise ValueError("fixture exact source observation missing")
    return fixture, save_path


def load_bound_fixture(game, session, manifest_path, engine, iwad_sha, skill,
                       candidate_preflight, post_load_gate, candidate_init_started_ns):
    manifest_path = Path(manifest_path).resolve()
    if candidate_preflight is None:
        fixture, save_path = validate_fixture_manifest(manifest_path, engine, iwad_sha, skill)
        binding = None
        expected_load_tic = fixture['episode_tic']
    else:
        if post_load_gate is None:
            raise ValueError('candidate setup requires a post-load clock gate')
        fixture, save_path, binding = candidate_preflight
        expected_load_tic = binding['expected_restore_tic']
        if file_sha256(manifest_path) != binding['candidate_manifest_sha256']:
            raise ValueError('candidate manifest changed after setup preflight')
    before_load_tic = game.get_episode_time()
    engine_load_path = session.tmp / 'fixture-load.png'
    if binding is None:
        shutil.copy2(save_path, engine_load_path)
        game.load(str(engine_load_path))
        observed_load_tic = game.get_episode_time()
    else:
        observed_load_tic, candidate_load_check = load_setup_candidate(
            game, save_path, engine_load_path, binding, before_load_tic, candidate_init_started_ns)
    loaded = {'manifest': str(manifest_path),
              'manifest_sha256': file_sha256(manifest_path) if binding is None else binding['candidate_manifest_sha256'],
              'save': str(save_path), 'save_sha256': fixture['save_sha256'],
              'before_load_tic': before_load_tic, 'after_load_tic': observed_load_tic,
              'source_episode_tic': fixture['episode_tic'] if binding is None else None,
              'setup_input_contract': fixture['setup_input_contract']}
    if binding is not None:
        loaded['setup_candidate_evidence'] = binding
        loaded['observed_restore_tic'] = observed_load_tic
        loaded['candidate_load_check'] = candidate_load_check
    gate_result = (post_load_gate.after_load(game, session, expected_tic=expected_load_tic)
                   if post_load_gate is not None else None)
    return loaded, gate_result


def close_before_control_effect(executor, out, emit, operation):
    """Retire the owned intent before engine refresh or fixture publication.

    This is a logical caller fence, not a physical or global-neutrality claim.
    In particular close() can return with an unstarted ambiguous admission or
    a retained failed release. Neither state permits this effect boundary.
    """
    executor.close()
    with executor.lock:
        obligation = executor.release_obligation_snapshot()
        active_intent = executor.active[0] if executor.active is not None else None
        closed = executor.closed
    backend=getattr(executor,'backend',None)
    custody=getattr(backend,'executor_custody_snapshot',lambda:{})()
    owner_service_obligation=custody.get('owner_service_obligation')
    if closed and active_intent is None and obligation is None and owner_service_obligation is None:
        return
    failure = {
        "event": "control_boundary_failed",
        "schema": "map01-control-retirement-failure-v1",
        "operation": operation,
        "executor_closed": closed,
        "active_intent": active_intent,
        "release_obligation": obligation,
        "owner_service_obligation":owner_service_obligation,
        "input_recovery_required": True,
        "task_effect": "unknown",
        "grants_input_authority": False,
    }
    # Preserve failure before the external sink; collision/save/delivery errors
    # also terminate this path before game refresh, Save or success publication.
    with (Path(out) / "control-boundary-failure.json").open(
            "x", encoding="utf-8", newline="\n") as stream:
        json.dump(failure, stream, indent=2)
        stream.write("\n")
    emit(failure)
    raise RuntimeError("input retirement is unresolved; control effect refused")


def main(*, post_load_gate=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--skill", type=int, choices=range(1,6), default=1)
    parser.add_argument("--fixture-out", type=Path)
    parser.add_argument("--load-fixture-manifest", type=Path)
    parser.add_argument("--verified-fixture-setup", action="store_true")
    parser.add_argument("--fresh-neutral-fixture-setup", action="store_true")
    parser.add_argument("--fixture-setup-program-sha256")
    parser.add_argument("--candidate-setup-evidence", type=Path)
    parser.add_argument("--candidate-setup-evidence-sha256")
    parser.add_argument("--synthetic-exit-pwad", type=Path)
    parser.add_argument("--synthetic-exit-arm", choices=("control","use"))
    parser.add_argument("--synthetic-exit-refresh", action="store_true")
    parser.add_argument("--door-task-arm", choices=("control","use"))
    parser.add_argument("--door-task-traverse", action="store_true")
    parser.add_argument("--door-task-exit", action="store_true")
    parser.add_argument("--door-task-exit-arm", choices=("control","use"))
    parser.add_argument("--door-expected-manifest-sha256")
    parser.add_argument("--door-expected-save-sha256")
    parser.add_argument("--door-expected-iwad-sha256")
    parser.add_argument("--door-expected-restore-tic", type=int)
    parser.add_argument("--renewal-passive-observer", action="store_true")
    args = parser.parse_args()
    try:
        validate_synthetic_exit_calibration(args, post_load_gate)
        setup_directory_identity = validate_verified_fixture_setup(args, post_load_gate)
    except ValueError as error:
        parser.error(str(error))
    if args.fixture_out is not None and args.fixture_out.suffix.lower() != ".png":
        parser.error("fixture-out must be a .png save container")
    candidate_preflight = None
    if args.candidate_setup_evidence is not None:
        from map01_candidate_setup_evidence_v1 import verify_setup_candidate
        candidate_iwad = Path(vd.__file__).parent / "freedoom2.wad"
        candidate_preflight = verify_setup_candidate(
            args.load_fixture_manifest, args.candidate_setup_evidence,
            args.candidate_setup_evidence_sha256, vd.__version__, file_sha256(candidate_iwad),
            args.skill, args.seed, args.timeout_seconds, candidate_iwad)
        if args.door_task_arm is not None:
            validate_door_candidate_binding(args,candidate_preflight[2],file_sha256(candidate_iwad))
    args.out.mkdir(parents=True, exist_ok=False)
    private_scenario=(copy_synthetic_exit_scenario(args.synthetic_exit_pwad,args.out/'synthetic-exit-calibration.wad')
                      if args.synthetic_exit_pwad is not None else None)
    lock = threading.RLock()
    session = game = executor = backend = None
    control_started_ns = None
    latest_observation = None
    owner_generation_protocol = InputOwnerGenerationProtocol()

    probe_delivery = None
    fresh_gate = None
    last_terminal = None
    last_accepted = None
    setup_events = []
    setup_sources = {}
    setup_input_claimed = False
    synthetic_heartbeat_count = 0
    synthetic_heartbeat_revision = None
    door_coordinator = None
    door_scorer = None
    if args.synthetic_exit_pwad is not None:
        from map01_synthetic_exit_scorer import SyntheticExitScorer
        door_scorer=SyntheticExitScorer(args.out / 'door-sector-private.jsonl')
    elif args.door_task_arm is not None:
        from map01_door_sector_scorer import DoorSectorScorer
        door_scorer=DoorSectorScorer(args.out / 'door-sector-private.jsonl',traverse=args.door_task_traverse,exit_probe=args.door_task_exit)

    def emit(row):
        nonlocal last_terminal, last_accepted
        if row.get("event") == "accepted":
            last_accepted = row
        if row.get("event") == "terminal":
            last_terminal = row
        nonlocal latest_observation
        with lock:
            if row.get("event") == "observation":
                latest_observation = dict(row)
            owner_generation_protocol.record_terminal(row, backend)
            event_gate=post_load_gate if post_load_gate is not None else (fresh_gate if args.synthetic_exit_pwad is not None else None)
            if event_gate is not None:
                try:
                    event_gate.record(row)
                except Exception as error:
                    # The executor releases input after emit raises. Do not do
                    # disk I/O here: attach the receipt to the exception that
                    # becomes the terminal error after the release attempt.
                    rejected = json.dumps(row, allow_nan=False, sort_keys=True)
                    raise RuntimeError(f"post-load gate rejected event: {rejected}; "
                                       f"{type(error).__name__}: {error}") from error
            if door_coordinator is not None:
                door_coordinator.record(row)
            if args.verified_fixture_setup or args.fresh_neutral_fixture_setup:
                if row.get('event') == 'accepted':
                    setup_sources[row['id']] = deepcopy(latest_observation)
                setup_events.append(deepcopy(row))
            row["emit_ns"] = time.perf_counter_ns()
            encoded = json.dumps(row)
            with (args.out / "events.jsonl").open("a") as stream:
                stream.write(encoded + "\n")
            with (args.out / "delivered.jsonl").open("a") as stream:
                stream.write(encoded + "\n")
            if row.get("event") == "typed_observation":
                # emit_ns is producer-side log start. The handoff marker is
                # after both raw appends and before stdout serialization/write.
                row["stdout_handoff_started_ns"] = time.perf_counter_ns()
                print(json.dumps(row), flush=True)
            else:
                print(encoded, flush=True)

    sources = {}
    for path in (Path(__file__), HERE.parent / "live_control/session_v8.py",
                 HERE.parent / "live_control/executor_v12.py",
                 HERE.parent / "live_control/executor_v11.py",
                 HERE.parent / "live_control/executor_v5.py",
                 HERE.parent / "live_control/lease_release_v1.py",
                 HERE.parent / "live_control/lease_cause_v2.py",
                 HERE.parent / "live_control/lease_cause_v1.py",
                 HERE.parent / "live_control/lease.py",
                 HERE.parent / "live_control/input_owner_v10.py",
                 HERE.parent / "live_control/input_owner_v5.py",
                 HERE.parent / "live_control/session_v9.py",
                 HERE.parent / "live_control/session_v10.py",
                 HERE.parent / "live_control/coast_backend_v1.py",
                 HERE / "map01_synthetic_exit_refresh.py",
                 HERE / "doom_typed_release_backend_v1.py",
                 HERE / "doom_typed_coast_backend_v1.py",
                 HERE / "doom_typed_observation_v1.py",
                 HERE / "input_owner_generation_protocol_v1.py",
                 HERE / "doom_hud_signal_v3.py",
                 HERE / "doom_hud_signal_v2.py",
                 HERE / "doom_hud_signal_v1.py"):
        sources[str(path.relative_to(HERE.parent))] = hashlib.sha256(path.read_bytes()).hexdigest()
    if post_load_gate is not None or args.fresh_neutral_fixture_setup or args.synthetic_exit_pwad is not None:
        sources["doom/map01_post_load_gate_v1.py"] = file_sha256(HERE / "map01_post_load_gate_v1.py")
    if candidate_preflight is not None:
        sources["doom/map01_candidate_setup_evidence_v1.py"] = file_sha256(HERE / "map01_candidate_setup_evidence_v1.py")
    if args.door_task_arm is not None or args.synthetic_exit_pwad is not None:
        for name in ('map01_door_coordinator.py','map01_door_journal.py','map01_door_task_contract.py','map01_door_sector_scorer.py'):
            sources['doom/'+name] = file_sha256(HERE/name)
    if args.synthetic_exit_pwad is not None:
        sources['doom/map01_synthetic_exit_scorer.py']=file_sha256(HERE/'map01_synthetic_exit_scorer.py')
    (args.out / "sources.json").write_text(json.dumps(sources, indent=2))
    try:
        with (args.out / "setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            if post_load_gate is not None or args.fresh_neutral_fixture_setup or args.synthetic_exit_pwad is not None:
                # An unset bus address invites X11 autolaunch. Suppress it
                # before Xvfb/Openbox inherit the environment.
                os.environ["DBUS_SESSION_BUS_ADDRESS"] = "disabled:"
            session = suite.Session()
            if post_load_gate is not None or args.fresh_neutral_fixture_setup or args.synthetic_exit_pwad is not None:
                # The shared X11 helper strips the inherited address from its
                # copied environment. Keep subsequent session subprocesses isolated.
                session.env["DBUS_SESSION_BUS_ADDRESS"] = os.environ["DBUS_SESSION_BUS_ADDRESS"]
            atom = session.d.intern_atom("_NET_SUPPORTING_WM_CHECK")
            session._wait(lambda: session.d.screen().root.get_full_property(atom, 0) is not None,
                          4, "WM readiness")
            for key in ("DISPLAY", "XAUTHORITY", "HOME", "XDG_CONFIG_HOME",
                        "XDG_CACHE_HOME", "XDG_RUNTIME_DIR"):
                os.environ[key] = session.env[key]
            os.environ["SDL_VIDEODRIVER"] = "x11"
            os.environ.pop("WAYLAND_DISPLAY", None)
            package = Path(vd.__file__).parent
            iwad = package / "freedoom2.wad"
            if args.synthetic_exit_pwad is not None:
                if vd.__version__!='1.3.0':raise ValueError('synthetic calibration engine differs')
                iwad=copy_pinned_calibration_file(iwad,args.out/'synthetic-iwad.wad',
                    'a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b')
            config = session.tmp / "doom.ini"
            config.write_text(
                "[Doom.Bindings]\n"
                "leftarrow=+left\nrightarrow=+right\n"
                "uparrow=+forward\ndownarrow=+back\n"
                "w=+forward\ns=+back\na=+moveleft\nd=+moveright\n"
                "e=+use\nenter=+use\nspace=+attack\nctrl=+attack\n"
                "shift=+speed\n", encoding="utf-8")
            game = vd.DoomGame()
            game.set_doom_game_path(str(iwad))
            game.set_doom_scenario_path(str(private_scenario) if private_scenario is not None else '')
            game.set_doom_map("MAP01")
            game.set_doom_config_path(str(config))
            game.set_mode(vd.Mode.ASYNC_SPECTATOR)
            game.set_ticrate(35)
            game.set_seed(args.seed)
            game.set_doom_skill(args.skill)
            game.set_episode_timeout(35 * args.timeout_seconds)
            game.set_window_visible(True)
            game.set_console_enabled(False)
            game.set_sound_enabled(False)
            if args.door_task_arm is not None:
                game.set_sectors_info_enabled(True)
            game.set_screen_resolution(vd.ScreenResolution.RES_640X480)
            game.set_render_hud(True)
            game.set_render_crosshair(True)
            game.set_render_all_frames(True)
            game.set_available_buttons([
                vd.Button.TURN_LEFT, vd.Button.TURN_RIGHT, vd.Button.MOVE_FORWARD,
                vd.Button.MOVE_BACKWARD, vd.Button.MOVE_LEFT, vd.Button.MOVE_RIGHT,
                vd.Button.ATTACK, vd.Button.USE, vd.Button.SPEED])
            game.set_available_game_variables(door_game_variables(vd.GameVariable,args.door_task_traverse))
            candidate_init_started_ns = time.perf_counter_ns() if candidate_preflight is not None else None
            game.init()
        from PIL import ImageGrab
        time.sleep(0.3)
        windows = session.windows()
        (args.out / "windows.txt").write_text(windows)
        ImageGrab.grab(xdisplay=session.name).save(args.out / "setup-screen.png")
        candidates = [line for line in windows.splitlines() if "doom" in line.lower()]
        if len(candidates) != 1:
            raise RuntimeError("Expected one Doom window: " + repr(windows))
        session.focus(" ".join(candidates[0].split()[3:]))
        if args.fresh_neutral_fixture_setup or args.synthetic_exit_pwad is not None:
            from map01_post_load_gate_v1 import PostLoadGate
            fresh_gate = PostLoadGate(args.out, args.timeout_seconds)
            fresh_gate.path = args.out / 'fresh-start-clock-gate.jsonl'
            before = game.get_episode_time()
            fresh_start = fresh_gate.after_load(game, session, expected_tic=before)
            after = fresh_start['last_refresh_tic']
            elapsed = fresh_start['delayed_elapsed_ns'] / 1e9
        else:
            game.advance_action(1, True)
            before = game.get_episode_time()
            wall = time.perf_counter()
            time.sleep(2)
            game.advance_action(1, True)
            after = game.get_episode_time()
            elapsed = time.perf_counter() - wall
        if args.synthetic_exit_pwad is None:
            iwad = Path(vd.__file__).parent / "freedoom2.wad"
        iwad_sha256 = file_sha256(iwad)
        loaded_fixture = None
        startup_gate = {}
        if args.synthetic_exit_pwad is not None:
            startup_gate['post_load_clock_gate']=fresh_start
            startup_gate['synthetic_exit_calibration']={'pwad_sha256':SYNTHETIC_EXIT_PWAD_SHA256,
                'iwad_sha256':iwad_sha256,'arm':args.synthetic_exit_arm,'scope':'synthetic calibration only'}
        if args.load_fixture_manifest is not None:
            loaded_fixture, gate_result = load_bound_fixture(
                game, session, args.load_fixture_manifest, vd.__version__, iwad_sha256, args.skill,
                candidate_preflight, post_load_gate, candidate_init_started_ns)
            if post_load_gate is not None:
                startup_gate['post_load_clock_gate'] = gate_result
        environment = {"vizdoom": vd.__version__, "mode": str(game.get_mode()),
            "ticrate": game.get_ticrate(), "seed": args.seed, "map": "MAP01", "skill": args.skill,
            "scenario_path": str(private_scenario) if private_scenario is not None else None,
            "scenario_sha256": SYNTHETIC_EXIT_PWAD_SHA256 if args.synthetic_exit_pwad is not None else None, "iwad": str(iwad),
            "iwad_sha256": iwad_sha256,
            "loaded_fixture": loaded_fixture,
            "sound_for_controller": False, "episode_timeout_seconds": args.timeout_seconds}
        if post_load_gate is not None or args.fresh_neutral_fixture_setup or args.synthetic_exit_pwad is not None:
            environment["dbus_session_bus_address"] = session.env["DBUS_SESSION_BUS_ADDRESS"]
        (args.out / "environment.json").write_text(json.dumps(environment, indent=2))
        emit({"event": "clock_probe", "before_tic": before, "after_tic": after,
              "wall_seconds": elapsed, "no_advance_calls_during_wait": True,
              "refresh_calls_before_control": 4 if args.fresh_neutral_fixture_setup or args.synthetic_exit_pwad is not None else 2})
        with (args.out / "backend-setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            signal_readers = {
                name: DoomStatusNumberReader(iwad, signal_id=name)
                for name in ("health", "ammo")}
            backend = Backend(session, args.out, emit, signal_readers)
        executor_factory = make_executor_factory(emit)
        executor = executor_factory(backend)
        if args.door_task_arm is not None or args.synthetic_exit_pwad is not None:
            from map01_door_coordinator import DoorCoordinator
            coordinator_gate=fresh_gate if args.synthetic_exit_pwad is not None else post_load_gate
            if (coordinator_gate is None or getattr(backend,'owned_service',None) is None
                    or getattr(backend,'owner',None) is None):
                raise ValueError('door trial requires the owned input service and post-load gate')
            door_coordinator=DoorCoordinator(args.door_task_arm or 'use',coordinator_gate,backend,executor,time.perf_counter_ns,
                                             traverse=args.door_task_traverse or args.synthetic_exit_pwad is not None,
                                             exit_probe=args.door_task_exit or args.synthetic_exit_pwad is not None,
                                             exit_arm=args.synthetic_exit_arm if args.synthetic_exit_pwad is not None else args.door_task_exit_arm,
                                             direct_exit=args.synthetic_exit_pwad is not None)
        operations = ["submit", "cancel", "clock", "finish"]
        if args.renewal_passive_observer:
            if (not callable(getattr(backend, "capture_cover_renewal", None))
                    or getattr(backend, "renewal_window_identity", None) is None):
                raise ValueError("renewal observer requires the process/window identity backend")

            def check_probe_source(command):
                return settled_cover_probe_source(executor, backend, last_terminal, last_accepted, command)

            probe_delivery = PassiveProbeDelivery(check_probe_source, backend.capture_cover_renewal, emit)
            operations.append("probe_cover_renewal")
        if (callable(getattr(backend, "rotate_input_owner_after_cancel", None))
                     and getattr(backend, "window_identity", None) is None
                     and getattr(backend, "_provided_input_owner", None) is None):
            operations.append("rotate_input_owner")
            operations.append("refresh_owner_source")
        if args.fixture_out is not None:
            operations.append("save_fixture")
        if args.fresh_neutral_fixture_setup:
            operations = ["submit", "cancel", "clock", "finish", "save_fixture"]
        if door_coordinator is not None:
            operations = ["submit", "door-settle", "cancel", "clock", "finish"]
        prohibited = ["pause", "API action selection", "automap", "object labels", "sector labels"]
        if args.fixture_out is None:
            prohibited.append("save state")
        emit({"event": "ready", "presentation": "full",
              "operations": operations,
              "command_contract": {
                  "submit": {"op": "submit", "id": "new nonempty string",
                      "expected_sequence": "latest integer observation sequence",
                      "valid_until_ns": "runtime monotonic ns, at most 30s ahead",
                      "steps": ([{"op": "coast", "duration_ms": "1-5000", "sample_ms": "50-1000"}]
                                if args.fresh_neutral_fixture_setup else
                                [{"op": "hold", "keys": ["1-4 exact binding names"],
                                  "duration_ms": "1-5000"}, {"op": "observe"}])},
                  "coast": {"op": "coast", "duration_ms": "1-5000",
                            "sample_ms": "50-1000", "input_authority": False},
                  "rotate_input_owner": {"op": "rotate_input_owner",
                      "id": "previously published cancelled terminal with verified empty release"},
                  "refresh_owner_source": {"op": "refresh_owner_source",
                      "id": "terminal id of the just-rotated owner generation",
                      "input_authority": False},
                  "limits": {"steps": "1-16", "total_hold_ms": 10000,
                             "implicit_queue": False},
                  "accepted_attestation": "SHA-256 of canonical validated step JSON"},
              "observation_contract": {
                  "early": "doom-typed-observation-v1 before transport/artifact publication",
                  "later": "exact full observation with matching epoch and RGB SHA-256",
                  "typed_signals": ["health", "ammo"],
                  "early_grants_input_authority": False},
              "release_contract": {
                  "early": "lease-bound input_released after independent owner verifies empty input",
                  "terminal": "program lifecycle closes separately after in-flight work and final cleanup",
                  "early_grants_input_authority": False},
              "task": ("Synthetic exit calibration" if args.synthetic_exit_pwad is not None else "Exit continuously advancing Freedoom MAP01"),
              "bindings": {"Left/Right": "turn", "Up or w": "forward",
                           "Down or s": "back", "a/d": "strafe",
                           "e or Return": "use", "space": "attack",
                           "Shift_L": "run"},
              "fixture": loaded_fixture,
              "prohibited": prohibited, **startup_gate})
        backend.snapshot("initial", 0)
        control_started_ns = time.perf_counter_ns()
        for line in sys.stdin:
            try:
                command = json.loads(line)
                emit({"event": "command", "command": command,
                      "received_ns": time.perf_counter_ns()})
                if args.fresh_neutral_fixture_setup and command.get('op') not in ('submit', 'cancel', 'clock', 'finish', 'save_fixture'):
                    raise ValueError('operation unavailable in fresh neutral setup')
                if door_coordinator is not None:
                    from map01_door_coordinator import route_door_command
                    with lock:
                        door_source=deepcopy(latest_observation)
                    operation_id=door_coordinator.pending
                    if (command.get('op')=='finish'
                            and (door_scorer.failed or door_scorer.index!=len(door_scorer.STAGES))):
                        raise ValueError('door sector observations are incomplete')
                    result=route_door_command(command,door_coordinator,door_source)
                    if result!='passthrough':
                        if command.get('op')=='door-settle' and result=='DONE':
                            try:
                                _,door_terminal=door_coordinator.journal.completion(operation_id)
                                door_scorer.sample(operation_id,game,door_terminal['terminal_ns'],
                                                   lambda:door_coordinator.gate.neutral(session))
                            except Exception:
                                emit({'event':'door_settle','status':'HOLD',
                                      'operation_id':operation_id,'reason':'sector_sample_failed'})
                                raise
                        if command.get('op')=='door-settle':
                            emit({'event':'door_settle','status':result,
                                  'operation_id':operation_id,
                                  'reason':door_coordinator.journal.failure if result=='HOLD' else None})
                        if result=='HOLD':
                            raise RuntimeError('door trial evidence or completion is unverified')
                        continue
                if command["op"] == "probe_cover_renewal" and probe_delivery is not None:
                    probe_delivery.start(command)
                elif command["op"] == "submit":
                    if args.verified_fixture_setup:
                        setup_input_claimed = admit_verified_setup_program(
                            command['steps'], args.fixture_setup_program_sha256, setup_input_claimed)
                    if args.fresh_neutral_fixture_setup:
                        setup_input_claimed = admit_fresh_neutral_program(
                            command['steps'], args.fixture_setup_program_sha256, setup_input_claimed)
                        checked_ns = time.perf_counter_ns()
                        if checked_ns >= fresh_gate.clock_reserve_deadline_ns:
                            raise ValueError('fresh setup start clock reserve expired')
                        owner_id, generation, owner_state, engine_state = fresh_gate._owner_and_source(
                            backend, latest_observation, command, checked_ns)
                        if time.perf_counter_ns() >= fresh_gate.clock_reserve_deadline_ns:
                            raise ValueError('fresh setup start clock reserve expired')
                        emit({'event': 'fresh_start_admission', 'id': command['id'],
                              'checked_ns': checked_ns, 'owner_id': owner_id, 'generation': generation,
                              'owner_state': owner_state, 'engine_state': engine_state,
                              'clock_deadline_ns': fresh_gate.clock_reserve_deadline_ns})
                    approval = {}
                    if probe_delivery is not None:
                        if type(command.get("id")) is str and RENEWAL_ID.fullmatch(command["id"]):
                            approval["admission_deadline_ns"] = probe_delivery.consume(command)
                        probe_delivery.cancel()
                    if "renewal_approval" in command and not approval:
                        raise ValueError("unexpected renewal approval")
                    if post_load_gate is not None and not post_load_gate.first_press_observed:
                        if executor.active is not None:
                            raise ValueError("executor must be idle for startup gate")
                        first_press_deadline = post_load_gate.check_submit(
                            command, backend, latest_observation,
                            terminal=last_terminal, accepted=last_accepted)
                        if first_press_deadline is not None:
                            approval["admission_deadline_ns"] = min(
                                approval.get("admission_deadline_ns", first_press_deadline),
                                first_press_deadline)
                    if args.fresh_neutral_fixture_setup:
                        require_fresh_neutral_deadline(latest_observation, owner_state, checked_ns,
                                                       fresh_gate.clock_reserve_deadline_ns,
                                                       now=time.perf_counter_ns())
                    executor.submit(command["id"], command["steps"],
                                    command["expected_sequence"], command["valid_until_ns"], **approval)
                elif command["op"] == "cancel":
                    if probe_delivery is not None:
                        probe_delivery.cancel()
                    executor.cancel(command["id"])
                elif command["op"] == "clock":
                    if args.synthetic_exit_pwad is not None and door_coordinator is not None and door_coordinator.finished:
                        started=time.perf_counter_ns()
                        _,last_probe=door_coordinator.journal.completion('exit-probe')
                        if (synthetic_heartbeat_count>=4 or executor.active is not None
                                or type(last_probe.get('terminal_ns')) is not int
                                or not 0<=started-last_probe['terminal_ns']<12_000_000_000):
                            raise RuntimeError('synthetic heartbeat window unavailable')
                        synthetic_heartbeat_count+=1
                        with lock:
                            heartbeat_source=deepcopy(latest_observation)
                        receipt=synthetic_neutral_heartbeat(backend,door_coordinator.gate,session,
                            heartbeat_source,started=started,expected_revision=synthetic_heartbeat_revision)
                        if synthetic_heartbeat_revision is None:
                            synthetic_heartbeat_revision=receipt['owner_state']['revision']
                        emit({'event':'synthetic_owner_heartbeat','count':synthetic_heartbeat_count,**receipt})
                    emit({"event": "clock", "runtime_ns": time.perf_counter_ns(),
                          "sequence": backend.sequence})
                elif command["op"] == "rotate_input_owner":
                    if args.verified_fixture_setup:
                        raise ValueError('owner rotation is unavailable in verified fixture setup')
                    executor, rotation = owner_generation_protocol.rotate(
                        command, executor=executor, backend=backend,
                        executor_factory=executor_factory)
                    emit(rotation)
                elif command["op"] == "refresh_owner_source":
                    if args.verified_fixture_setup:
                        raise ValueError('owner rotation is unavailable in verified fixture setup')
                    try:
                        refreshed = owner_generation_protocol.refresh_source(
                            command, backend=backend)
                    except Exception as error:
                        emit({"event": "rejected", "id": command.get("id"),
                              "terminal_id": command.get("id"),
                              "operation": "refresh_owner_source",
                              "attempt": owner_generation_protocol._refresh_attempts,
                              "reason": str(error)})
                    else:
                        emit(refreshed)
                elif command["op"] == "save_fixture":
                    if args.fixture_out is None:
                        raise ValueError("save_fixture is unavailable in measured control")
                    close_before_control_effect(executor, args.out, emit, "save_fixture")
                    if args.verified_fixture_setup:
                        validate_setup_completed(setup_events, setup_sources, post_load_gate,
                                                 args.fixture_setup_program_sha256,
                                                 last_accepted, last_terminal, backend)
                    if args.fresh_neutral_fixture_setup:
                        validate_fresh_neutral_completed(setup_events, setup_sources,
                            args.fixture_setup_program_sha256, last_accepted, last_terminal, backend)
                    if args.fresh_neutral_fixture_setup:
                        from map01_post_load_gate_v1 import PostLoadGate
                        end_gate = PostLoadGate(args.out, args.timeout_seconds)
                        end_gate.path = args.out / 'fresh-end-clock-gate.jsonl'
                        end_gate.after_load(game, session, expected_tic=game.get_episode_time())
                        if end_gate.display != fresh_gate.display:
                            raise ValueError('fresh fixture display changed')
                    backend.snapshot("fixture-source", 0)
                    if args.fresh_neutral_fixture_setup:
                        validate_fresh_neutral_snapshot(setup_events, latest_observation)
                        checked_ns = time.perf_counter_ns()
                        if checked_ns >= end_gate.clock_reserve_deadline_ns:
                            raise ValueError('fresh fixture end clock reserve expired')
                        owner_id, generation, owner_state, engine_state = end_gate._owner_and_source(
                            backend, latest_observation,
                            {'expected_sequence': latest_observation['sequence']}, checked_ns)
                        if (owner_id != setup_sources[last_accepted['id']]['renewal_owner_id']
                                or generation != setup_sources[last_accepted['id']]['input_owner_generation']
                                or time.perf_counter_ns() >= end_gate.clock_reserve_deadline_ns):
                            raise ValueError('fresh fixture end owner or clock changed')
                        emit({'event': 'fresh_end_admission', 'checked_ns': checked_ns,
                              'owner_id': owner_id, 'generation': generation, 'owner_state': owner_state,
                              'engine_state': engine_state, 'clock_deadline_ns': end_gate.clock_reserve_deadline_ns})
                    candidate_setup = args.verified_fixture_setup or args.fresh_neutral_fixture_setup
                    save_path = (Path(os.path.abspath(args.fixture_out)) if candidate_setup
                                 else args.fixture_out.resolve())
                    if not candidate_setup:
                        save_path.parent.mkdir(parents=True, exist_ok=True)
                    engine_save_path = session.tmp / "fixture-save.png"
                    if args.fresh_neutral_fixture_setup:
                        require_fresh_neutral_deadline(latest_observation, owner_state, checked_ns,
                                                       end_gate.clock_reserve_deadline_ns,
                                                       now=time.perf_counter_ns())
                    game.save(str(engine_save_path))
                    game.advance_action(1, True)
                    wait_for_stable_file(engine_save_path)
                    if not candidate_setup:
                        shutil.copy2(engine_save_path, save_path)
                    source_frame = save_path.with_name(save_path.stem + ".source.png")
                    if not candidate_setup:
                        shutil.copy2(Path(latest_observation["image"]), source_frame)
                    fixture = {
                        "schema": CANDIDATE_FIXTURE_SCHEMA if candidate_setup else FIXTURE_SCHEMA,
                        "map": "MAP01", "skill": args.skill, "seed": args.seed,
                        "vizdoom": vd.__version__, "iwad_sha256": iwad_sha256,
                        "save_file": save_path.name,
                        "save_sha256": None if candidate_setup else file_sha256(save_path),
                        "source_frame": source_frame.name,
                        "source_frame_sha256": None if candidate_setup else file_sha256(source_frame),
                        **fixture_clock_fields(candidate_setup, game.get_episode_time()),
                        "source_observation": latest_observation,
                        "setup_input_contract": SETUP_INPUT_CONTRACT,
                        "runtime_events": str((args.out / "events.jsonl").resolve()),
                    }
                    if loaded_fixture is not None:
                        fixture["parent_fixture"] = {
                            "manifest_sha256": loaded_fixture["manifest_sha256"],
                            "save_sha256": loaded_fixture["save_sha256"],
                            "source_episode_tic": loaded_fixture["source_episode_tic"],
                            "loaded_episode_tic": loaded_fixture["after_load_tic"],
                        }
                        if 'setup_candidate_evidence' in loaded_fixture:
                            fixture["parent_fixture"]["setup_candidate_evidence"] = loaded_fixture['setup_candidate_evidence']
                            fixture["parent_fixture"]["observed_restore_tic"] = loaded_fixture['observed_restore_tic']
                            fixture["parent_fixture"]["candidate_load_check"] = loaded_fixture['candidate_load_check']
                    if candidate_setup:
                        fixture["setup_mode"] = ("fresh_neutral_fixture_setup_v1" if args.fresh_neutral_fixture_setup
                                                 else "verified_loaded_fixture_setup_v1")
                        fixture["qualification"] = "pending"
                    manifest_path = save_path.with_suffix(".json")
                    if candidate_setup:
                        write_verified_fixture(save_path, setup_directory_identity, engine_save_path,
                                               Path(latest_observation["image"]), fixture)
                    else:
                        manifest_path.write_text(json.dumps(fixture, indent=2) + "\n",
                                                 encoding="utf-8", newline="\n")
                    emit({"event": "fixture_saved", "manifest": str(manifest_path),
                          "save": str(save_path), "save_sha256": fixture["save_sha256"],
                          **{key: fixture[key] for key in ("episode_tic", "post_save_refresh_episode_tic",
                                                            "restored_episode_tic", "restored_episode_tic_status") if key in fixture},
                          "source_sequence": latest_observation["sequence"]})
                    break
                elif command["op"] == "finish":
                    if probe_delivery is not None:
                        probe_delivery.cancel()
                    close_before_control_effect(executor, args.out, emit, "finish")
                    scorer_refresh_calls = 0
                    if getattr(args, 'synthetic_exit_refresh', False):
                        if (door_coordinator is None or not door_coordinator.finished
                                or synthetic_heartbeat_count != 4 or synthetic_heartbeat_revision is None):
                            raise ValueError('synthetic synchronization prerequisites unavailable')
                        with lock:
                            refresh_source = deepcopy(latest_observation)
                        def verify_refresh_owner():
                            return synthetic_neutral_heartbeat(
                                backend, door_coordinator.gate, session, refresh_source,
                                expected_revision=synthetic_heartbeat_revision)
                        refresh_deadline = min(time.perf_counter_ns() + 1_000_000_000,
                            control_started_ns + (args.timeout_seconds - 5) * 1_000_000_000)
                        refresh_result = synchronize_terminal(
                            game, args.out, lambda: door_coordinator.gate.neutral(session),
                            verify_refresh_owner, deadline_ns=refresh_deadline)
                        scorer_refresh_calls = refresh_result['refresh_calls']
                        emit({'event': 'synthetic_terminal_refresh', **refresh_result})
                    finished_before_refresh = game.is_episode_finished()
                    if type(finished_before_refresh) is not bool:
                        raise ValueError('initial terminal state is not a boolean')
                    if finished_before_refresh is False and not (getattr(args,'door_task_exit',False) or getattr(args,'synthetic_exit_pwad',None) is not None):
                        game.advance_action(1, True)
                        scorer_refresh_calls = 1
                    finished = game.is_episode_finished()
                    dead = game.is_player_dead()
                    wall_ns = time.perf_counter_ns() - control_started_ns
                    timeout_check = getattr(game, "is_episode_timeout_reached", None)
                    timeout_reached = tic_limit_reached = None
                    if callable(timeout_check):
                        timeout_source = "engine_api"
                        status = timeout_check()
                        if type(status) is bool:
                            timeout_reached = status
                    else:
                        timeout_source = "engine_tic_limit"
                        tic = game.get_episode_time()
                        ticrate = game.get_ticrate()
                        if type(tic) is int and tic >= 0 and type(ticrate) is int and ticrate > 0:
                            tic_limit_reached = tic >= args.timeout_seconds * ticrate
                            if finished is False and not tic_limit_reached:
                                timeout_reached = False
                    map_exit = bool(finished is True and dead is False and timeout_reached is False
                                    and wall_ns < (args.timeout_seconds - 5) * 1_000_000_000)
                    raw_deaths = game.get_game_variable(vd.GameVariable.DEATHCOUNT)
                    raw_kills = game.get_game_variable(vd.GameVariable.KILLCOUNT)
                    if any(type(value) not in (int, float) or value < 0 or value % 1 != 0
                           for value in (raw_deaths, raw_kills)):
                        raise ValueError('game counter is invalid')
                    deaths = int(raw_deaths)
                    kills = int(raw_kills)
                    score = {"event": "post_control_score", "map": ("SYNTHETIC_EXIT" if getattr(args,'synthetic_exit_pwad',None) is not None else "MAP01"), "skill": args.skill,
                        "map_exit": map_exit, "episode_finished": finished,
                        "episode_timeout_reached": timeout_reached,
                        "episode_timeout_source": timeout_source,
                        "engine_tic_limit_reached": tic_limit_reached,
                        "player_dead": dead, "wall_control_ns": wall_ns,
                        "death_count": deaths, "kill_count": kills,
                        "one_life_map_exit": bool(map_exit and deaths == 0),
                        "episode_timeout_seconds": args.timeout_seconds,
                        "reward": game.get_total_reward(),
                        "scorer_refresh_calls_after_control": scorer_refresh_calls}
                    (args.out / "score.json").write_text(json.dumps(score, indent=2))
                    emit(score)
                    break
                else:
                    raise ValueError("unsupported command")
            except (ValueError, TypeError, KeyError, Expired) as error:
                if (door_coordinator is not None or args.fresh_neutral_fixture_setup
                        or command.get('op') == 'finish'
                        or (args.verified_fixture_setup and command.get('op') == 'save_fixture')):
                    raise
                emit({"event": "rejected", "id": command.get("id"),
                      "reason": str(error)})
        else:
            if door_coordinator is not None:
                emit({'event':'door_settle','status':'HOLD','operation_id':door_coordinator.pending,
                      'reason':'stdin_eof_before_finish'})
                raise RuntimeError('door trial ended before finish')
    finally:
        try:
            if probe_delivery is not None:
                probe_delivery.cancel()
        finally:
            # A close or evidence-save error must not skip later owned resources.
            # Each finally preserves failure reporting and the existing close order.
            try:
                try:
                    if executor is not None:
                        executor.close()
                finally:
                    if backend is not None:
                        try:
                            backend.close()
                        finally:
                            (args.out / "owner-events.json").write_text(
                                json.dumps(getattr(backend, "owner_records", backend.owner.records), indent=2))
            finally:
                try:
                    if game is not None:
                        game.close()
                finally:
                    if session is not None:
                        try:
                            if (session.tmp / "doom.ini").exists():
                                shutil.copy2(session.tmp / "doom.ini", args.out / "doom.ini")
                        finally:
                            session.close()
                        # Preserve the directory if config saving or close fails.
                        shutil.rmtree(session.tmp)


if __name__ == "__main__":
    main()

