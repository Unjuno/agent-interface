"""One policy worker, receiving only exact wire bytes and an opaque request ID."""
import argparse, base64, json, sys
import strict_policy, legacy_policy
p=argparse.ArgumentParser()
p.add_argument('--policy', choices=('LEGACY_JSON','STRICT_AFTER_PARSE','STRICT_RAW'), required=True)
a=p.parse_args()
for line in sys.stdin:
    q=json.loads(line)
    try:
        raw=base64.b64decode(q['wire_b64'], validate=True)
        if a.policy == 'STRICT_RAW':
            result=strict_policy.decide_json(raw)
        else:
            data=json.loads(raw)
            if a.policy == 'STRICT_AFTER_PARSE':
                result=strict_policy.decide(data['saved'],data['current'])
            else:
                result=legacy_policy.Policy('PER_FRAME_RECHECK').decide(data['saved'],data['current'])
        error=None
    except Exception as exc:
        result=None;error={'type':type(exc).__name__,'message':str(exc)}
    print(json.dumps({'id':q['id'],'policy':a.policy,'result':result,'error':error},sort_keys=True),flush=True)
