from __future__ import annotations
import argparse,base64,gzip,tarfile,io
from pathlib import Path
def main():
 ap=argparse.ArgumentParser();ap.add_argument('out');ap.add_argument('parts',nargs='+');a=ap.parse_args();joined=''.join(Path(p).read_text().strip() for p in a.parts);raw=base64.b64decode(joined,validate=True);tar_bytes=gzip.decompress(raw);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(tar_bytes),mode='r:') as tf: tf.extractall(out,filter='data')
if __name__=='__main__':main()
