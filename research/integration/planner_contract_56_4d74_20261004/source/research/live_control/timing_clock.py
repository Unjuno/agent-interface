"""Explicit Linux monotonic clock identity; no inferred cross-domain offsets."""
import hashlib,json,os,time,uuid
from pathlib import Path


def describe():
    info=time.get_clock_info('perf_counter')
    result=dict(clock='perf_counter_ns',implementation=info.implementation,monotonic=info.monotonic,
        adjustable=info.adjustable,resolution_seconds=info.resolution,authority='none')
    try:
        boot=str(uuid.UUID(Path('/proc/sys/kernel/random/boot_id').read_text().strip()))
        namespace=os.readlink('/proc/self/ns/time')
        offsets=Path('/proc/self/timens_offsets').read_text()
        if info.implementation!='clock_gettime(CLOCK_MONOTONIC)' or not info.monotonic or info.adjustable:
            raise ValueError('unsupported clock implementation')
        domain=dict(boot_id=boot,time_namespace=namespace,time_namespace_offsets=offsets,implementation=info.implementation)
        identifier=hashlib.sha256(json.dumps(domain,sort_keys=True).encode()).hexdigest()
        result.update(status='identified',domain=domain,domain_id=identifier,
            uncertainty='clock resolution recorded; scheduling/endpoint uncertainty not measured')
    except (OSError,ValueError) as exc:
        result.update(status='unavailable',domain=None,domain_id=None,reason=type(exc).__name__)
    return result


def interval(start_ns,start_clock,end_ns,end_clock):
    if type(start_ns)is not int or type(end_ns)is not int:
        return dict(status='missing_endpoint',duration_ns=None)
    if not isinstance(start_clock,dict) or not isinstance(end_clock,dict):
        return dict(status='missing_clock',duration_ns=None)
    if start_clock.get('status')!='identified' or end_clock.get('status')!='identified':
        return dict(status='missing_clock',duration_ns=None)
    if not start_clock.get('domain_id') or start_clock.get('domain_id')!=end_clock.get('domain_id') or start_clock.get('domain')!=end_clock.get('domain'):
        return dict(status='different_clock_domain',duration_ns=None)
    if end_ns<start_ns:return dict(status='ordering_error',duration_ns=None)
    return dict(status='comparable',duration_ns=end_ns-start_ns,
        scope='same identified monotonic domain; endpoint semantics must be supplied by caller')
