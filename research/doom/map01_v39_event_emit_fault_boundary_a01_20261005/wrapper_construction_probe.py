import pathlib,tempfile
from unittest import mock
orig=pathlib.Path.open
calls=[]
def wrapper(path,*args,**kwargs):
 calls.append((type(path).__name__,str(path),args[0] if args else None))
 if str(path).endswith('marker.txt'): raise OSError('expected injected failure')
 return orig(path,*args,**kwargs)
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d)/'marker.txt'
 with mock.patch.object(pathlib.Path,'open',wrapper):
  try:p.open('a')
  except OSError as e: print(type(e).__name__,str(e))
print(calls)
assert calls==[('PosixPath',str(p),'a')]
