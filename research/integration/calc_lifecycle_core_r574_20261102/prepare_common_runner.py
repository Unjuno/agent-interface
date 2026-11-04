"""Create a reviewed three-arm runner overlay from one exact archived source."""
import argparse
import hashlib
import json
from pathlib import Path

ORIGINAL_SHA256 = '3054fd29a11233f0a7fdcf80daaea6a59e4b286fa30ca4e506c91abb4a0d8d05'
CHANGES = (
 ("if click.get('status')!='completed' or not releases or not all(r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] for r in releases):", "if not completed_neutral(click):"),
 ("if saved.get('status')!='completed' or not rel or not all(x.get('verified') and not x.get('keys_down') and not x.get('buttons_down') for x in rel):", "if not completed_neutral(saved):"),
 ("if first.get('status')!='completed' or not all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in first.get('execution',{}).get('releases',[])):", "if not completed_neutral(first):"),
 ("if save_result.get('status')!='completed' or not all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in save_result.get('execution',{}).get('releases',[])):", "if not completed_neutral(save_result):"),
)


def rewrite(source):
    if hashlib.sha256(source).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('unexpected archived runner hash')
    text=source.decode('utf-8')
    for old,new in CHANGES:
        if text.count(old)!=1:raise ValueError('runner pattern mismatch')
        text=text.replace(old,new,1)
    return ('from release_gate import completed_neutral\n'+text).encode('utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runner',required=True)
    parser.add_argument('--destination',required=True)
    args=parser.parse_args()
    source=Path(args.runner).read_bytes();candidate=rewrite(source)
    gate=Path(__file__).with_name('release_gate.py').read_bytes()
    compile(candidate,'runner.py','exec');compile(gate,'release_gate.py','exec')
    target=Path(args.destination);target.mkdir(parents=False,exist_ok=False)
    (target/'runner.py').write_bytes(candidate);(target/'release_gate.py').write_bytes(gate)
    manifest={'source_sha256':hashlib.sha256(source).hexdigest(),
              'runner_sha256':hashlib.sha256(candidate).hexdigest(),
              'release_gate_sha256':hashlib.sha256(gate).hexdigest(),
              'live_ready':False,'note':'overlay only; no runtime, process custody or benchmark validation'}
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest))

if __name__=='__main__':main()
