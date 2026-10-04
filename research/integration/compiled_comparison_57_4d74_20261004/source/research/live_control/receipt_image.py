"""Compatibility entry point for the promoted receipt image selector."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.cli_v1.receipt_image import select_image

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);ap.add_argument('run_directory',type=Path)
    args=ap.parse_args();print(json.dumps(select_image(json.loads(args.batch.read_text()),args.run_directory)))
