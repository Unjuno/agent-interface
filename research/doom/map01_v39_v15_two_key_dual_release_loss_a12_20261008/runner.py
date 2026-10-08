import importlib.abc,importlib.util,json,os,pathlib,sys
class _Loader(importlib.abc.Loader):
 def __init__(self,name,source):self.name=name;self.source=source
 def create_module(self,spec):return None
 def exec_module(self,module):module.__file__="frozen-source:"+self.name;exec(compile(self.source,module.__file__,"exec"),module.__dict__)
class _Finder(importlib.abc.MetaPathFinder):
 def __init__(self,sources):self.sources=sources
 def find_spec(self,name,path=None,target=None):
  if name in self.sources:return importlib.util.spec_from_loader(name,_Loader(name,self.sources[name].decode()))
  return None
def execute(candidate_bytes,source_map,out_path,virtual=False):
 sources={pathlib.PurePosixPath(p).stem:b for p,b in source_map.items()}
 sys.meta_path.insert(0,_Finder(sources));os.environ["A09_OUT"]=str(out_path);os.environ["A09_ROOT"]="/virtual/source_snapshot"
 captured={};old=pathlib.Path.write_text
 if virtual:
  def _capture(self,data,*args,**kwargs):captured["candidate.json"]=data;return len(data)
  pathlib.Path.write_text=_capture
 try:exec(compile(candidate_bytes,"candidate.py","exec"),{"__name__":"__main__","__file__":"candidate.py"})
 finally:
  if virtual:pathlib.Path.write_text=old
 return captured.get("candidate.json")
def main():
 root=pathlib.Path(__file__).resolve().parent
 manifest=json.loads((root/"source-manifest.json").read_text())
 source_map={p:(root/"source_snapshot"/p).read_bytes() for p in manifest["files"]}
 out=root/"results";out.mkdir(exist_ok=True)
 execute((root/"candidate.py").read_bytes(),source_map,out,virtual=False)
if __name__=="__main__":main()
