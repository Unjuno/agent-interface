import collections,json,pathlib
p=pathlib.Path(__file__).resolve().parent
for file in [p/'candidate-normal/stdout.txt',p.parent/'x11-unified-custody-01a0ff2c/candidate-workflow-normal-LF/stdout.txt']:
    rows=[json.loads(line) for line in file.read_text(encoding='utf8').splitlines() if line.startswith('{')]
    print(file.name, file.parent.name, len(rows), collections.Counter(tuple(sorted(r)) for r in rows))
