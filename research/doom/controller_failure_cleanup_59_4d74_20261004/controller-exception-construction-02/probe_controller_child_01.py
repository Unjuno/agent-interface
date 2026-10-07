import json
from pathlib import Path
print(json.dumps({'event':'ready','fixture':None}), flush=True)
for line in __import__('sys').stdin:
    command=json.loads(line)
    with Path('/out/child-commands.jsonl').open('a') as stream:
        stream.write(json.dumps(command)+'\n')
    if command.get('op')=='finish':
        print(json.dumps({'event':'probe_finish_ack'}), flush=True)
        break
