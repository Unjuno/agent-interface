"""Caller-placed, one-shot visual lanes on the existing native capture route.

Exact pixel change is only a cue, not a semantic effect. No background thread,
input, model, saved-document oracle, or additional capture backend is used.
"""
import copy
import time

import numpy as np


class NativeVisualWatch:
    def __init__(self, bridge, source_sequence, regions, *, timeout_ms=1000):
        if type(timeout_ms) is not int or not 0 <= timeout_ms <= 10000:
            raise ValueError('watch timeout must be 0..10000 ms')
        if not isinstance(regions, list) or not 1 <= len(regions) <= 8:
            raise ValueError('one to eight explicitly placed regions required')
        observation, image = bridge.history[source_sequence]
        self.source = copy.deepcopy(observation)
        self.size = image.size
        self.regions = []
        identifiers = set()
        for region in regions:
            if not isinstance(region, dict) or set(region) != {'id', 'box', 'min_changed_pixels'}:
                raise ValueError('region requires id, box, min_changed_pixels')
            identifier, box, minimum = region['id'], region['box'], region['min_changed_pixels']
            if not isinstance(identifier, str) or not identifier or len(identifier) > 64 or identifier in identifiers:
                raise ValueError('unique nonempty lane ID up to 64 characters required')
            if (not isinstance(box, list) or len(box) != 4
                    or any(type(v) is not int for v in box)):
                raise ValueError('box must be four integer screen-pixel edges')
            left, top, right, bottom = box
            if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
                raise ValueError('region must fit exact source image')
            if type(minimum) is not int or not 1 <= minimum <= (right-left)*(bottom-top):
                raise ValueError('pixel threshold must fit region area')
            identifiers.add(identifier)
            self.regions.append((copy.deepcopy(region), np.asarray(image.crop(box).convert('RGB')).copy()))
        self.timeout_ms = timeout_ms
        self.used = False
        self.registered_ns = time.monotonic_ns()

    def run(self, bridge):
        if self.used:
            raise RuntimeError('one-shot watch already consumed; do not silently rearm')
        if bridge.active is not None:
            raise RuntimeError('watch cannot run during guarded input')
        self.used = True
        started = time.monotonic_ns()
        deadline = started + self.timeout_ms * 1_000_000
        result = {'schema': 'agent-interface/native-visual-watch-v1',
                  'status': 'pending', 'authority_granted': False, 'input_dispatched': False,
                  'task_success': None, 'semantic_verified': False,
                  'sampling': 'synchronous_bounded_any_lane', 'lifetime': 'one_shot',
                  'registered_ns': self.registered_ns, 'started_ns': started,
                  'source': self.source, 'regions': [r for r, _ in self.regions],
                  'samples': [], 'events': []}
        previous = {}
        try:
            while True:
                observation = bridge.observe()
                result['observation'] = observation
                image = bridge.history[observation['sequence']][1]
                if (observation['binding_revision'] != self.source['binding_revision']
                        or observation['pointer_binding'] != self.source['pointer_binding']
                        or image.size != self.size or not bridge._focus_within_target()):
                    result.update(status='unavailable', reason='binding_or_focus_changed')
                    break
                states = []
                known = time.monotonic_ns()
                for region, baseline in self.regions:
                    current = np.asarray(image.crop(region['box']).convert('RGB'))
                    count = int(np.count_nonzero(np.any(current != baseline, axis=2)))
                    state = {'id': region['id'], 'changed_pixels': count,
                             'condition': count >= region['min_changed_pixels']}
                    states.append(state)
                    if previous.get(region['id']) != state['condition']:
                        result['events'].append(dict(state, event_index=len(result['events'])+1,
                            observation_sequence=observation['sequence'], capture_ns=observation['capture_ns'],
                            known_ns=known))
                    previous[region['id']] = state['condition']
                result['samples'].append({'observation': observation, 'known_ns': known, 'lanes': states})
                result['latest'] = states
                if any(s['condition'] for s in states):
                    result['status'] = 'changed'
                    break
                if time.monotonic_ns() >= deadline:
                    result['status'] = 'timeout'
                    break
                time.sleep(min(.05, max(0, (deadline-time.monotonic_ns())/1e9)))
        except Exception as error:
            result.update(status='unavailable', reason='capture_or_evaluation_failed', error=repr(error))
        if result['status'] == 'unavailable':
            # Never let an earlier false condition masquerade as current evidence.
            result['latest'] = [{'id': r['id'], 'condition': None} for r, _ in self.regions]
        result['ended_ns'] = time.monotonic_ns()
        return result
