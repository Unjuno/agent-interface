from pathlib import Path
import hashlib,json
EXPECTED={
 'ROADMAP.md':'04d3000b5529e8ccb7ae383ee0a95d18a8247ce6905e0a3819ebd792a0d321ad',
 'HTDCU.md':'4e50cb7b96dadd3ef7b79d7d4078b52d3a5280c926945f778f329fe8c9055934',
 'CONSTRUCTION_NOTE.md':'a2117aa2b346e3fde496c3c8c5db9d8a5dcd64b7e88725343c19b5f0344e1c62',
 'SOURCE_HASHES.json':'2991a73c4b4a1d657f8370fc5895829ee7f7c41910887181a1f51087c3c60041',
 'rule.py':'8bbdb6cfa1b445374be4436d3618de1eca56f4e2933f04979e67ba0cccf65bd7',
 'fixture.py':'41533f16eab74860f36eccebe06546ee2c6b732ba350b03f7c211a72b9b66582',
 'supervisor.py':'2954024d46a8d462a4b069ed9118bb045d06e1a6ed7fd83e45a27465b704ac58',
 'audit.py':'96dccd58c91413157dbe599e8f664c6c1d0c731efff7b2894813044f32dfb3d2',
}
for name,sha in EXPECTED.items():
 b=Path(name).read_bytes(); assert hashlib.sha256(b).hexdigest()==sha,name
print(json.dumps({'verified':len(EXPECTED),'source_sha256':EXPECTED},sort_keys=True))
