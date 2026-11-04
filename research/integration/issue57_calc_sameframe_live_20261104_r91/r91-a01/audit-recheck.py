import hashlib, json, sys
from pathlib import Path
from PIL import Image, ImageChops
from collections import Counter

ROOT = Path(__file__).resolve().parent
ATTEMPT = ROOT
ATTEMPT_ID = 'issue57-r91-a01'
CROP = (0, 126, 1218, 742)
READ_ERRORS = []

def read(name):
    try:
        return json.loads((ATTEMPT / name).read_text(encoding='utf-8-sig'))
    except (OSError, json.JSONDecodeError) as exc:
        READ_ERRORS.append(f'missing_or_invalid:{name}:{exc}')
        return {}
def sha(data): return hashlib.sha256(data).hexdigest()
def empty(v): return v in (None, '', [], {})
def artifact_path_from_observation(obs):
    p = obs.get('native', {}).get('artifact', {}).get('path')
    prefix = '/evidence/r91-a01/'
    if not isinstance(p, str) or not p.startswith(prefix):
        raise ValueError(f'artifact path outside attempt: {p!r}')
    return ATTEMPT / Path(*p[len(prefix):].split('/'))

def audit_surface_readiness():
    readiness = read('preinput-surface-readiness.json')
    samples = readiness.get('samples') or []
    launch = read('launch.json')
    candidate = ((launch.get('window_discovery') or {}).get('candidate') or {})
    prior_sequence = 0
    prior_generation = None
    sample_ok = []
    for index, sample in enumerate(samples, start=1):
        review = read(f'review-samples/review-{index}.json')
        if review.get('status') != 'reviewed' or review.get('input_dispatched') is not False:
            sample_ok.append(False)
            continue
        source = (review.get('review') or {}).get('source') or {}
        binding = review.get('binding') or {}
        generation = (binding.get('xid'), binding.get('process_generation'),
                      binding.get('window_generation'))
        sequence = source.get('sequence')
        native = source.get('native') or {}
        meta = native.get('artifact') or {}
        try:
            path = artifact_path_from_observation(source)
            raw = path.read_bytes()
            with Image.open(path) as image:
                rgb = image.convert('RGB')
                counts = Counter(rgb.getdata())
                unique = len(counts)
                dominant_fraction = counts.most_common(1)[0][1] / (rgb.width * rgb.height)
                dimensions = list(rgb.size)
            thresholds = sample.get('thresholds') or {}
            calculated_pass = (dimensions == [1280,800] and unique >= 1500
                               and dominant_fraction < 0.90)
            exact = (type(sequence) is int and sequence > prior_sequence
                and sample.get('source_sequence') == sequence
                and sample.get('sha256') == meta.get('sha256') == sha(raw)
                and sample.get('path') == meta.get('path')
                and sample.get('dimensions') == dimensions
                and sample.get('unique_rgb_colors') == unique
                and abs(sample.get('dominant_fraction', -1) - dominant_fraction) < 1e-12
                and thresholds == {'min_unique_rgb_colors':1500,'max_dominant_fraction':0.90}
                and sample.get('passed') is calculated_pass
                and generation[0] == candidate.get('xid')
                and type(generation[0]) is int and generation[0] > 1
                and isinstance(generation[1], str) and bool(generation[1])
                and isinstance(generation[2], str) and bool(generation[2])
                and (prior_generation is None or generation == prior_generation))
            sample_ok.append(exact)
            prior_sequence = sequence if type(sequence) is int else prior_sequence
            prior_generation = generation
        except (OSError, ValueError, IndexError, TypeError) as exc:
            READ_ERRORS.append(f'readiness_sample_{index}:{exc}')
            sample_ok.append(False)
    return (1 <= len(samples) <= 5
        and readiness.get('sample_count') == len(samples)
        and readiness.get('maximum_samples') == 5
        and readiness.get('inter_sample_wait_ms') == 250
        and readiness.get('same_window_generation_required') is True
        and readiness.get('input_dispatched_during_sampling') is False
        and readiness.get('ready') is True
        and all(sample_ok)
        and samples[-1].get('passed') is True
        and all(row.get('passed') is False for row in samples[:-1]))

