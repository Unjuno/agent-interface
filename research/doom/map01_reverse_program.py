"""Fixed, finite OS-input suffix for a matched MAP01 reverse-door trial.

This program grants no input authority and reads no private scorer data.
The coordinator must validate identity, freshness, admission and releases
for every individual stage. These durations are a hypothesis, not a route.
"""


def reverse_stages(arm):
    if arm not in ('control', 'use', 'calibrate', 'east-return', 'east-return-turn75'):
        raise ValueError('invalid reverse arm')
    coast=lambda duration: [{'op':'coast','duration_ms':duration,'sample_ms':100}]
    hold=lambda key,duration: [{'op':'hold','keys':[key],'duration_ms':duration}]
    stages=[(f'reverse-wait-{i}',coast(1000)) for i in range(1,7)]
    turn=(600,600,475) if arm=='east-return-turn75' else (600,600,400)
    stages.extend((f'reverse-turn-{i}',hold('Left',duration))
                  for i,duration in enumerate(turn,1))
    if arm=='calibrate':
        return stages
    stages.append(('reverse-probe',hold('e',120) if arm in ('use','east-return','east-return-turn75') else coast(120)))
    stages.append(('reverse-open-wait',coast(1000)))
    stages.append(('reverse-cross',hold('Up',600)))
    if arm in ('east-return','east-return-turn75'):
        stages.extend((f'east-turn-{i}',hold('Right',duration))
                      for i,duration in enumerate((600,600,400),1))
        stages.extend((f'east-advance-{i}',hold('Up',duration))
                      for i,duration in enumerate((600,400),1))
    return stages


def reverse_manifest(arm):
    import hashlib
    import json
    program = reverse_stages(arm)
    canonical = json.dumps(program, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return {'version': 1, 'arm': arm, 'prefix_arm': 'use', 'traverse': True,
            'traverse_ms': 300, 'suffix_sha256': hashlib.sha256(canonical).hexdigest()}
