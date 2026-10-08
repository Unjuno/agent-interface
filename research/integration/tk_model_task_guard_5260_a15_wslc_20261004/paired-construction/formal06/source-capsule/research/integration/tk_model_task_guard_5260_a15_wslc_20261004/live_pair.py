"""Private matched live apps using the actual unchanged shared native owner.

No model answer synthesis, independent file score or task-success certificate.
The deliberately image-only control is confined to these owned study apps.
"""
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from host_bridge import sha
from task_session import TaskSession
from task_guard import _snapshot_error

ROOT = Path(__file__).resolve().parent


def save_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write('\n')


class LiveApp:
    def __init__(self, directory, *, wanted, target, decoy, freeze_sha256, display_name):
        self.out = Path(directory)
        self.out.mkdir(parents=True, exist_ok=False)
        self.token = 'paired-'+uuid.uuid4().hex
        self.index = 0
        self.streams = [(self.out/name).open('xb') for name in ('stdout.bin','stderr.bin')]
        argv = [sys.executable, '-B', str(ROOT/'live_app.py'), str(self.out),
                self.token, freeze_sha256, wanted, target, decoy]
        save_json(self.out/'launch.json', dict(argv=argv, started_ns=time.monotonic_ns()))
        self.process = None
        try:
            self.process = subprocess.Popen(argv, stdout=self.streams[0], stderr=self.streams[1],
                env=dict(os.environ, DISPLAY=display_name))
            self.ready = self.read('ready.json')
            if self.ready['pid'] != self.process.pid or self.ready['token'] != self.token:
                raise ValueError('App ready binding mismatch')
        except BaseException:
            self.close()
            raise

    def read(self, name):
        deadline = time.monotonic()+5
        while time.monotonic() < deadline:
            try:
                return json.loads((self.out/name).read_bytes())
            except (FileNotFoundError, json.JSONDecodeError):
                if self.process.poll() is not None:
                    raise ValueError('Owned app exited before '+name)
                time.sleep(0.005)
        raise TimeoutError('Owned app publication deadline: '+name)

    def request(self, operation, nonce):
        self.index += 1
        save_json(self.out/f'request-{self.index:06d}.json',
                  dict(operation=operation, nonce=nonce, token=self.token))
        reply = self.read(f'reply-{self.index:06d}.json')
        if reply.get('status') != 'returned' or reply.get('nonce') != nonce:
            raise ValueError('Owned app request refused')
        return reply

    def close(self):
        try:
            if self.process is not None and self.process.poll() is None:
                try:
                    self.request('finish', 'finish-'+uuid.uuid4().hex)
                    self.process.wait(timeout=3)
                finally:
                    if self.process.poll() is None:
                        self.process.terminate()
                        try:
                            self.process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            self.process.kill()
                            self.process.wait(timeout=3)
        finally:
            for stream in self.streams:
                stream.close()


