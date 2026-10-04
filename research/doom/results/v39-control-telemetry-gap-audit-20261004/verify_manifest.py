from pathlib import Path
import hashlib
HERE=Path(__file__).resolve().parent
EXPECTED={'README.md','audit.py','audit.json','events.jsonl','owner-events.json','sources.json'}
def main():
 lines=(HERE/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines()
 listed={}
 for line in lines:
  digest,name=line.split('  ',1)
  if name in listed: raise SystemExit('STOP_DUPLICATE_PATH:'+name)
  listed[name]=digest
 if set(listed)!=EXPECTED: raise SystemExit('STOP_FILE_SET:'+repr(sorted(set(listed)^EXPECTED)))
 for name,want in listed.items():
  got=hashlib.sha256((HERE/name).read_bytes()).hexdigest()
  if got!=want: raise SystemExit(f'STOP_PACKAGE_HASH:{name}:{got}')
 print(f'PASS_PACKAGE_MANIFEST files={len(listed)}')
if __name__=='__main__': main()
