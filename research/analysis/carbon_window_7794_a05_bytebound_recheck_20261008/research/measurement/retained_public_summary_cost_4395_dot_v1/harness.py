"""Small measurement helpers; never import backend or dispatch packages."""
import itertools
import json
import time

POLICIES = ('FULL_V3', 'PACED_BRIEF', 'PUBLIC_SUMMARY')

def wire_bytes(value):
    # Exact metadata preparation/json options in mcp_server.content, with
    # include_image=True. UTF-8 encoding is included in the named boundary.
    metadata = dict(value)
    metadata.pop('image', None)
    return json.dumps(metadata, allow_nan=False).encode('utf-8')

def orders():
    return list(itertools.permutations(POLICIES))

def batch(producer, value, count, *, measured):
    outputs=[]
    if measured:
        wall=time.perf_counter_ns(); cpu=time.process_time_ns()
    for _ in range(count):
        outputs.append(wire_bytes(producer(value)))
    if measured:
        cpu_end=time.process_time_ns(); wall_end=time.perf_counter_ns()
        row={'count':count,'wall_ns':wall_end-wall,'cpu_ns':cpu_end-cpu}
    else:
        row={'count':count}
    return row, outputs