class LivePair:
    def __init__(self, directory, *, wanted, initial_target, initial_decoy,
                 freeze_sha256, display_name):
        self.out = Path(directory)
        self.out.mkdir(parents=True, exist_ok=False)
        self.wanted = wanted
        self.apps, self.sessions, self.images, self.initial = {}, {}, {}, {}
        self.control_consumed = False
        self.guard_results = []
        self.guard_reviews = []
        self.guard_attempts = 0
        self.stopped = False
        self.focus_recovery_consumed = False
        self.activations = []
        self.closed = False
        try:
            for arm in ('control','guard'):
                app = LiveApp(self.out/arm/'app', wanted=wanted, target=initial_target,
                    decoy=initial_decoy, freeze_sha256=freeze_sha256, display_name=display_name)
                self.apps[arm] = app
                session = TaskSession(app.ready, self.out/arm/'native', app.request,
                                      display_name=display_name, wanted=wanted)
                self.sessions[arm] = session
                snapshot = app.request('snapshot', 'initial-'+uuid.uuid4().hex)['snapshot']
                source, blob = self.capture(arm, 'initial')
                self.initial[arm] = dict(snapshot=snapshot, source=source, png_sha256=sha(blob))
                self.images[arm] = blob
            save_json(self.out/'initial-pair.json', dict(arms=self.initial,
                image_identical=self.images['control'] == self.images['guard']))
            if self.images['control'] != self.images['guard']:
                raise ValueError('METHOD_STOP_UNEQUAL_INITIAL_PIXELS')
        except BaseException:
            self.close()
            raise

    def capture(self, arm, purpose):
        bridge = self.sessions[arm].owner.bridge
        source = bridge.observe()
        image = bridge.history[source['sequence']][1]
        stream = io.BytesIO()
        image.save(stream, format='PNG')
        blob = stream.getvalue()
        with (self.out/arm/(purpose+'.png')).open('xb') as output:
            output.write(blob)
        save_json(self.out/arm/(purpose+'-capture.json'), source)
        return source, blob

    def activate(self, arm):
        session = self.sessions[arm]
        bridge = session.owner.bridge
        source = bridge.observe()
        activation = bridge.activate_window(window_id=self.apps[arm].ready['root']['id'],
            source_sequence=source['sequence'], current_binding_revision=bridge.binding_revision,
            expires_at_ns=time.monotonic_ns()+2_000_000_000, timeout_ms=500)
        review = bridge.review_window(self.apps[arm].ready['root']['id'])
        row = dict(arm=arm, activation=activation, review=review,
                   finished_ns=time.monotonic_ns())
        self.activations.append(row)
        save_json(self.out/f'activation-{len(self.activations):03d}.json', row)
        if activation.get('status') != 'completed' or review.get('status') != 'reviewed':
            raise ValueError('Owned arm activation/review failed')

    def _control_keyboard(self, tail, purpose):
        session = self.sessions['control']
        bridge = session.owner.bridge
        source = bridge.observe()
        anchor = self.apps['control'].ready['anchor']
        point = [anchor['x']+anchor['width']//2, anchor['y']+anchor['height']//2]
        alias = purpose+'_'+uuid.uuid4().hex[:16]
        mint = bridge.mint_reference(alias, source['sequence'], point, region_size=(40,24))
        # Ordinary native admission remains; only semantic task reconciliation
        # is deliberately absent from this private image-only comparison arm.
        report = session.owner.invoke_guarded('guarded_input', dict(interaction='keyboard',
            alias=alias, offset=mint['offset'], tail=tail, observe_after=False),
            self.out/'control'/('call-'+alias))
        return dict(report=report, tail=deepcopy(tail), finished_ns=time.monotonic_ns())

    def control(self, review):
        if self.control_consumed:
            raise ValueError('First image-only control already consumed')
        self.control_consumed = True
        if (type(review) is not dict or set(review) !=
            {'decision','observed_target','observed_decoy','prefix'}
            or any(type(v) is not str for v in review.values())
            or review['decision'] not in ('NO_REPAIR','INSERT_PREFIX','REFUSE')
            or (len(review['prefix']) != 1 if review['decision']=='INSERT_PREFIX' else review['prefix']!='')):
            raise ValueError('Control response schema invalid')
        calls = []
        status, reason = 'YIELD', 'MODEL_REFUSE'
        if review['decision'] != 'REFUSE':
            self.activate('control')
            if review['decision'] == 'INSERT_PREFIX':
                calls.append(self._control_keyboard([
                    dict(op='key_chord', keys=['Home']),
                    dict(op='text', text=review['prefix'])], 'prefix'))
            if not calls or TaskSession._completed(calls[-1]):
                calls.append(self._control_keyboard([dict(op='key_chord', keys=['CTRL','s'])], 'save'))
                status, reason = ('SAVE_DISPATCHED','INDEPENDENT_FILE_SCORE_STILL_REQUIRED') if (
                    TaskSession._completed(calls[-1])) else ('YIELD','CONTROL_NATIVE_INCOMPLETE')
            else:
                reason = 'CONTROL_PREFIX_NATIVE_INCOMPLETE'
        result = dict(status=status, reason=reason, review=deepcopy(review), native_calls=calls,
                      task_complete=False, grants_input_authority=False)
        save_json(self.out/'control-result.json', result)
        return result

    def guard(self, review, *, response_seen_ns, image_sequence=None):
        if self.stopped or self.guard_attempts >= 2 or (self.guard_results and self.guard_results[-1]['status']!='YIELD'):
            raise ValueError('Guard outcome terminal or one recovery consumed')
        self.guard_attempts += 1
        try:
            self.activate('guard')
            session = self.sessions['guard']
            baseline = self.initial['guard']['snapshot']['sequence'] if image_sequence is None else image_sequence
            plan = session.admit(review, image_sequence=baseline, response_seen_ns=response_seen_ns)
            result = session.apply(plan)
            save_json(self.out/f'guard-result-{self.guard_attempts:02d}.json',
                      dict(review=deepcopy(review), response_seen_ns=response_seen_ns, plan=plan, result=result))
            self.guard_results.append(deepcopy(result))
            self.guard_reviews.append(deepcopy(review))
            return result
        except BaseException:
            self.stopped = True
            raise

    def focus_recovery(self, review, *, response_seen_ns):
        if (self.stopped or self.focus_recovery_consumed or len(self.guard_results)!=1
            or review != self.guard_reviews[0]
            or self.guard_results[-1].get('reason') != 'FOCUS_NOT_TARGET'):
            raise ValueError('One focus-only recovery requires original focus YIELD')
        self.focus_recovery_consumed = True
        try:
            return self._focus_recovery(review, response_seen_ns=response_seen_ns)
        except BaseException:
            self.stopped = True
            raise

    def _focus_recovery(self, review, *, response_seen_ns):
        session = self.sessions['guard']
        boundary = time.monotonic_ns()
        current, nonce = session._snapshot('focus-only-prerequisite')
        minimum = max(session.sequence, self.initial['guard']['snapshot']['sequence'])
        checked = time.monotonic_ns()
        error = _snapshot_error(current, session.binding, nonce, minimum,
                                boundary, checked, 50_000_000)
        semantic = (review['observed_target'] == current.get('target')
            and review['observed_decoy'] == current.get('decoy') == ''
            and ((review['decision']=='NO_REPAIR' and current['target']==self.wanted)
                or (review['decision']=='INSERT_PREFIX' and current['target']
                    and review['prefix']+current['target']==self.wanted)))
        save_json(self.out/'focus-prerequisite.json', dict(snapshot=current,
            request_nonce=nonce, minimum_sequence=minimum, boundary_ns=boundary,
            checked_ns=checked, maximum_age_ns=50_000_000, snapshot_error=error,
            original_review=deepcopy(review), semantic_consistent=bool(semantic)))
        if error not in (None,'FOCUS_NOT_TARGET') or not semantic:
            denied = dict(status='YIELD', reason='MIXED_SEMANTIC_FOCUS_YIELD' if not semantic
                          else 'FOCUS_PREREQUISITE_UNQUALIFIED',
                          task_complete=False, native_calls=[])
            save_json(self.out/'focus-recovery-denied.json', dict(snapshot=current,
                snapshot_error=error, original_review=deepcopy(review), result=denied))
            return denied
        bridge = session.owner.bridge
        source = bridge.observe()
        target = self.apps['guard'].ready['target']
        # The middle of this Entry is blank. Ground the fixed left-text patch
        # rather than weakening the shared visually-flat-region refusal.
        point = [target['x']+16, target['y']+target['height']//2]
        alias = 'focus_'+uuid.uuid4().hex[:16]
        mint = bridge.mint_reference(alias, source['sequence'], point, region_size=(40,24))
        report = session.owner.invoke_guarded('guarded_input', dict(interaction='click',
            alias=alias, offset=mint['offset'], tail=[], observe_after=False),
            self.out/'guard'/('call-'+alias))
        finished = time.monotonic_ns()
        save_json(self.out/'focus-recovery.json', dict(report=report,
            original_response_seen_ns=response_seen_ns, click_finished_ns=finished))
        if not TaskSession._completed(dict(report=report)):
            return dict(status='YIELD', reason='FOCUS_RECOVERY_NATIVE_INCOMPLETE',
                        task_complete=False, native_calls=[])
        # NEW nonce-bound ACK must follow the ordinary click, not an old plan.
        return self.guard(review, response_seen_ns=max(response_seen_ns, finished))

    def close(self):
        if self.closed:
            return
        self.closed = True
        errors = []
        for arm in reversed(tuple(self.apps)):
            try:
                if arm in self.sessions:
                    self.sessions[arm].close()
            except BaseException as error:
                errors.append(dict(arm=arm, stage='session-close', error=repr(error)))
            try:
                self.apps[arm].close()
            except BaseException as error:
                errors.append(dict(arm=arm, stage='app-close', error=repr(error)))
        save_json(self.out/'close.json', dict(errors=errors, finished_ns=time.monotonic_ns()))


def await_response(client, slot, pair, timeout_seconds):
    deadline = time.monotonic()+timeout_seconds
    while time.monotonic() < deadline:
        response = client.receive(slot)
        if response is not None:
            if response['status'] != 'returned':
                raise ValueError('METHOD_STOP_FIRST_HOST_RESPONSE')
            return response
        if any(app.process.poll() is not None for app in pair.apps.values()):
            raise ValueError('METHOD_STOP_APP_EXITED_DURING_MODEL_WAIT')
        time.sleep(0.01)
    raise TimeoutError('METHOD_STOP_RESPONSE_DEADLINE_NO_RETRY')


def run_pair(pair, client, pair_id, *, prompt, focus_drift, response_timeout_seconds):
    """One actual first response shared across arms; at most one new recovery.

    Caller freezes source, exact schedule, requested model, artifacts and gates.
    This method dispatches/composes but never scores task completion itself.
    """
    first_slot, recovery_slot = pair_id+'-first', pair_id+'-recovery'
    if pair.images['control'] != pair.images['guard']:
        raise ValueError('METHOD_STOP_UNEQUAL_INITIAL_PIXELS')
    client.submit(first_slot, image=pair.images['guard'], prompt=prompt)
    first = await_response(client, first_slot, pair, response_timeout_seconds)
    answer = first['reply']['parsed']['answer']
    # Persist the ORIGINAL first response before any downstream arm operation.
    save_json(pair.out/'first-model.json', first)
    control = pair.control(answer)
    if focus_drift:
        pair.apps['guard'].request('drift', 'post-first-'+uuid.uuid4().hex)
    initial_guard = pair.guard(answer, response_seen_ns=first['response_seen_ns'])
    recovery, final_guard, focus = None, initial_guard, None
    if initial_guard['reason'] == 'MODEL_STATE_MISMATCH':
        source, blob = pair.capture('guard', 'recovery')
        snapshot, nonce = pair.sessions['guard']._snapshot('recovery-prompt')
        discrepancy = dict(first_answer=answer, current_app_snapshot=snapshot,
                           capture_source=source, recovery_nonce=nonce)
        recovery_prompt = (prompt+b'\nChanged-evidence recovery, not a retry: the first answer '
            b'was inconsistent with the later cooperative app snapshot. Preserve the requested '
            b'task and base a NEW decision on the attached later original image and literal '
            b'current state below; never assume a repair already happened.\n'+
            (json.dumps(discrepancy, sort_keys=True)+'\n').encode('utf-8'))
        client.submit(recovery_slot, image=blob, prompt=recovery_prompt)
        recovery = await_response(client, recovery_slot, pair, response_timeout_seconds)
        save_json(pair.out/'recovery-model.json', recovery)
        final_guard = pair.guard(recovery['reply']['parsed']['answer'],
            response_seen_ns=recovery['response_seen_ns'], image_sequence=snapshot['sequence'])
    else:
        if initial_guard['reason'] == 'FOCUS_NOT_TARGET':
            final_guard = pair.focus_recovery(answer, response_seen_ns=first['response_seen_ns'])
            filename = 'focus-recovery.json' if (pair.out/'focus-recovery.json').exists() else 'focus-recovery-denied.json'
            focus = json.loads((pair.out/filename).read_bytes())
        reason = (final_guard['reason'] if final_guard['reason'] in
                  ('MIXED_SEMANTIC_FOCUS_YIELD','FOCUS_PREREQUISITE_UNQUALIFIED')
                  else 'MODEL_REFUSE' if answer['decision']=='REFUSE' else 'NO_SEMANTIC_MISMATCH')
        client.skip_recovery(recovery_slot, reason=reason)
    result = dict(first=first, control=control, guard_first=initial_guard,
                  recovery=recovery, guard_final=final_guard, focus_recovery=focus,
                  provider_calls_declared=1+(recovery is not None), task_complete=False)
    # Number of actual CLI response processes; provider attestation is separate.
    result['cli_calls'] = result.pop('provider_calls_declared')
    save_json(pair.out/'paired-result.json', result)
    return result
