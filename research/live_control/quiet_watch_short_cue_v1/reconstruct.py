"""Restore archived evidence without GUI input. Standard library only."""
from __future__ import annotations
import argparse, base64, hashlib, json, lzma, pathlib
P=pathlib.Path

def sha(b):return hashlib.sha256(b).hexdigest()
def git_blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('output',type=P);a=p.parse_args()
    here=P(__file__).resolve().parent;m=json.loads((here/'manifest.json').read_text())
    a.output.mkdir(parents=True,exist_ok=False)
    count=0
    for archive in m['archives']:
        parts=[]
        for part in archive['parts']:
            b=(here/part['path']).read_bytes()
            if len(b)!=part['bytes'] or sha(b)!=part['sha256'] or git_blob(b)!=part['git_blob']:
                raise ValueError('corrupt archive part: '+part['path'])
            parts.append(b)
        data=b''.join(parts)
        if len(data)!=archive['bytes'] or sha(data)!=archive['sha256']:
            raise ValueError('archive identity mismatch')
        files=json.loads(lzma.decompress(data))
        for path,entry in files.items():
            dest=a.output/path
            if not dest.resolve().is_relative_to(a.output.resolve()):
                raise ValueError('unsafe archive path')
            if 'frame_delta_v1' in entry:
                delta=entry['frame_delta_v1'];row=delta['row'];row['frames']=[]
                for i,(shift,elapsed,j) in enumerate(delta['samples']):
                    start=delta['base']+i*10_000_000+shift;digest,red=delta['digests'][j]
                    row['frames'].append(dict(start_ns=start,end_ns=start+elapsed,digest=digest,red=red))
                raw=(json.dumps(row,indent=2)+'\n').encode()
            elif 'json' in entry:raw=(json.dumps(entry['json'],indent=2)+'\n').encode()
            elif 'text' in entry:raw=entry['text'].encode()
            else:raw=base64.b64decode(entry['base64'],validate=True)
            if sha(raw)!=entry['sha256']:raise ValueError('file identity mismatch: '+path)
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f:f.write(raw)
            count+=1
    print(json.dumps({'restored_files':count,'status':'ALL_ARCHIVE_AND_FILE_HASHES_VERIFIED'}))
if __name__=='__main__':main()
