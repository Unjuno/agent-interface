from __future__ import annotations
import json, sys, time, platform, os

def meta():
    return {
        'pid': os.getpid(),
        'python': sys.version,
        'platform': platform.platform(),
        'perf': vars(time.get_clock_info('perf_counter')),
        'mono': vars(time.get_clock_info('monotonic')),
        'clock_monotonic_available': hasattr(time, 'CLOCK_MONOTONIC'),
    }

print(json.dumps({'type':'meta','meta':meta()}, sort_keys=True), flush=True)
for line in sys.stdin:
    req=json.loads(line)
    seq=req['seq']; nonce=req['nonce']
    c_perf_recv=time.perf_counter_ns()
    c_mono_recv=time.monotonic_ns()
    c_clock_recv=time.clock_gettime_ns(time.CLOCK_MONOTONIC)
    c_perf_send=time.perf_counter_ns()
    c_mono_send=time.monotonic_ns()
    c_clock_send=time.clock_gettime_ns(time.CLOCK_MONOTONIC)
    resp={
        'type':'pong','seq':seq,'nonce':nonce,
        'c_perf_recv':c_perf_recv,'c_mono_recv':c_mono_recv,'c_clock_recv':c_clock_recv,
        'c_perf_send':c_perf_send,'c_mono_send':c_mono_send,'c_clock_send':c_clock_send,
    }
    print(json.dumps(resp, separators=(',',':'), sort_keys=True), flush=True)
