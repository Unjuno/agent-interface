"""Opt-in V15 composition with explicit scorer client updates.

Updates change execution timing. This version is unqualified for live efficacy,
controller neutrality and physical-release/recovery claims.
"""
import hashlib
import json
import os
from pathlib import Path
import uuid

from acknowledged_scorer_v1 import AcknowledgedSampler
import session_map01_v15 as previous


class ObservedGameProxy(previous._GameProxy):
    def __init__(self, inner, final_sample, sampler):
        super().__init__(inner, final_sample)
        self._sampler = sampler

    def advance_action(self, tics=1, update_state=True):
        self._sampler.before_external_update(self)
        if tics != 1 or update_state is not True:
            raise ValueError('V16 requires one requested tic with state update')
        before = int(self._inner.get_episode_time())
        started = self._sampler.clock_ns()
        try:
            result = self._inner.advance_action(tics, update_state)
            returned = self._sampler.clock_ns()
            after = int(self._inner.get_episode_time())
            self._sampler.observe_external_update(self, before, after, started, returned)
            return result
        except BaseException as error:
            self._sampler._failure = error
            raise


def main():
    out = Path(previous._option('--out'))
    run_id = str(uuid.uuid4())
    original = previous._coherent_progress_sample
    original_proxy = previous._GameProxy
    identity_key = 'AGENT_INTERFACE_SESSION_ID'
    prior_session_id = os.environ.get(identity_key)

    def emit(row):
        out.mkdir(parents=True, exist_ok=True)
        with (out / 'scorer-client-updates.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, sort_keys=True) + '\n')

    sampler = AcknowledgedSampler(original, run_id, emit)
    previous._coherent_progress_sample = sampler
    previous._GameProxy = lambda inner, final_sample: ObservedGameProxy(inner, final_sample, sampler)
    os.environ[identity_key] = run_id
    session_error = None
    try:
        return previous.main()
    except BaseException as error:
        session_error = error
        raise
    finally:
        previous._coherent_progress_sample = original
        previous._GameProxy = original_proxy
        if prior_session_id is None:
            os.environ.pop(identity_key, None)
        else:
            os.environ[identity_key] = prior_session_id
        try:
            sources = out / 'sources.json'
            if sources.exists():
                data = json.loads(sources.read_text(encoding='utf-8'))
                for name in ('session_map01_v12.py', 'session_identity_v1.py',
                             'session_map01_v16.py', 'acknowledged_scorer_v1.py'):
                    path = Path(__file__).parent / name
                    data['doom/' + name] = hashlib.sha256(path.read_bytes()).hexdigest()
                sources.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        except BaseException as provenance_error:
            if session_error is not None:
                raise BaseExceptionGroup(
                    "session and source provenance finalization failed",
                    [session_error, provenance_error]) from None
            raise



if __name__ == '__main__':
    main()
