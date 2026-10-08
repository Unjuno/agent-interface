from pathlib import Path
import os,subprocess,sys,tempfile

HERE=Path(__file__).resolve().parent

def main():
    with tempfile.TemporaryDirectory(prefix='ai1261-xauth-') as td:
        auth=Path(td)/'Xauthority'
        auth.write_bytes(b'')
        os.chmod(auth,0o600)
        env=os.environ.copy();env['XAUTHORITY']=str(auth)
        p=subprocess.run([sys.executable,str(HERE/'reconstructed_source'/'runner.py'),*sys.argv[1:]],env=env)
        raise SystemExit(p.returncode)

if __name__=='__main__':main()