def main():
    gates, errors, crops = {}, [], []
    result, compiled, prep = read('result.json'), read('compiled-result.json'), read('prepare.json')
    method = compiled.get('method_receipt') or {}
    transitions = method.get('transitions') or []
    observations = method.get('observations') or []
    events = method.get('critical_events') or []
    descriptor = compiled.get('task_artifact_admission') or {}
    request = compiled.get('task_save_request') or {}
    saves = [e for e in events if e.get('event') == 'effect_checked' and e.get('action') == 'save']
    save = saves[0] if len(saves) == 1 else {}
    gates['bounded_surface_readiness_same_generation'] = audit_surface_readiness()
    gates['two_enter_save_transitions_released'] = (
        len(transitions) == 2 and [x.get('action') for x in transitions] == ['enter','save']
        and all(x.get('release_verified') is True for x in transitions))
    gates['save_effect_callback_and_request_timing'] = (
        method.get('outcome') == 'SAFE_YIELD' and method.get('reason') == 'effect_unavailable'
        and len(saves) == 1 and save.get('status') == 'unavailable'
        and type(save.get('effect_verification_started_ns')) is int
        and type(save.get('effect_verification_accepted_ns')) is int
        and type(request.get('save_request_monotonic_ns')) is int
        and save['effect_verification_started_ns'] <= request['save_request_monotonic_ns'] <= save['effect_verification_accepted_ns'])
    root_call = prep.get('call_id')
    gates['save_request_bound_to_call_attempt_and_generations'] = (
        request.get('schema') == 'agent-interface/calc-task-save-request-v1'
        and request.get('attempt_id') == ATTEMPT_ID and request.get('call_id') == root_call
        and descriptor.get('call_id') == root_call
        and request.get('process_generation') == descriptor.get('process_generation')
        and request.get('window_generation') == descriptor.get('window_generation')
        and bool(request.get('save_request_id')))
    gates['final_observations_have_expected_calc_predicates'] = (
        len(observations) >= 3 and all(x.get('predicates',{}).get('context_ok') is True
        and x.get('predicates',{}).get('cells_filled') is True
        and x.get('predicates',{}).get('blank') is False for x in observations[-2:]))
    crop_ok = False
    crop_diagnostics = {}
    if len(observations) >= 2:
        pairs = observations[-2:]
        for row in pairs:
            refs = list((ATTEMPT / 'server-output').rglob(f"{row.get('evidence_ref')}.json"))
            if len(refs) != 1:
                errors.append(f"expected one raw observation for {row.get('evidence_ref')}, got {len(refs)}")
                continue
            obs = json.loads(refs[0].read_text(encoding='utf-8-sig'))
            path = artifact_path_from_observation(obs)
            raw = path.read_bytes()
            meta = obs['native']['artifact']
            if sha(raw) != meta.get('sha256'):
                errors.append(f"PNG hash mismatch for {row.get('evidence_ref')}")
            with Image.open(path) as im:
                rgb = im.convert('RGB')
                if rgb.size != (1280,800):
                    errors.append(f"unexpected image dimensions {rgb.size}")
                crop = rgb.crop(CROP)
                crops.append({'evidence_ref':row.get('evidence_ref'),
                    'sequence':row.get('sequence'),'full_png_sha256':sha(raw),
                    'crop_rgb_sha256':sha(crop.tobytes()),'crop_size':list(crop.size)})
        if len(crops) == 2:
            p0 = artifact_path_from_observation(json.loads(list((ATTEMPT/'server-output').rglob(f"{pairs[0].get('evidence_ref')}.json"))[0].read_text(encoding='utf-8-sig')))
            p1 = artifact_path_from_observation(json.loads(list((ATTEMPT/'server-output').rglob(f"{pairs[1].get('evidence_ref')}.json"))[0].read_text(encoding='utf-8-sig')))
            with Image.open(p0) as a, Image.open(p1) as b:
                a,b=a.convert('RGB'),b.convert('RGB')
                full_diff = sum(1 for x,y in zip(a.getdata(),b.getdata()) if x != y)
                crop_diff = sum(1 for x,y in zip(a.crop(CROP).getdata(),b.crop(CROP).getdata()) if x != y)
            crop_ok = crop_diff == 0 and crops[0]['crop_rgb_sha256'] == crops[1]['crop_rgb_sha256']
            crop_diagnostics = {'full_frame_changed_pixels':full_diff,
                'frozen_crop_changed_pixels':crop_diff}
    gates['r87_candidate_crop_identical_with_full_frames_retained'] = crop_ok
    pre = read('artifact-read-before-close.json')
    gates['preclose_fods_exact_task'] = (pre.get('status') == 'verified' and pre.get('task_success') is True and pre.get('cells') == {'A1':'731','A2':'864'})
    verified = read('verify-task.json')
    effect = verified.get('task_effect') or {}
    parsed = effect.get('parsed_effect') or {}
    controller = effect.get('save_controller') or {}
    method_hash = sha(json.dumps(method,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
    gates['parent_verifier_matches_preclose_artifact_and_request'] = (
        verified.get('status') == 'verified' and verified.get('task_success') is True
        and parsed.get('status') == 'verified' and parsed.get('task_success') is True
        and parsed.get('cells') == {'A1':'731','A2':'864'}
        and effect.get('artifact_sha256') == pre.get('artifact_sha256')
        and effect.get('save_request_id') == request.get('save_request_id')
        and controller.get('call_id') == root_call and controller.get('attempt_id') == ATTEMPT_ID
        and controller.get('process_generation') == request.get('process_generation')
        and controller.get('window_generation') == request.get('window_generation')
        and controller.get('save_request_id') == request.get('save_request_id')
        and controller.get('save_action_id') == save.get('action_id')
        and controller.get('method_receipt_sha256') == method_hash)
    close = read('close.json')
    release = close.get('release') or {}
    lifecycle = close.get('calc_target_lifecycle') or []
    life = lifecycle[0] if len(lifecycle)==1 else {}
    exit_receipt = life.get('target_process_exit_receipt') or {}
    cleanup = life.get('process_group_cleanup') or {}
    gates['close_verified_neutral_release'] = (close.get('status') == 'closed' and close.get('verified') is True and close.get('release_confirmed') is True and empty(release.get('keys_down')) and empty(release.get('buttons_down')) and close.get('owner_process_exitcode') == 0)
    gates['exact_target_launcher_clean_exit'] = (exit_receipt.get('status') == 'exited' and exit_receipt.get('verified') is True and exit_receipt.get('exit_code') == 0 and exit_receipt.get('launcher_exit_code') == 0 and cleanup.get('clean_exit_verified') is True)
    gates['no_replay_and_task_success'] = result.get('task_success') is True and result.get('release_confirmed') is True and result.get('replay_allowed') is False and result.get('action_transition_count') == 2
    prepare_path = prep.get('artifact_path')
    prefix = '/evidence/r91-a01/'
    artifact_digest = None
    if isinstance(prepare_path,str) and prepare_path.startswith(prefix):
        artifact_file = ATTEMPT / Path(*prepare_path[len(prefix):].split('/'))
        if artifact_file.is_file(): artifact_digest = sha(artifact_file.read_bytes())
    gates['raw_fods_matches_independent_parent_hash'] = artifact_digest is not None and artifact_digest == effect.get('artifact_sha256')
    docker = read('docker-exit-code.json')
    gates['live_container_exit_zero'] = docker.get('exit_code') == 0
    failed = [name for name,passed in gates.items() if not passed]
    report={'schema':'agent-interface/issue57-r91-crop-live-audit-v1','attempt_id':ATTEMPT_ID,
        'status':'PASS_SCOPED' if not failed else 'FAIL_OR_UNKNOWN','gates':gates,
        'failed_gates':failed,'details':{'method_outcome':method.get('outcome'),
        'method_reason':method.get('reason'),'task_cells':parsed.get('cells'),
        'artifact_sha256':artifact_digest,'crop':list(CROP),'crop_observations':crops,
        'crop_diagnostics':crop_diagnostics,
        'limitations':['one scripted Docker/Xvfb Calc attempt; no provider/model usage',
        'crop rectangle was selected from r87 posthoc review and tested only once prospectively',
        'no integrated efficiency, broad reliability, WSLc, MAP01 or product completion claim']},'audit_errors':READ_ERRORS + errors}
    (ATTEMPT/'audit-recheck.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,sort_keys=True,indent=2))
    return 0 if not failed else 1
if __name__ == '__main__': raise SystemExit(main())




