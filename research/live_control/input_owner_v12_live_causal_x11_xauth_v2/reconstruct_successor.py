from pathlib import Path
import hashlib,json,shutil,subprocess,sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
PARENT=REPO/'research/live_control/input_owner_v12_live_causal_x11_v1'
EXPECTED={
 'runner.py':'4fe06071b84132c69103d0808201d40c5af821a359f74d43a7a7c9e40417e0ce',
 'audit.py':'b89236abcbeeb7a8d5c944d9e502e606d61ee83284027c5cfaaf6821b629de44',
 'fixture.py':'7739e9cfa4c4f68171cb6dfec91c647868896111619c70577d8456c6fefa5b2a'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 subprocess.run([sys.executable,str(PARENT/'reconstruct_source.py')],check=True)
 src=PARENT/'reconstructed_source';out=HERE/'reconstructed_source'
 if out.exists():shutil.rmtree(out)
 shutil.copytree(src,out)
 r=out/'runner.py';s=r.read_text()
 assert sha(r)=='5a3a9c534bc37c95d0e97b7bcb1140a53e683a20feeaaa54682cd6cf28643cc9'
 s=s.replace("b64=b''.join((src[x['name']]).read_bytes() for x in man['parts'])","b64=b''.join((src/x['name']).read_bytes() for x in man['parts'])",1)
 s=s.replace("TASK='INPUT-OWNER-V12-LIVE-CAUSAL-X11-20260918-001'","TASK='INPUT-OWNER-V12-LIVE-CAUSAL-X11-XAUTH-20260918-002'",1)
 s=s.replace('ISSUE=1099','ISSUE=1261',1)
 s=s.replace("BRANCH='research/input-owner-v12-live-causal-x11-20260918-001'","BRANCH='research/input-owner-v12-live-causal-x11-xauth-20260918-002'",1)
 r.write_text(s)
 a=out/'audit.py';s=a.read_text();assert sha(a)=='4f1e085c67049c5039a3015f53aa19d9af04f63154cc673f52c067eca4a745e6';a.write_text(s.replace("TASK='INPUT-OWNER-V12-LIVE-CAUSAL-X11-20260918-001'","TASK='INPUT-OWNER-V12-LIVE-CAUSAL-X11-XAUTH-20260918-002'",1))
 for name,want in EXPECTED.items():
  got=sha(out/name);assert got==want,(name,got,want)
 print(json.dumps({'pass':True,'files':EXPECTED},sort_keys=True))
if __name__=='__main__':main()
