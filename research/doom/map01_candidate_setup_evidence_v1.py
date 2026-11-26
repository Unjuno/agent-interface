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


def verify_setup_candidate(manifest_path, evidence_path, evidence_sha, engine, iwad_sha, skill, seed, timeout_seconds, iwad_path, *, _depth=0, _seen=frozenset()):
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
        require(type(_depth) is int and 0<=_depth<8 and creation not in _seen and gui not in _seen,
                'candidate evidence lineage is cyclic or too deep')
        seen=_seen | {creation,gui}
        require(creation.is_absolute() and gui.is_absolute() and creation != gui,
                'distinct absolute evidence roots required')
        seals[creation]=read_sealed_directory(creation,proof['creation_seal_sha256'])
        seals[gui]=read_sealed_directory(gui,proof['gui_seal_sha256'])
        expected_manifest=creation/'candidate/fixture.json'
        require(not manifest_path.is_symlink() and manifest_path.resolve()==expected_manifest.resolve(),
                'candidate manifest is outside sealed creation')
        candidate=read(creation,'candidate/fixture.json')
        derived=candidate.get('setup_mode')=='verified_loaded_fixture_setup_v1'
        creation_reg=read(creation,'registration.json')
        creation_out=read(creation,'worker-outcome.json')
        creation_launch=read(creation,'launcher-outcome.json')
        gui_reg=read(gui,'registration.json')
        gui_out=read(gui,'worker-outcome.json')
        gui_launch=read(gui,'launcher-outcome.json')
        headless=Path(gui_reg['headless_root'])
        require(headless.is_absolute() and headless not in (creation,gui), 'headless evidence root differs')
        require(headless not in seen, 'candidate evidence lineage reuses a sealed root')
        seen=seen | {headless}
        seals[headless]=read_sealed_directory(headless,gui_reg['headless_seal_sha256'],expected_pass=derived)
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
        validate_service_custody(headless,headless_reg,'30s',0 if derived else 2)
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
                and candidate.get('setup_mode') in ('fresh_neutral_fixture_setup_v1','verified_loaded_fixture_setup_v1')
                and candidate.get('qualification')=='pending'
                and ((derived and type(candidate.get('parent_fixture')) is dict)
                     or (not derived and 'parent_fixture' not in candidate))
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
                and creation_out.get('model_calls')==0
                and ((derived and creation_out.get('keyed_commands')==1)
                     or (not derived and creation_out.get('input_admissions_observed')==0
                         and creation_out.get('admission_observation_complete') is True))
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
                and headless_out.get('disposition')==('PASS' if derived else 'HOLD')
                and headless_out.get('expected_tic')==(expected if derived else after_save)
                and headless_out.get('actual_tic_before_any_refresh')==expected
                and headless_out.get('candidate_save_sha256')==candidate['save_sha256']
                and headless_out.get('model_calls')==0 and headless_out.get('input_commands')==0
                and headless_out.get('game_close')=='returned' and headless_launch.get('retired') is True,
                'headless reload evidence differs')
        if derived:
            headless_reg=read(headless,'registration.json')
            require(headless_reg.get('expected_tic')==expected
                    and headless_reg.get('candidate_manifest_sha256')==manifest_sha
                    and headless_reg.get('candidate_seal_sha256')==proof['creation_seal_sha256']
                    and headless_reg.get('candidate_save_sha256')==candidate['save_sha256']
                    and headless_reg.get('repeat_limit')==1
                    and headless_reg.get('input_commands')==0 and headless_reg.get('model_calls')==0,
                    'derived headless preregistration differs')
        headless_attempt=read(headless,'load-attempt.json')
        headless_return=read(headless,'load-returned.json')
        headless_times=[headless_out['init_started_ns'],headless_attempt['before_sample_started_ns'],
                        headless_attempt['recorded_ns'],headless_return['load_started_ns'],
                        headless_return['load_returned_ns'],headless_return['after_getter_ns']]
        headless_before=headless_attempt.get('before_load_tic')
        require(all(type(t) is int for t in headless_times) and all(a<=b for a,b in zip(headless_times,headless_times[1:]))
                and type(headless_before) is int and headless_before>=0
                and headless_before==headless_out.get('before_load_tic')
                and headless_attempt.get('before_sample_started_ns')==headless_out.get('before_sample_started_ns')
                and headless_attempt.get('candidate_save_sha256')==candidate['save_sha256']
                and all(headless_return.get(k)==headless_out.get(k) for k in
                        ('load_started_ns','load_returned_ns','after_getter_ns','actual_tic_before_any_refresh'))
                and headless_return.get('actual_tic_before_any_refresh')==expected
                and headless_before+((headless_times[-1]-headless_times[0])*45+999_999_999)//1_000_000_000+1<expected,
                'headless load marker or natural progress bound differs')
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
            fields=('id','step','sequence','capture_ns','frame_rgb_sha256','pointer_binding','renewal_owner_id',
                    'input_owner_generation','target_process_identity','target_renewal_window_identity')
            require(all(early.get(key)==frame.get(key) for key in fields), 'candidate typed/full observation differs')
            seq,capture=frame.get('sequence'),frame.get('capture_ns')
            binding=frame.get('pointer_binding');process=frame.get('target_process_identity')
            window=frame.get('target_renewal_window_identity')
            require(type(frame.get('step')) is int and frame['step']>=0 and type(seq) is int and seq>0 and type(capture) is int and capture>0
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
        if not derived:
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
        else:
            from doom_controller_failure_cleanup_v1 import operation_release_verified, owner_event_verified
            parent=candidate['parent_fixture']
            parent_proof=parent.get('setup_candidate_evidence')
            require(type(parent_proof) is dict and type(creation_reg.get('runtime_argv')) is list,
                    'derived candidate parent evidence missing')
            argv=creation_reg['runtime_argv']
            require(argv.count('--load-fixture-manifest')==1 and argv.index('--load-fixture-manifest')+1<len(argv),
                    'derived candidate parent manifest argument differs')
            parent_manifest=Path(argv[argv.index('--load-fixture-manifest')+1])
            parent_evidence=creation/'evidence.json'
            parent_evidence_sha=hashlib.sha256(sealed_bytes(creation,'evidence.json')).hexdigest()
            require(parent_evidence_sha==creation_reg.get('candidate_evidence_sha256')
                    and parent_evidence_sha==parent_proof.get('evidence_sha256'),
                    'derived parent proof hash differs')
            _,_,verified_parent=verify_setup_candidate(parent_manifest,parent_evidence,parent_evidence_sha,
                engine,iwad_sha,skill,seed,timeout_seconds,iwad_path,_depth=_depth+1,_seen=seen)
            require(verified_parent==parent_proof and parent.get('manifest_sha256')==verified_parent['candidate_manifest_sha256']
                    and creation_reg.get('parent_manifest_sha256')==verified_parent['candidate_manifest_sha256']
                    and creation_reg.get('parent_save_sha256')==verified_parent['candidate_save_sha256']
                    and creation_reg.get('loaded_tic')==verified_parent['expected_restore_tic']
                    and parent.get('save_sha256')==verified_parent['candidate_save_sha256']
                    and parent.get('source_episode_tic') is None
                    and parent.get('loaded_episode_tic')==verified_parent['expected_restore_tic']
                    and parent.get('observed_restore_tic')==verified_parent['expected_restore_tic'],
                    'derived parent lineage differs')
            ready=[row for row in creation_events if row.get('event')=='ready']
            check=parent.get('candidate_load_check')
            require(len(ready)==1 and type(ready[0].get('fixture')) is dict and type(check) is dict
                    and ready[0]['fixture'].get('setup_candidate_evidence')==verified_parent
                    and ready[0]['fixture'].get('candidate_load_check')==check
                    and ready[0]['fixture'].get('manifest_sha256')==parent['manifest_sha256']
                    and ready[0]['fixture'].get('save_sha256')==parent['save_sha256']
                    and ready[0]['fixture'].get('after_load_tic')==verified_parent['expected_restore_tic']
                    and ready[0].get('post_load_clock_gate',{}).get('passed') is True,
                    'derived runtime parent ready evidence differs')
            times=[check.get(k) for k in ('init_started_ns','load_started_ns','load_returned_ns','getter_finished_ns')]
            before=check.get('before_load_tic')
            require(type(before) is int and before>=0 and all(type(t) is int for t in times)
                    and all(a<=b for a,b in zip(times,times[1:]))
                    and check.get('assumed_max_tics_per_second')==45
                    and check.get('observed_restore_tic')==verified_parent['expected_restore_tic']
                    and check.get('natural_progress_upper_tic')==
                        before+((times[-1]-times[0])*45+999_999_999)//1_000_000_000+1
                    and check['natural_progress_upper_tic']<verified_parent['expected_restore_tic'],
                    'derived parent load effect is unverified')
            parent_gate=[json.loads(line) for line in sealed_bytes(creation,'runtime/post-load-clock-gate.jsonl').splitlines()]
            require(len(parent_gate)==8 and parent_gate[0].get('event')=='loaded'
                    and parent_gate[0].get('state',{}).get('tic')==verified_parent['expected_restore_tic']
                    and [(row.get('event'),row.get('series'),row.get('side')) for row in parent_gate[1:5]]==
                        [('refresh','immediate','left'),('refresh','immediate','right'),
                         ('refresh','delayed','left'),('refresh','delayed','right')]
                    and parent_gate[5].get('event')=='gate' and parent_gate[5].get('passed') is True
                    and {k:v for k,v in parent_gate[5].items() if k!='event'}==ready[0]['post_load_clock_gate']
                    and [(row.get('event'),row.get('id')) for row in parent_gate[6:]]==
                        [('submission_gate','cover-0'),('submission_gate','setup-move')],
                    'derived parent clock gate evidence missing')
            parent_states=[parent_gate[0]['state']]
            for row in parent_gate[1:5]:
                require(row.get('before')==parent_states[-1] and row.get('requested_tics')==1
                        and row.get('update_state') is True, 'derived parent gate refresh lineage differs')
                parent_states.append(row['after'])
            require(all(state.get('rate')==35 and state.get('limit')==2625
                        and state.get('x11_input_neutral') is True and state.get('last_action')==[0]*9
                        and all(state.get(key) is False for key in ('dead','finished','timeout'))
                        for state in parent_states), 'derived parent gate neutral state differs')
            parent_immediate=parent_states[2]['tic']-parent_states[1]['tic']
            parent_delayed=parent_states[4]['tic']-parent_states[3]['tic']
            parent_elapsed=parent_gate[4]['end_ns']-parent_gate[3]['end_ns']
            require(0<=parent_immediate<=5 and parent_delayed-2>=35 and parent_delayed-parent_immediate>=35
                    and parent_elapsed>0 and 25<=parent_delayed*1e9/parent_elapsed<=45
                    and parent_gate[4]['start_ns']-parent_gate[3]['end_ns']>=1_950_000_000
                    and parent_gate[5].get('immediate_delta')==parent_immediate
                    and parent_gate[5].get('delayed_delta')==parent_delayed
                    and parent_gate[5].get('delayed_elapsed_ns')==parent_elapsed,
                    'derived parent gate timing differs')
            steps=creation_reg.get('movement_steps')
            require(type(steps) is list and len(steps)==2 and type(steps[0]) is dict and type(steps[1]) is dict
                    and set(steps[0])=={'op','keys','duration_ms'} and steps[0].get('op')=='hold'
                    and type(steps[0].get('keys')) is list and len(steps[0]['keys'])==1
                    and steps[0]['keys'][0] in ('a','d','Up','Down','Left','Right')
                    and type(steps[0].get('duration_ms')) is int and 1<=steps[0]['duration_ms']<=600
                    and set(steps[1])=={'op','duration_ms','sample_ms'} and steps[1].get('op')=='coast'
                    and type(steps[1].get('duration_ms')) is int and 1<=steps[1]['duration_ms']<=5000
                    and type(steps[1].get('sample_ms')) is int and 50<=steps[1]['sample_ms']<=1000,
                    'derived candidate movement program outside setup-only bounds')
            program_sha=hashlib.sha256(json.dumps(steps,sort_keys=True,separators=(',', ':'),
                ensure_ascii=False,allow_nan=False).encode()).hexdigest()
            accepted=[row for row in creation_events if row.get('event')=='accepted']
            terminals=[row for row in creation_events if row.get('event')=='terminal']
            admissions=[row for row in creation_events if row.get('event')=='input_admission']
            transitions=[row for row in creation_events if row.get('event')=='input_release_transition']
            saved=[row for row in creation_events if row.get('event')=='fixture_saved']
            require(creation_reg.get('movement_sha256')==program_sha and creation_reg.get('maximum_key_admissions')==1
                    and creation_reg.get('repeat_limit')==1 and creation_reg.get('model_calls')==0
                    and len(commands)==3 and commands[0].get('op')=='submit' and commands[0].get('id')=='cover-0'
                    and commands[0].get('steps')==[{'op':'coast','duration_ms':200,'sample_ms':100}]
                    and commands[1].get('op')=='submit' and commands[1].get('id')=='setup-move'
                    and commands[1].get('steps')==steps and commands[2]=={'op':'save_fixture'}
                    and [row.get('id') for row in accepted]==['cover-0','setup-move']
                    and [row.get('id') for row in terminals]==['cover-0','setup-move']
                    and accepted[1].get('program_sha256')==program_sha
                    and terminals[0].get('status')=='completed' and terminals[0].get('steps_completed')==1
                    and terminals[1].get('status')=='completed' and terminals[1].get('steps_completed')==2
                    and len(admissions)==len(transitions)==len(saved)==1
                    and not any(row.get('event') in ('pointer_admission','input_released','rejected') for row in creation_events)
                    and saved[0].get('save_sha256')==candidate['save_sha256']
                    and saved[0].get('source_sequence')==candidate['source_observation']['sequence']
                    and all(saved[0].get(key)==candidate.get(key) for key in
                        ('episode_tic','post_save_refresh_episode_tic','restored_episode_tic','restored_episode_tic_status')),
                    'derived setup command or terminal evidence differs')
            admission,transition=admissions[0],transitions[0]
            up=transition.get('owner_thread_keyup_receipt')
            token=accepted[1].get('intent_token');owner=binding_identity[1];generation=binding_identity[2]
            require(type(token) is str and bool(token) and type(up) is dict
                    and admission.get('id')=='setup-move' and admission.get('step')==0
                    and admission.get('key')==steps[0]['keys'][0] and admission.get('owner_id')==owner
                    and admission.get('intent_token')==token and transition.get('id')=='setup-move'
                    and admission.get('first_press_submission_checked_before_deadline') is True
                    and type(admission.get('keycode')) is int and admission['keycode']>0
                    and admission.get('target_process_identity')==[commands[1].get('expected_sequence'),
                        binding_identity[0],binding_identity[3],accepted[1].get('valid_until_ns')]
                    and admission.get('valid_until_ns')==accepted[1].get('valid_until_ns')
                    and type(accepted[1].get('accepted_ns')) is int and type(admission.get('admitted_ns')) is int
                    and type(admission.get('input_ack_ns')) is int and type(admission.get('first_press_deadline_ns')) is int
                    and accepted[1]['accepted_ns']<=admission['admitted_ns']<=admission['input_ack_ns']<admission['first_press_deadline_ns']
                    and transition.get('key')==admission['key'] and transition.get('owner_id')==owner
                    and transition.get('intent_token')==token and transition.get('owner_transition_verified') is True
                    and up.get('owner_id')==owner and up.get('key')==admission['key']
                    and up.get('intent_token')==token and up.get('server_keyup_verified') is True
                    and up.get('keycode')==admission['keycode'] and up.get('operation')=='up'
                    and transition.get('operation')=='up'
                    and creation_events.index(accepted[0])<creation_events.index(terminals[0])<
                        creation_events.index(accepted[1])<creation_events.index(admission)<
                        creation_events.index(transition)<creation_events.index(terminals[1])<creation_events.index(saved[0])
                    and all(row.get('input_owner_id')==owner and row.get('input_owner_generation')==generation
                            for row in terminals)
                    and operation_release_verified('cover-0',creation_events)
                    and operation_release_verified('setup-move',creation_events,require_intent=True),
                    'derived setup admission or release evidence differs')
            parent_summary=parent_gate[5]
            final_tic=parent_states[-1].get('tic')
            require(type(final_tic) is int and type(parent_summary.get('validated_ns')) is int
                    and parent_gate[4]['end_ns']<=parent_summary['validated_ns']
                    and parent_summary.get('last_refresh_tic')==final_tic
                    and parent_summary.get('last_refresh_started_ns')==parent_gate[4]['start_ns']
                    and parent_summary.get('remaining_game_seconds_required')==15
                    and parent_summary.get('projection_tics_per_second')==45
                    and final_tic<2625-525,
                    'derived parent clock reserve basis differs')
            reserve_deadline=parent_gate[4]['start_ns']+(2625-final_tic-525)*1_000_000_000//45
            require(parent_summary.get('first_input_clock_deadline_ns')==reserve_deadline,
                    'derived parent clock reserve deadline differs')
            for index, gate in enumerate(parent_gate[6:]):
                state=gate.get('owner_state')
                source_sequence=gate.get('source_sequence')
                matching=[row for row in frames if row.get('sequence')==source_sequence]
                command_index=next(i for i,row in enumerate(creation_events)
                                   if row.get('event')=='command' and row.get('command')==commands[index])
                preceding=[row for row in creation_events[:command_index] if row.get('event')=='observation']
                gate_observed=gate.get('observed_ns')
                admission_deadline=gate.get('admission_deadline_ns')
                clock_deadline=gate.get('first_input_clock_deadline_ns')
                submission_tic=gate.get('observed_engine_tic')
                require(type(state) is dict and state.get('owner_id')==owner
                        and state.get('owned_buttons')==[] and state.get('owned_keycodes')==[]
                        and state.get('physical_pointer_mask')==0
                        and type(state.get('focus')) is int and len(matching)==1
                        and state['focus']==matching[0].get('pointer_binding',{}).get('focus')
                        and state.get('active_lease_deadline_ns') is None
                        and state.get('active_lease_time_valid') is False
                        and state.get('cancel_requested') is False and state.get('release_pending') is False
                        and type(state.get('sample_started_ns')) is int and type(state.get('sample_finished_ns')) is int
                        and type(gate_observed) is int and type(admission_deadline) is int and type(clock_deadline) is int
                        and type(submission_tic) is int and verified_parent['expected_restore_tic']<=submission_tic<2100
                        and parent_summary['validated_ns']<=state['sample_started_ns']<=state['sample_finished_ns']<=gate_observed
                        and len(matching)==1 and bool(preceding) and preceding[-1]==matching[0]
                        and matching[0].get('id')==('initial' if index==0 else 'cover-0')
                        and 0<=state['sample_started_ns']-matching[0]['capture_ns']<3_000_000_000
                        and source_sequence==commands[index].get('expected_sequence')
                        and gate.get('terminal_id')==(None if index==0 else 'cover-0')
                        and (index==0 or terminals[0]['terminal_ns']<=gate_observed)
                        and type(accepted[index].get('accepted_ns')) is int
                        and gate_observed<=accepted[index]['accepted_ns']<admission_deadline
                        and gate_observed<clock_deadline<=reserve_deadline
                        and clock_deadline<=state['sample_started_ns']+(2100-submission_tic)*1_000_000_000//45
                        and admission_deadline<=clock_deadline
                        and admission_deadline<=(parent_summary['validated_ns']+2_000_000_000 if index==0
                                                else state['sample_started_ns']+1_000_000_000),
                        'derived submission gate chronology or neutral owner differs')
            require(admission['first_press_deadline_ns']==parent_gate[7]['admission_deadline_ns']
                    and admission['input_ack_ns']<parent_gate[7]['first_input_clock_deadline_ns'],
                    'derived movement admission exceeds gate deadline')
            owner_events=read(creation,'runtime/owner-events.json')
            require(type(owner_events) is list and sum(row==up for row in owner_events)==1
                    and owner_event_verified(up)
                    and transition.get('admission_receipt')==dict({k:v for k,v in admission.items() if k!='emit_ns'},operation='down')
                    and transition.get('admission_receipt_valid') is True
                    and up.get('server_key_down_after_keyup') is False
                    and type(up.get('owner_keymap_sampled_ns')) is int
                    and all(row.get('owner_id')==owner and row.get('owner_generation')==generation
                            and row.get('grants_input_authority') is False for row in parent_gate[6:]),
                    'derived owner journal or submission gate binding differs')
            releases=[row for row in owner_events if row.get('event')=='owner_release']
            require(len(owner_events)==4 and len(releases)==3
                    and [row.get('event') for row in owner_events]==[
                        'owner_release','owner_explicit_keyup','owner_release','owner_release']
                    and [row.get('reason') for row in releases]==['release','release','close']
                    and [row.get('intent_token') for row in releases]==[None,token,None]
                    and all(row.get('verified') is True and row.get('key_state_source')=='x11_query_keymap'
                            and all(row.get(k)==[] for k in ('buttons_down','keys_down','keys_unknown','key_state_errors'))
                            and type(row.get('verified_ns')) is int for row in releases)
                    and all({k:v for k,v in terminals[i].get('release',{}).items()
                             if k not in ('release_call_started_ns','release_call_returned_ns')}==releases[i]
                            for i in (0,1))
                    and releases[0]['verified_ns']<=terminals[0]['terminal_ns']
                    and up['owner_keymap_sampled_ns']<=releases[1]['verified_ns']<=terminals[1]['terminal_ns']
                    and terminals[1]['terminal_ns']<=releases[2]['verified_ns'],
                    'derived owner release journal differs')
            movement=[row for row in frames if row.get('id')=='setup-move']
            move_steps=[row.get('step') for row in movement]
            require(bool(movement) and 0 in move_steps and 1 in move_steps and move_steps==sorted(move_steps)
                    and all(step in (0,1) for step in move_steps)
                    and type(admission.get('input_ack_ns')) is int and type(up.get('owner_keyrelease_started_ns')) is int
                    and type(terminals[1].get('terminal_ns')) is int
                    and all(admission['input_ack_ns']<=row['capture_ns']<terminals[1]['terminal_ns'] for row in movement)
                    and any(row['step']==0 and row['capture_ns']<up['owner_keyrelease_started_ns'] for row in movement)
                    and all(row['capture_ns']>=up['owner_keymap_sampled_ns'] for row in movement if row['step']==1),
                    'derived setup observation chronology differs')
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
