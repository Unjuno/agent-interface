"""Bounded data-only restoration in a trusted, quiescent checkout/parent."""
import hashlib,io,json,lzma,sys,tarfile
from pathlib import Path,PurePosixPath

def restore(manifest_file,parts_dir,dest):
 m=json.loads(manifest_file.read_text());parts=[]
 for i,row in enumerate(m['parts']):
  if row['name']!=f'{i:02d}.bin':raise ValueError('part order')
  p=parts_dir/row['name']
  if p.is_symlink() or not p.is_file():raise ValueError('part type')
  b=p.read_bytes()
  if len(b)!=row['bytes'] or hashlib.sha256(b).hexdigest()!=row['sha256']:raise ValueError('part hash')
  if hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()!=row['git_blob']:raise ValueError('git blob')
  parts.append(b)
 b=b''.join(parts)
 if len(b)!=m['bytes'] or hashlib.sha256(b).hexdigest()!=m['sha256']:raise ValueError('archive hash')
 d=lzma.LZMADecompressor(memlimit=128*1024*1024);raw=d.decompress(b,max_length=16*1024*1024+1)
 if len(raw)>16*1024*1024 or not d.eof or d.unused_data:raise ValueError('expansion')
 files={}
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as t:
  for member in t:
   name=member.name;p=PurePosixPath(name)
   if (not member.isfile() or name in files or len(files)>=512 or p.is_absolute() or '..' in p.parts or str(p)!=name or '\\' in name or name=='.'):raise ValueError('member')
   files[name]=t.extractfile(member).read()
 if len(files)!=m['files']:raise ValueError('count')
 dest.mkdir(exist_ok=False)
 for name,b in files.items():
  p=dest.joinpath(*PurePosixPath(name).parts);p.parent.mkdir(exist_ok=True,parents=True)
  with p.open('xb') as f:f.write(b)
 return m
if __name__=='__main__':
 m=restore(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]));print(json.dumps({'restored_files':m['files'],'sha256':m['sha256']},sort_keys=True))
