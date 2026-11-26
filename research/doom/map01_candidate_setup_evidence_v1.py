"""Verify immutable, setup-only MAP01 candidate evidence without granting input."""
import hashlib
import io
import json
import re
from pathlib import Path


class EvidenceError(ValueError):
    pass


def digest_file(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_sealed_directory(root, expected_sha, *, expected_pass=True):
    root=Path(root)
    if type(expected_sha) is not str or re.fullmatch(r'[0-9a-f]{64}', expected_sha) is None:
        raise EvidenceError('invalid expected seal hash')
    try:
        if root.is_symlink() or not root.is_dir() or (root/'seal.json').is_symlink():
            raise EvidenceError('sealed directory or seal path differs')
        seal_bytes=(root/'seal.json').read_bytes()
        if hashlib.sha256(seal_bytes).hexdigest() != expected_sha:
            raise EvidenceError('sealed directory or seal hash differs')
        seal=json.loads(seal_bytes)
        if (type(seal) is not dict or type(expected_pass) is not bool or seal.get('passed') is not expected_pass
                or seal.get('complete_service_retirement') is not True or type(seal.get('files')) is not dict):
            raise EvidenceError('sealed run did not pass and retire')
        paths=list(root.rglob('*'))
        if any(path.is_symlink() for path in paths):
            raise EvidenceError('sealed directory contains symlinks')
        actual={path.relative_to(root).as_posix() for path in paths if path.is_file()}
        if actual != set(seal['files']) | {'seal.json'}:
            raise EvidenceError('sealed file inventory differs')
        for name, entry in seal['files'].items():
            if (type(name) is not str or type(entry) is not dict or type(entry.get('bytes')) is not int
                    or entry['bytes'] < 0 or type(entry.get('sha256')) is not str
                    or re.fullmatch(r'[0-9a-f]{64}', entry['sha256']) is None):
                raise EvidenceError('invalid sealed file entry')
            path=root/name
            if path.stat().st_size != entry['bytes'] or digest_file(path) != entry['sha256']:
                raise EvidenceError('sealed file differs')
        return seal
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise EvidenceError('sealed evidence unavailable or malformed') from error


def verify_setup_candidate(manifest_path, evidence_path, evidence_sha, engine, iwad_sha, skill, seed, timeout_seconds, iwad_path):
    """Validate two sealed trials and return a setup-only load binding.

    The caller supplies the pre-registered evidence hash; this grants no task or
    input authority and leaves the original pending candidate unchanged.
    """
    manifest_path, evidence_path = Path(manifest_path), Path(evidence_path)
    def require(condition, message):
        if not condition:
            raise EvidenceError(message)
    seals={}
    def sealed_bytes(root, name):
        entry=seals[root]['files'][name]
        path=root/name
        require(not path.is_symlink(), 'sealed evidence path is a symlink')
        data=path.read_bytes()
        require(len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256'],
                'sealed evidence changed during verification')
        return data
    def read(root, name):
        return json.loads(sealed_bytes(root,name))
    try:
        require(type(evidence_sha) is str and re.fullmatch(r'[0-9a-f]{64}',evidence_sha) is not None
                and not evidence_path.is_symlink(), 'setup evidence hash differs')
        evidence_bytes=evidence_path.read_bytes()
        require(hashlib.sha256(evidence_bytes).hexdigest()==evidence_sha, 'setup evidence hash differs')
        proof=json.loads(evidence_bytes)
        require(type(timeout_seconds) is int and timeout_seconds==75, 'candidate setup requires 75-second timeout')
        require(type(proof) is dict and proof.get('schema')=='map01_setup_candidate_evidence_v1',
                'unsupported setup evidence')
        creation,gui=Path(proof['creation_root']),Path(proof['gui_root'])
        require(creation.is_absolute() and gui.is_absolute() and creation != gui,
                'distinct absolute evidence roots required')
        seals[creation]=read_sealed_directory(creation,proof['creation_seal_sha256'])
        seals[gui]=read_sealed_directory(gui,proof['gui_seal_sha256'])
        expected_manifest=creation/'candidate/fixture.json'
        require(not manifest_path.is_symlink() and manifest_path.resolve()==expected_manifest.resolve(),
                'candidate manifest is outside sealed creation')
        candidate=read(creation,'candidate/fixture.json')
        creation_reg=read(creation,'registration.json')
        creation_out=read(creation,'worker-outcome.json')
        creation_launch=read(creation,'launcher-outcome.json')
        gui_reg=read(gui,'registration.json')
        gui_out=read(gui,'worker-outcome.json')
        gui_launch=read(gui,'launcher-outcome.json')
        headless=Path(gui_reg['headless_root'])
        require(headless.is_absolute() and headless not in (creation,gui), 'headless evidence root differs')
        seals[headless]=read_sealed_directory(headless,gui_reg['headless_seal_sha256'],expected_pass=False)
        headless_out=read(headless,'worker-outcome.json')
        headless_launch=read(headless,'launcher-outcome.json')
        headless_reg=read(headless,'registration.json')
        def validate_service_custody(root, registration, runtime, exit_code):
            claim=read(root,'claim.json'); launch=read(root,'launch.json')
            active_service=read(root,'service-active.json'); outer=read(root,'launcher-outcome.json')
            unit=registration.get('unit'); registration_sha=hashlib.sha256(sealed_bytes(root,'registration.json')).hexdigest()
            require(type(unit) is str and unit.endswith('.service') and '/' not in unit
                    and registration.get('root')==str(root) and claim.get('unit')==unit
                    and claim.get('registration_sha256')==registration_sha
                    and registration.get('driver_sha256')==hashlib.sha256(sealed_bytes(root,'driver.py')).hexdigest()
                    and registration.get('launcher_sha256')==hashlib.sha256(sealed_bytes(root,'launcher.py')).hexdigest(),
                    'service registration identity differs')
            options=['UMask=0077','PrivateTmp=yes','PrivateNetwork=yes',
                     'RuntimeMaxSec='+('60s' if runtime=='1min' else '30s'),
                     'TimeoutStopSec=5s','KillMode=control-group']
            expected_argv=['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit]
            for option in options:expected_argv.extend(('-p',option))
            expected_argv.extend((registration['python'],'-B',str(root/'driver.py'),registration_sha))
            props=active_service['properties']; main=int(props['MainPID']); group=props['ControlGroup']
            require(registration.get('unit_options')==options and launch.get('argv')==expected_argv
                    and type(group) is str and group.endswith('/'+unit) and main>1
                    and active_service.get('initial_pids')==[main]
                    and all(props.get(key)==value for key,value in
                        {'Id':unit,'PrivateTmp':'yes','PrivateNetwork':'yes','KillMode':'control-group',
                         'RuntimeMaxUSec':runtime,'TimeoutStopUSec':'5s','UMask':'0077'}.items())
                    and type(props.get('InvocationID')) is str and bool(props['InvocationID'])
                    and outer.get('unit')==unit and outer.get('control_group')==group
                    and outer.get('retired') is True and outer.get('timed_out') is False
                    and outer.get('exit_code')==exit_code, 'service isolation or retirement differs')
            for snapshot in (claim.get('before'),outer.get('service_after')):
                require(type(snapshot) is dict and snapshot.get('exit_code')==0
                        and type(snapshot.get('stdout')) is str, 'service state unavailable')
                state=dict(line.split('=',1) for line in snapshot['stdout'].splitlines() if '=' in line)
                require(all(state.get(key)==value for key,value in
                    {'Id':unit,'LoadState':'not-found','ActiveState':'inactive','MainPID':'0','ControlGroup':''}.items()),
                    'service not proven absent')
        validate_service_custody(creation,creation_reg,'1min',0)
        validate_service_custody(gui,gui_reg,'30s',0)
        validate_service_custody(headless,headless_reg,'30s',2)
        observed=read(gui,'gui-observation.json')
        raw_capture=read(gui,'capture-raw.json')
        active=read(gui,'display-active.json')
        retired=read(gui,'display-retired.json')
        service=read(gui,'service-active.json')
        attempt=read(gui,'load-attempt.json')
        returned=read(gui,'load-returned.json')
        manifest_sha=hashlib.sha256(sealed_bytes(creation,'candidate/fixture.json')).hexdigest()
        save=creation/'candidate'/candidate['save_file']
        source=creation/'candidate'/candidate['source_frame']
        require(candidate.get('schema')=='map01_os_input_fixture_candidate_v1'
                and candidate.get('setup_mode')=='fresh_neutral_fixture_setup_v1'
                and candidate.get('qualification')=='pending' and 'parent_fixture' not in candidate
                and candidate.get('setup_input_contract')==('fixture state reached through the same X11 Executor and '
                     'recorded OS-input/coast programs; save is setup-only')
                and type(candidate.get('source_observation')) is dict
                and candidate['source_observation'].get('event')=='observation'
                and candidate['source_observation'].get('id')=='fixture-source'
                and candidate['source_observation'].get('exact') is True
                and type(candidate['source_observation'].get('sequence')) is int
                and candidate['source_observation']['sequence']>0
                and candidate.get('map')=='MAP01' and type(candidate.get('skill')) is int
                and candidate['skill']==skill and type(candidate.get('seed')) is int and candidate['seed']==seed
                and candidate.get('vizdoom')==engine and candidate.get('iwad_sha256')==iwad_sha
                and digest_file(iwad_path)==iwad_sha and candidate.get('save_file')=='fixture.png'
                and candidate.get('source_frame')=='fixture.source.png'
                and digest_file(save)==candidate.get('save_sha256')
                and digest_file(source)==candidate.get('source_frame_sha256'),
                'sealed candidate fields or bytes differ')
        expected=proof.get('expected_restore_tic')
        after_save=(candidate.get('post_save_refresh_episode_tic')
                    if candidate.get('post_save_refresh_episode_tic') is not None else candidate.get('episode_tic'))
        require(type(expected) is int and expected>=0 and type(after_save) is int and after_save>=0
                and creation_reg.get('candidate_manifest')==str(manifest_path)
                and creation_out.get('candidate_manifest_sha256')==manifest_sha
                and creation_out.get('passed') is True and creation_out.get('candidate_status')=='unqualified'
                and creation_out.get('model_calls')==0 and creation_out.get('input_admissions_observed')==0
                and creation_out.get('admission_observation_complete') is True
                and creation_out.get('owner_close_verified') is True and creation_out.get('display_retired') is True
                and creation_launch.get('retired') is True and creation_launch.get('exit_code')==0,
                'candidate creation evidence incomplete')
        require(gui_reg.get('candidate_root')==str(creation)
                and gui_reg.get('candidate_seal_sha256')==proof['creation_seal_sha256']
                and gui_reg.get('candidate_manifest_sha256')==manifest_sha
                and gui_reg.get('candidate_save_sha256')==candidate['save_sha256']
                and gui_reg.get('source_post_save_tic')==after_save and gui_reg.get('expected_tic')==expected
                and gui_reg.get('input_commands')==0 and gui_reg.get('model_calls')==0
                and gui_out.get('expected_tic')==expected and gui_out.get('source_post_save_tic')==after_save
                and gui_out.get('actual_tic_before_any_refresh')==expected
                and gui_out.get('candidate_save_sha256')==candidate['save_sha256']
                and gui_out.get('passed') is True and gui_out.get('disposition')=='PASS'
                and gui_out.get('comparison')=='PASS' and gui_out.get('model_calls')==0
                and gui_out.get('input_commands')==0 and gui_out.get('game_close')=='returned'
                and gui_out.get('session_close')=='returned' and gui_launch.get('retired') is True
                and gui_launch.get('exit_code')==0 and attempt.get('candidate_save_sha256')==candidate['save_sha256']
                and returned.get('actual_tic_before_any_refresh')==expected,
                'GUI reload evidence does not bind the candidate')
        require(digest_file(headless/'worker-outcome.json')==gui_reg['headless_outcome_sha256']
                and headless_out.get('disposition')=='HOLD' and headless_out.get('expected_tic')==after_save
                and headless_out.get('actual_tic_before_any_refresh')==expected
                and headless_out.get('candidate_save_sha256')==candidate['save_sha256']
                and headless_out.get('model_calls')==0 and headless_out.get('input_commands')==0
                and headless_out.get('game_close')=='returned' and headless_launch.get('retired') is True,
                'headless reload evidence differs')
        require(all(hashlib.sha256(sealed_bytes(root,'isolated-save.png')).hexdigest()==candidate['save_sha256']
                    for root in (headless,gui)), 'diagnostic loaded save bytes differ')
        creation_events=[json.loads(line) for line in sealed_bytes(creation,'runtime/events.jsonl').splitlines()]
        commands=[row['command'] for row in creation_events if row.get('event')=='command']
        typed=[row for row in creation_events if row.get('event')=='typed_observation']
        frames=[row for row in creation_events if row.get('event')=='observation']
        require(len(typed)>=2 and len(typed)==len(frames) and frames[0].get('id')=='initial'
                and frames[-1].get('id')=='fixture-source', 'candidate observation coverage incomplete')
        prior_seq=prior_time=None
        binding_identity=None
        for early, frame in zip(typed,frames):
            fields=('id','sequence','capture_ns','frame_rgb_sha256','pointer_binding','renewal_owner_id',
                    'input_owner_generation','target_process_identity','target_renewal_window_identity')
            require(all(early.get(key)==frame.get(key) for key in fields), 'candidate typed/full observation differs')
            seq,capture=frame.get('sequence'),frame.get('capture_ns')
            binding=frame.get('pointer_binding');process=frame.get('target_process_identity')
            window=frame.get('target_renewal_window_identity')
            require(type(seq) is int and seq>0 and type(capture) is int and capture>0
                    and type(binding) is dict and type(binding.get('surface')) is int
                    and binding.get('focus')==binding['surface'] and type(process) is dict and type(window) is dict
                    and process.get('sequence')==seq and window.get('sequence')==seq
                    and process.get('surface')==binding['surface'] and window.get('surface')==binding['surface']
                    and type(process.get('digest')) is str and re.fullmatch(r'[0-9a-f]{64}',process['digest']) is not None
                    and type(window.get('digest')) is str and re.fullmatch(r'[0-9a-f]{64}',window['digest']) is not None
                    and type(frame.get('renewal_owner_id')) is str and bool(frame['renewal_owner_id'])
                    and type(frame.get('input_owner_generation')) is int and frame.get('exact') is True
                    and frame.get('focus_samples_match') is True and frame.get('input_focus_before')==binding['focus']
                    and frame.get('input_focus_after')==binding['focus'], 'candidate observation binding differs')
            if prior_seq is not None:
                require(seq==prior_seq+1 and 0<capture-prior_time<=3_000_000_000,
                        'candidate observation sequence or coverage differs')
            current=(binding['surface'],frame['renewal_owner_id'],frame['input_owner_generation'],
                     process['digest'],window['digest'])
            if binding_identity is None:binding_identity=current
            require(current==binding_identity,'candidate target or owner changed')
            for name,value in (('health',100),('ammo',50)):
                signal=early.get('signals',{}).get(name,{})
                require(signal.get('status')=='observed' and signal.get('value')==value
                        and signal.get('signal_id')==name and signal.get('sequence')==seq
                        and signal.get('capture_ns')==capture and signal.get('binding')==binding,
                        'candidate HUD observation differs')
            prior_seq,prior_time=seq,capture
        source_observation=candidate['source_observation']
        source_rows=[row for row in creation_events if row.get('event')=='observation'
                     and row.get('sequence')==source_observation['sequence'] and row.get('id')=='fixture-source']
        source_typed=[row for row in typed if row.get('sequence')==source_observation['sequence']]
        require(len(source_rows)==1 and {k:v for k,v in source_rows[0].items() if k!='emit_ns'}==source_observation
                and len(source_typed)==1 and source_typed[0].get('frame_rgb_sha256')==source_observation.get('frame_rgb_sha256'),
                'candidate source observation is not bound to typed evidence')
        from PIL import Image
        with Image.open(io.BytesIO(sealed_bytes(creation,'candidate/fixture.source.png'))) as source_image:
            require(hashlib.sha256(source_image.convert('RGB').tobytes()).hexdigest()==source_observation.get('frame_rgb_sha256'),
                    'candidate source RGB differs')
        fixed_steps=[{'op':'coast','duration_ms':5000,'sample_ms':250},
                     {'op':'coast','duration_ms':4768,'sample_ms':250}]
        program_sha=hashlib.sha256(json.dumps(fixed_steps,sort_keys=True,separators=(',', ':'),
                                              ensure_ascii=False,allow_nan=False).encode()).hexdigest()
        accepted=[row for row in creation_events if row.get('event')=='accepted']
        terminals=[row for row in creation_events if row.get('event')=='terminal']
        saved=[row for row in creation_events if row.get('event')=='fixture_saved']
        clock_keys=('episode_tic','post_save_refresh_episode_tic','restored_episode_tic',
                    'restored_episode_tic_status')
        require(creation_reg.get('steps')==fixed_steps and creation_reg.get('program_sha256')==program_sha
                and len(accepted)==1 and accepted[0].get('id')=='fresh-coast'
                and accepted[0].get('program_sha256')==program_sha and len(terminals)==1
                and terminals[0].get('id')=='fresh-coast' and terminals[0].get('status')=='completed'
                and terminals[0].get('steps_completed')==len(fixed_steps)
                and len(saved)==1 and saved[0].get('save_sha256')==candidate['save_sha256']
                and saved[0].get('source_sequence')==candidate['source_observation']['sequence']
                and all(saved[0].get(key)==candidate.get(key) for key in clock_keys)
                and len(commands)==2 and commands[0].get('op')=='submit'
                and commands[0].get('id')=='fresh-coast' and commands[0].get('steps')==creation_reg.get('steps')
                and commands[1]=={'op':'save_fixture'}
                and not any(row.get('event') in ('input_admission','pointer_admission',
                            'input_release_transition','input_released') for row in creation_events)
                and bool(typed) and all(row.get('signals',{}).get('health',{}).get('status')=='observed'
                    and row['signals']['health'].get('value')==100
                    and row.get('signals',{}).get('ammo',{}).get('status')=='observed'
                    and row['signals']['ammo'].get('value')==50 for row in typed),
                'candidate setup command or HUD evidence differs')
        from doom_controller_failure_cleanup_v1 import operation_release_verified
        require(operation_release_verified('fresh-coast',creation_events), 'candidate coast release unverified')
        gate_rows=[json.loads(line) for line in sealed_bytes(gui,'gui-load-clock-gate.jsonl').splitlines()]
        require(len(gate_rows)==6 and gate_rows[0].get('event')=='loaded'
                and gate_rows[0].get('state',{}).get('tic')==expected
                and [(row.get('event'),row.get('series'),row.get('side')) for row in gate_rows[1:5]]==
                    [('refresh','immediate','left'),('refresh','immediate','right'),
                     ('refresh','delayed','left'),('refresh','delayed','right')]
                and gate_rows[-1].get('event')=='gate', 'GUI gate event sequence differs')
        states=[gate_rows[0]['state']]
        for row in gate_rows[1:5]:
            require(row.get('before')==states[-1] and row.get('requested_tics')==1
                    and row.get('update_state') is True, 'GUI gate refresh lineage differs')
            states.append(row['after'])
        require(all(state.get('rate')==35 and state.get('limit')==2625
                    and state.get('x11_input_neutral') is True and state.get('last_action')==[0]*9
                    and all(state.get(key) is False for key in ('dead','finished','timeout'))
                    for state in states), 'GUI gate input or clock state differs')
        immediate=states[2]['tic']-states[1]['tic']; delayed=states[4]['tic']-states[3]['tic']
        elapsed=gate_rows[4]['end_ns']-gate_rows[3]['end_ns']
        require(0<=immediate<=5 and delayed-2>=35 and delayed-immediate>=35 and elapsed>0
                and 25<=delayed*1e9/elapsed<=45
                and gate_rows[4]['start_ns']-gate_rows[3]['end_ns']>=1_950_000_000
                and gate_rows[-1].get('immediate_delta')==immediate
                and gate_rows[-1].get('delayed_delta')==delayed
                and gate_rows[-1].get('delayed_elapsed_ns')==elapsed
                and gui_out.get('clock_gate')=={k:v for k,v in gate_rows[-1].items() if k!='event'},
                'GUI gate timing evidence differs')
        gate=gui_out.get('clock_gate',{})
        require(gate.get('passed') is True and type(gate.get('validated_ns')) is int
                and type(gate.get('delayed_delta')) is int and type(gate.get('delayed_elapsed_ns')) is int
                and gate['delayed_elapsed_ns']>0 and 25<=gate['delayed_delta']*1e9/gate['delayed_elapsed_ns']<=45
                and type(observed.get('capture_ns')) is int and observed['capture_ns']>=gate['validated_ns']
                and observed.get('physical_input_neutral') is True and observed.get('before')==observed.get('after')
                and observed.get('before')==active.get('load_window')
                and observed.get('image_sha256')==seals[gui]['files']['loaded.png']['sha256'],
                'GUI clock, window, or observation evidence differs')
        target=observed['before']
        identity=target.get('identity',{})
        worker_pid=int(service['properties']['MainPID'])
        pids=active.get('pids')
        pidfds=retired.get('pidfds_signaled')
        require(type(pids) is list and len(pids)==4 and len(set(pids))==4 and worker_pid in pids
                and type(pidfds) is dict and set(pidfds)=={str(pid) for pid in pids if pid!=worker_pid}
                and all(value is True for value in pidfds.values())
                and active.get('xvfb_pid') in pids and active.get('openbox_pid') in pids
                and target.get('pid') in pids and len({active.get('xvfb_pid'),active.get('openbox_pid'),
                                                       target.get('pid'),worker_pid})==4
                and identity.get('pid')==target.get('pid') and identity.get('xid')==target.get('surface')
                and target.get('focus')==target.get('surface') and type(identity.get('start_ticks')) is int
                and identity['start_ticks']>0 and raw_capture.get('before')==target
                and raw_capture.get('image_sha256')==observed.get('image_sha256')
                and raw_capture.get('frame_rgb_sha256')==observed.get('frame_rgb_sha256')
                and raw_capture.get('capture_started_ns')==observed.get('capture_started_ns')
                and raw_capture.get('capture_ns')==observed.get('capture_ns')
                and active.get('keymap_neutral') is True
                and retired.get('lock_absent') is True and retired.get('xauthority_absent') is True
                and retired.get('cgroup_pids')==[worker_pid], 'GUI process retirement evidence incomplete')
        for field, scheme, keys in (
            ('process_generation','xres-linux-process-v1',('xid','pid','start_ticks')),
            ('process_incarnation','xres-linux-process-incarnation-v1',('pid','start_ticks'))):
            payload={'scheme':scheme,**{key:identity[key] for key in keys}}
            require(hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest()
                    ==identity.get(field), 'GUI process identity digest differs')
        gate_times=[gate_rows[0]['observed_ns']]
        for row in gate_rows[1:5]:
            gate_times.extend((row['start_ns'],row['end_ns']))
        chronology=[gui_out['init_started_ns'],gui_out['before_sample_started_ns'],active['observed_ns'],
                    attempt['recorded_ns'],returned['load_started_ns'],returned['load_returned_ns'],
                    returned['after_getter_ns'],*gate_times,gate['validated_ns'],observed['capture_started_ns'],
                    observed['capture_ns']]
        require(all(type(value) is int for value in chronology)
                and all(a<=b for a,b in zip(chronology,chronology[1:]))
                and all(gui_out.get(key)==returned.get(key) for key in
                        ('load_started_ns','load_returned_ns','after_getter_ns','actual_tic_before_any_refresh'))
                and attempt.get('before_load_tic')==gui_out.get('before_load_tic')
                and type(gui_out['before_load_tic']) is int
                and gui_out['before_load_tic'] +
                    ((returned['after_getter_ns']-gui_out['init_started_ns'])*45+999_999_999)//1_000_000_000+1
                    < expected, 'GUI load chronology or natural progress bound differs')
        from PIL import Image
        from doom_hud_signal_v3 import DoomStatusNumberReader
        before=observed['before']
        binding={key:before[key] for key in ('focus','surface','geometry')}
        with Image.open(io.BytesIO(sealed_bytes(gui,'loaded.png'))) as image:
            frame=image.convert('RGB')
            require(hashlib.sha256(frame.tobytes()).hexdigest()==observed.get('frame_rgb_sha256'),
                    'GUI RGB differs')
            for name,value in (('health',100),('ammo',50)):
                decoded=DoomStatusNumberReader(iwad_path,signal_id=name).read_frame(
                    {'sequence':1,'capture_ns':observed['capture_ns'],'pointer_binding':binding},frame)
                stored=observed['signals'][name]
                require(decoded.get('status')=='observed' and decoded.get('value')==value
                        and stored.get('status')=='observed' and stored.get('value')==value
                        and decoded.get('wad_sha256')==iwad_sha,
                        'GUI HUD does not match fixed WAD')
        return candidate,save,{'evidence_sha256':evidence_sha,'candidate_manifest_sha256':manifest_sha,
                'candidate_save_sha256':candidate['save_sha256'], 'source_post_save_tic':after_save,
                'expected_restore_tic':expected,'creation_seal_sha256':proof['creation_seal_sha256'],
                'gui_seal_sha256':proof['gui_seal_sha256']}
    except EvidenceError:
        raise
    except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError) as error:
        raise EvidenceError('setup candidate evidence unavailable or malformed') from error
