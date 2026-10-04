"""Opt-in V16 lifecycle using scorer clock/status candidate V2.

Construction candidate only; not qualified for live efficacy, controller
neutrality, timing, physical release, recovery, or gameplay claims.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
V2_PATH = (HERE / "acknowledged_scorer_status_clock_v2_59_20261004" /
           "acknowledged_scorer_clock_v2.py")
_spec = importlib.util.spec_from_file_location(
    "agent_interface_acknowledged_scorer_clock_v2", V2_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load scorer clock candidate: {V2_PATH}")
_v2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v2)
AcknowledgedSamplerClockV2 = _v2.AcknowledgedSamplerClockV2

import session_map01_v16 as previous


class ObservedGameProxyClockV2(previous.ObservedGameProxy):
    """Record the inner API return before fallible return-clock qualification."""

    def advance_action(self, tics=1, update_state=True):
        sampler = self._sampler
        sampler.before_external_update(self)
        if tics != 1 or update_state is not True:
            raise ValueError("V17 requires one requested tic with state update")
        before = int(self._inner.get_episode_time())
        started = sampler.clock_ns()
        try:
            result = self._inner.advance_action(tics, update_state)
        except BaseException as error:
            sampler._failure = error
            raise
        try:
            returned = sampler.clock_ns()
        except BaseException as error:
            sampler.record_external_return_unqualified(self, before, started)
            sampler._failure = error
            raise
        try:
            after = int(self._inner.get_episode_time())
        except BaseException as error:
            sampler.record_external_return_unqualified(
                self, before, started, returned=returned)
            sampler._failure = error
            raise
        try:
            sampler.observe_external_update(self, before, after, started, returned)
        except BaseException as error:
            sampler.record_external_return_unqualified(
                self, before, started, returned=returned, after=after)
            sampler._failure = error
            raise
        return result


def _merge_sources(out):
    sources = Path(out) / "sources.json"
    if not sources.is_file():
        return False
    data = json.loads(sources.read_text(encoding="utf-8"))
    for path in (HERE / "session_map01_v17.py", V2_PATH):
        data[str(path.relative_to(RESEARCH))] = hashlib.sha256(path.read_bytes()).hexdigest()
    sources.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
    return True


def main():
    original_sampler = previous.AcknowledgedSampler
    original_proxy_type = previous.ObservedGameProxy
    previous.AcknowledgedSampler = AcknowledgedSamplerClockV2
    previous.ObservedGameProxy = ObservedGameProxyClockV2
    session_error = None
    try:
        return previous.main()
    except BaseException as error:
        session_error = error
        raise
    finally:
        previous.AcknowledgedSampler = original_sampler
        previous.ObservedGameProxy = original_proxy_type
        try:
            out = previous.previous._option("--out")
            _merge_sources(out)
        except BaseException as provenance_error:
            if session_error is not None:
                raise BaseExceptionGroup(
                    "V16 session and V17 provenance finalization failed",
                    [session_error, provenance_error]) from None
            raise


if __name__ == "__main__":
    main()
