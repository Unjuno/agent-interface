from pathlib import Path
import subprocess,sys
HERE=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(HERE/'build_successor.py')],check=True)
print(HERE/'runner.py')
