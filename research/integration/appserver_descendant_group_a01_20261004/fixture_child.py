import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--pid-file', required=True)
args = p.parse_args()
grandchild = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
tmp = Path(args.pid_file + '.tmp')
tmp.write_text(str(grandchild.pid), encoding='ascii')
os.replace(tmp, args.pid_file)
time.sleep(30)
