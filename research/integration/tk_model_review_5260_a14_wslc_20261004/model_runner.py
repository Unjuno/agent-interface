"""Four bounded host CLI calls; first transport/method STOP consumes allocation."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from model_contract import parse
ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run_command(argv,prompt,output,timeout):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    attempt=dict(argv=argv,prompt_sha256=hashlib.sha256(prompt).hexdigest(),started_utc=datetime.now(timezone.utc).isoformat())
    (output/'attempt.json').write_text(json.dumps(attempt,sort_keys=True)+'\n',encoding='utf-8')
    began=time.perf_counter();timed_out=False;error=None
    try:
        process=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:stdout,stderr=process.communicate(prompt,timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True;process.kill();stdout,stderr=process.communicate()
        exit_code=process.returncode
    except OSError as exc:
        stdout=stderr=b'';exit_code=None;error=type(exc).__name__+':'+str(exc)
    (output/'stdout.bin').write_bytes(stdout);(output/'stderr.bin').write_bytes(stderr)
    receipt=dict(**attempt,finished_utc=datetime.now(timezone.utc).isoformat(),wall_seconds=time.perf_counter()-began,exit_code=exit_code,timed_out=timed_out,launch_error=error,output_sha256={n:sha(output/n) for n in ('attempt.json','stdout.bin','stderr.bin')})
    (output/'receipt.json').write_text(json.dumps(receipt,sort_keys=True)+'\n',encoding='utf-8')
    return receipt
def main():
    freeze=json.loads((ROOT/'FREEZE.json').read_bytes());paths=freeze['host_paths']
    data=Path(paths['candidate_data']);out=Path(paths['model_data'])
    raw=json.loads((data/'candidate_stdout.json').read_bytes())
    rows=[];error=None
    if raw['error'] is not None or len(raw['rows'])!=4:raise ValueError('STOP_STIMULUS_NOT_READY')
    prompt=(ROOT/'prompt.txt').read_bytes()
    for index,row in enumerate(raw['rows']):
        image=data/f'row-{index:03d}'/'screen.png'
        before=sha(image)
        if before!=row['screen']['png_sha256']:raise ValueError('STOP_IMAGE_BINDING')
        argv=freeze['model_commands'][index]
        if sha(argv[0])!=freeze['cli']['sha256']:raise ValueError('STOP_CLI_IDENTITY')
        output=out/f'row-{index:03d}'
        process=run_command(argv,prompt,output,raw['fixture']['model_timeout_seconds'])
        parsed=None;first_error=None
        try:
            if process['exit_code']!=0 or process['timed_out'] or process['launch_error']:raise ValueError('STOP_MODEL_PROCESS')
            events=[json.loads(line) for line in (output/'stdout.bin').read_bytes().decode('utf-8').splitlines() if line]
            parsed=parse(events)
            if sha(image)!=before:raise ValueError('STOP_IMAGE_CHANGED')
        except (KeyError,ValueError,TypeError,UnicodeError) as exc:first_error=type(exc).__name__+':'+str(exc)
        rows.append(dict(index=index,image_sha256=before,process=process,parsed=parsed,error=first_error,authority_granted=False,actions_emitted=0))
        if first_error:error=first_error;break
    result=dict(schema='5260-a14-model-review-v1',freeze_sha256=sha(ROOT/'FREEZE.json'),candidate_raw_sha256=sha(data/'candidate_stdout.json'),prompt_sha256=sha(ROOT/'prompt.txt'),rows=rows,error=error)
    (out/'model_result.json').write_text(json.dumps(result,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(dict(rows=len(rows),error=error)))
    return 1 if error else 0
if __name__=='__main__':raise SystemExit(main())
