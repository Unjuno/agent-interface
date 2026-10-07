"""Trusted task caller using the unchanged actual shared X11 owner.

No model synthesis, implicit retry, file scoring, input authority or task-success
certification. A caller must separately retain and audit model and file outcomes.
"""
from copy import deepcopy
import json
from pathlib import Path
import time
import uuid

from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from task_guard import decide_review, verify_repair_effect, _snapshot_error


class TaskSession:
    def __init__(self, ready, directory, request, *, display_name, wanted):
        self.out = Path(directory)
        self.out.mkdir(parents=True, exist_ok=False)
        self.ready = deepcopy(ready)
        self.binding = {'pid':ready['pid'], 'token':ready['token'],
                        'root_id':ready['root']['id'],
                        'target_id':ready['target']['id'],
                        'freeze_sha256':ready['freeze_sha256']}
        self.request = request
        self.wanted = wanted
        self.owner = GuardedSessionOwner({'app':ready['root']['id']}, self.out,
                                         display_name=display_name)
        self.owner.get()
        self.sequence = 0
        self.snapshots = []
        self.native_calls = []
        self._admitted = None

    def _snapshot(self, purpose):
        nonce = purpose+'-'+uuid.uuid4().hex
        reply = self.request('snapshot', nonce)
        if reply.get('status') != 'returned' or reply.get('nonce') != nonce:
            raise ValueError('Snapshot reply identity unavailable')
        snapshot = reply['snapshot']
        self.snapshots.append({'purpose':purpose, 'reply':deepcopy(reply),
                               'received_ns':time.monotonic_ns()})
        (self.out/f'snapshot-{len(self.snapshots):04d}.json').write_text(
            json.dumps(self.snapshots[-1], sort_keys=True)+'\n')
        return snapshot, nonce

    def admit(self, review, *, image_sequence, response_seen_ns):
        # Every new review boundary invalidates prior semantic proposals even
        # if transport/shape validation fails before a new proposal is returned.
        self._admitted = None
        current, nonce = self._snapshot('review')
        minimum_sequence = (max(image_sequence, self.sequence)
                            if type(image_sequence) is int else image_sequence)
        now = time.monotonic_ns()
        plan = decide_review(review, current, wanted=self.wanted,
            expected_binding=self.binding, request_nonce=nonce,
            image_sequence=minimum_sequence, response_seen_ns=response_seen_ns,
            now_ns=now)
        if _snapshot_error(current, self.binding, nonce, minimum_sequence,
                           response_seen_ns, now, 50_000_000) is None:
            self.sequence = max(self.sequence, current['sequence'])
        self._admitted = deepcopy(plan)
        (self.out/f'review-{uuid.uuid4().hex}.json').write_text(json.dumps({
            'review':review, 'image_sequence':image_sequence,
            'response_seen_ns':response_seen_ns, 'snapshot':current, 'plan':plan},
            sort_keys=True)+'\n')
        return plan

    def _keyboard(self, tail, expected_text, purpose):
        bridge = self.owner.bridge
        source = bridge.observe()
        anchor = self.ready['anchor']
        point = [anchor['x']+anchor['width']//2, anchor['y']+anchor['height']//2]
        alias = purpose+'_'+uuid.uuid4().hex[:16]
        mint = bridge.mint_reference(alias, source['sequence'], point,
                                     region_size=(40, 24))
        checks = []
        def verify(stage, native, image):
            boundary = time.monotonic_ns()
            current, nonce = self._snapshot('native-'+purpose)
            error = _snapshot_error(current, self.binding, nonce, self.sequence,
                                    boundary, time.monotonic_ns(), 50_000_000)
            if error is None and (current['target'] != expected_text or current['decoy']):
                error = 'CURRENT_TASK_DEPENDENCY_CHANGED'
            if error is None and native['pointer_binding']['surface'] != self.binding['root_id']:
                error = 'NATIVE_SURFACE_CHANGED'
            checks.append({'stage':stage, 'native_sequence':native['sequence'],
                           'snapshot':deepcopy(current), 'error':error})
            if error is None:
                self.sequence = current['sequence']
            return error is None
        with self.owner.input_guard(alias, mint['offset'], tail=tail, verify=verify):
            report = self.owner.invoke_guarded('guarded_input', {
                'interaction':'keyboard', 'alias':alias, 'offset':mint['offset'],
                'tail':tail, 'observe_after':False}, self.out/('call-'+alias))
        call = {'purpose':purpose, 'tail':deepcopy(tail), 'checks':checks,
                'report':report, 'finished_ns':time.monotonic_ns()}
        self.native_calls.append(call)
        (self.out/f'call-{len(self.native_calls):04d}.json').write_text(
            json.dumps(call, sort_keys=True)+'\n')
        return call

    @staticmethod
    def _completed(call):
        report = call['report']
        releases = report.get('result', {}).get('execution', {}).get('releases', [])
        return (report.get('status') == 'completed' and bool(releases)
                and all(r.get('verified') is True and r.get('keys_down') == []
                        and r.get('buttons_down') == [] for r in releases))

    def apply(self, plan):
        # Consume this exact caller-reviewed proposal even when input refuses.
        admitted, self._admitted = self._admitted, None
        first_call = len(self.native_calls)
        def result(status, reason):
            return {'status':status, 'reason':reason, 'task_complete':False,
                    'grants_input_authority':False,
                    'native_calls':deepcopy(self.native_calls[first_call:])}
        if admitted is None or plan != admitted:
            return result('YIELD', 'UNBOUND_OR_CONSUMED_PLAN')
        if plan['status'] == 'YIELD':
            return result('YIELD', plan['reason'])
        if plan['status'] == 'PLAN_PREFIX':
            call = self._keyboard([{'op':'key_chord', 'keys':['Home']},
                                   {'op':'text', 'text':plan['prefix']}],
                                  plan['prior_target'], 'prefix')
            if not self._completed(call):
                return result('YIELD', 'PREFIX_NATIVE_NOT_COMPLETED_AND_RELEASED')
            current, nonce = self._snapshot('repair-effect')
            now = time.monotonic_ns()
            error = _snapshot_error(current, self.binding, nonce, self.sequence,
                                    call['finished_ns'], now, 50_000_000)
            if error:
                return result('YIELD', error)
            save_plan = verify_repair_effect(plan, current, request_nonce=nonce,
                action_finished_ns=call['finished_ns'], now_ns=now)
            if save_plan['status'] != 'PLAN_SAVE':
                return result('YIELD', save_plan['reason'])
            self.sequence = max(self.sequence, current['sequence'])
        elif plan['status'] != 'PLAN_SAVE':
            return result('YIELD', 'UNSUPPORTED_PLAN')
        save = self._keyboard([{'op':'key_chord', 'keys':['CTRL', 's']}],
                              self.wanted, 'save')
        if not self._completed(save):
            return result('YIELD', 'SAVE_NATIVE_NOT_COMPLETED_AND_RELEASED')
        return result('SAVE_DISPATCHED', 'INDEPENDENT_FILE_SCORE_STILL_REQUIRED')

    def close(self):
        return self.owner.close()
