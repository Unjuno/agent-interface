"""Formal synthetic integration benchmark for MAP01 telemetry-only session v1.

This uses a fake DoomGame-shaped object because this container has no vizdoom.
It measures scheduling/persistence integration only; it is not a live MAP01 run.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import tempfile
import threading
import time

from map01_telemetry_session_v1 import (
    Map01IndependentScorer,
    make_v12_command_handler,
    run_telemetry_control_loop,
)


def percentile(values, p):
    rows=sorted(values)
    if not rows: return None
    index=min(len(rows)-1,max(0,round((len(rows)-1)*p)))
    return rows[index]


def cpu_model():
    try:
        for line in Path('/proc/cpuinfo').read_text(encoding='utf-8',errors='replace').splitlines():
            if line.lower().startswith('model name'):
                return line.split(':',1)[1].strip()
    except OSError:
        return None
    return None


class FakeBackend:
    sequence=123


class FakeExecutor:
    def __init__(self): self.calls=[]
    def submit(self,*args): self.calls.append(('submit',args))
    def cancel(self,*args): self.calls.append(('cancel',args))


class FakeGame:
    """Deterministic running-episode getter workload with sparse kill progress."""
    def __init__(self):
        self.sample_index=-1
        self.current_index=0
        self.thread_ids=[]
    def _touch(self): self.thread_ids.append(threading.get_ident())
    def is_episode_finished(self):
        self._touch(); self.sample_index+=1; self.current_index=self.sample_index
        return False
    def is_player_dead(self): self._touch(); return False
    def get_game_variable(self, variable):
        self._touch()
        if variable=='kills': return self.current_index//18
        if variable=='deaths': return 0
        raise KeyError(variable)


def one_run(duration_s, sample_hz, command_hz):
    read_fd,write_fd=os.pipe()
    game=FakeGame(); backend=FakeBackend(); executor=FakeExecutor(); controller_events=[]
    command_latency_ns=[]
    start_ns=time.perf_counter_ns()
    stop_ns=start_ns+int(duration_s*1e9)
    command_period_ns=round(1e9/command_hz)

    def emit(row):
        controller_events.append(row)
        if row.get('event')=='command':
            sent=row.get('command',{}).get('sent_ns')
            if type(sent) is int:
                command_latency_ns.append(row['received_ns']-sent)

    finished=[]
    handler=make_v12_command_handler(
        emit=emit,executor=executor,backend=backend,on_finish=lambda:finished.append(True))

    def writer():
        target=start_ns; seq=0
        while True:
            target+=command_period_ns
            if target>=stop_ns: break
            delay=(target-time.perf_counter_ns())/1e9
            if delay>0: time.sleep(delay)
            sent=time.perf_counter_ns()
            payload={'op':'clock','seq':seq,'sent_ns':sent}
            os.write(write_fd,(json.dumps(payload,separators=(',',':'))+'\n').encode())
            seq+=1
        sent=time.perf_counter_ns()
        os.write(write_fd,(json.dumps({'op':'finish','sent_ns':sent},separators=(',',':'))+'\n').encode())
        os.close(write_fd)

    thread=threading.Thread(target=writer,name='synthetic-command-writer')
    thread.start()
    with tempfile.TemporaryDirectory() as d:
        scorer=Map01IndependentScorer(
            game=game,kill_variable='kills',death_variable='deaths',out_dir=Path(d),
            control_started_ns=start_ns,timeout_seconds=600)
        stats,summary=run_telemetry_control_loop(
            fd=read_fd,scorer=scorer,command_handler=handler,sample_hz=sample_hz)
        thread.join(); os.close(read_fd)
        samples=[json.loads(line) for line in scorer.sample_path.read_text(encoding='utf-8').splitlines()]
        scorer_events=(
            [json.loads(line) for line in scorer.event_path.read_text(encoding='utf-8').splitlines()]
            if scorer.event_path.exists() else []
        )
        controller_blob=json.dumps(controller_events,sort_keys=True)
        leak=('kill_count' in controller_blob or 'death_count' in controller_blob or
              'independent-progress-' in controller_blob)
        owner_ids=set(game.thread_ids)
        lateness=[row['start_lateness_ns'] for row in samples]
        callback=[row['sample_finished_ns']-row['sample_started_ns'] for row in samples]
        return {
            'samples':stats.samples,
            'commands':stats.commands,
            'missed_sample_periods':stats.missed_sample_periods,
            'stopped_by_command':stats.stopped_by_command,
            'scorer_records':len(samples),
            'scorer_events':len(scorer_events),
            'owner_thread_consistent':owner_ids=={summary['owner_thread_id']}=={stats.owner_thread_id},
            'controller_scorer_leak':leak,
            'finish_calls':len(finished),
            'sample_lateness_ns':lateness,
            'sample_callback_ns':callback,
            'command_latency_ns':command_latency_ns,
        }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repetitions',type=int,default=12)
    ap.add_argument('--duration-s',type=float,default=1.0)
    ap.add_argument('--sample-hz',type=float,default=35.0)
    ap.add_argument('--command-hz',type=float,default=50.0)
    args=ap.parse_args()
    runs=[one_run(args.duration_s,args.sample_hz,args.command_hz) for _ in range(args.repetitions)]
    lateness=[v for r in runs for v in r['sample_lateness_ns']]
    callback=[v for r in runs for v in r['sample_callback_ns']]
    command=[v for r in runs for v in r['command_latency_ns']]
    period_ns=round(1e9/args.sample_hz)
    checks={
        'all_runs_stop_on_finish':all(r['stopped_by_command'] and r['finish_calls']==1 for r in runs),
        'zero_missed_sample_periods':sum(r['missed_sample_periods'] for r in runs)==0,
        'all_scorer_getters_on_owner_thread':all(r['owner_thread_consistent'] for r in runs),
        'controller_scorer_leak_zero':not any(r['controller_scorer_leak'] for r in runs),
        'sample_records_match_stats':all(r['scorer_records']==r['samples'] for r in runs),
        'sample_lateness_p99_below_one_period':percentile(lateness,.99)<period_ns,
        'command_latency_p99_below_one_period':percentile(command,.99)<period_ns,
    }
    result={
        'schema':'map01-telemetry-session-integration-benchmark-v1',
        'environment':{
            'python':platform.python_version(),
            'kernel':platform.release(),
            'machine':platform.machine(),
            'cpu_model':cpu_model(),
            'cpu_affinity':sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,
            'cpu_clock':'not pinned / unavailable',
            'vizdoom_available':False,
            'concurrency':'one polling/scorer owner thread + one synthetic command writer thread',
        },
        'workload':{
            'repetitions':args.repetitions,'duration_s_each':args.duration_s,
            'sample_hz':args.sample_hz,'command_hz':args.command_hz,
            'game':'deterministic fake DoomGame-shaped getter workload',
            'persistence':'JSONL scorer samples/events + JSON summary in TemporaryDirectory',
        },
        'totals':{
            'samples':sum(r['samples'] for r in runs),
            'commands':sum(r['commands'] for r in runs),
            'missed_sample_periods':sum(r['missed_sample_periods'] for r in runs),
            'scorer_events':sum(r['scorer_events'] for r in runs),
        },
        'sample_start_lateness_us':{
            'median':statistics.median(lateness)/1e3,'p95':percentile(lateness,.95)/1e3,
            'p99':percentile(lateness,.99)/1e3,'max':max(lateness)/1e3,
        },
        'sample_callback_duration_us':{
            'median':statistics.median(callback)/1e3,'p95':percentile(callback,.95)/1e3,
            'p99':percentile(callback,.99)/1e3,'max':max(callback)/1e3,
        },
        'command_write_to_handler_us':{
            'median':statistics.median(command)/1e3,'p95':percentile(command,.95)/1e3,
            'p99':percentile(command,.99)/1e3,'max':max(command)/1e3,
        },
        'checks':checks,
        'pass':all(checks.values()),
        'runs':[{k:v for k,v in r.items() if not k.endswith('_ns')} for r in runs],
        'scope':'synthetic session-integration benchmark only; no ViZDoom/X11/model/GUI/live MAP01 allocation',
    }
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['pass'] else 1)

if __name__=='__main__': main()
