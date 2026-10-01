from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

from map01_telemetry_session_v1 import (
    Map01IndependentScorer,
    make_v12_command_handler,
    run_telemetry_control_loop,
)


class FakeBackend:
    sequence = 7


class FakeExecutor:
    def __init__(self):
        self.calls=[]
    def submit(self,*args): self.calls.append(("submit",)+args)
    def cancel(self,*args): self.calls.append(("cancel",)+args)


class ScriptedGame:
    def __init__(self, states):
        self.states=list(states); self.index=-1; self.current=self.states[0]
        self.thread_ids=[]
    def _touch(self): self.thread_ids.append(threading.get_ident())
    def is_episode_finished(self):
        self._touch(); self.index=min(self.index+1,len(self.states)-1); self.current=self.states[self.index]
        return self.current[2]
    def is_player_dead(self): self._touch(); return self.current[3]
    def get_game_variable(self, variable):
        self._touch(); return self.current[0] if variable=="kills" else self.current[1]


def pipe_with(*commands):
    r,w=os.pipe()
    os.write(w, ("\n".join(json.dumps(c) for c in commands)+"\n").encode())
    os.close(w)
    return r


class Tests(unittest.TestCase):
    def test_v12_command_routing_is_preserved(self):
        events=[]; exe=FakeExecutor(); finished=[]
        handler=make_v12_command_handler(
            emit=events.append,executor=exe,backend=FakeBackend(),on_finish=lambda: finished.append(True),clock_ns=lambda:123)
        submit={"op":"submit","id":"x","steps":[{"op":"hold"}],"expected_sequence":7,"valid_until_ns":999}
        self.assertTrue(handler(json.dumps(submit)))
        self.assertTrue(handler(json.dumps({"op":"cancel","id":"x"})))
        self.assertTrue(handler(json.dumps({"op":"clock"})))
        self.assertFalse(handler(json.dumps({"op":"finish"})))
        self.assertEqual(exe.calls,[('submit','x',[{'op':'hold'}],7,999),('cancel','x')])
        self.assertEqual([e['event'] for e in events],['command','command','command','clock','command'])
        self.assertEqual(finished,[True])

    def test_rejection_is_nonterminal(self):
        events=[]
        handler=make_v12_command_handler(emit=events.append,executor=FakeExecutor(),backend=FakeBackend(),on_finish=lambda:None)
        self.assertTrue(handler(json.dumps({"op":"unknown"})))
        self.assertEqual(events[-1]['event'],'rejected')

    def test_malformed_json_is_rejected_and_loop_can_continue(self):
        events=[]
        handler=make_v12_command_handler(emit=events.append,executor=FakeExecutor(),backend=FakeBackend(),on_finish=lambda:None)
        self.assertTrue(handler('{bad json'))
        self.assertEqual(events[-1]['event'],'rejected')

    def test_save_fixture_availability_matches_v12_contract(self):
        events=[]
        handler=make_v12_command_handler(emit=events.append,executor=FakeExecutor(),backend=FakeBackend(),on_finish=lambda:None)
        self.assertTrue(handler(json.dumps({"op":"save_fixture"})))
        self.assertEqual(events[-1]['reason'],'save_fixture is unavailable in measured control')
        saved=[]
        handler=make_v12_command_handler(emit=events.append,executor=FakeExecutor(),backend=FakeBackend(),on_finish=lambda:None,on_save_fixture=lambda:saved.append(1))
        self.assertFalse(handler(json.dumps({"op":"save_fixture"})))
        self.assertEqual(saved,[1])

    def test_progress_state_is_scorer_only_and_same_thread(self):
        game=ScriptedGame([(0,0,False,False),(1,0,False,False),(1,0,True,False)])
        events=[]
        with tempfile.TemporaryDirectory() as d:
            scorer=Map01IndependentScorer(game=game,kill_variable='kills',death_variable='deaths',out_dir=Path(d),control_started_ns=time.perf_counter_ns(),timeout_seconds=600)
            handler=make_v12_command_handler(emit=events.append,executor=FakeExecutor(),backend=FakeBackend(),on_finish=lambda:None)
            fd=pipe_with({"op":"clock"},{"op":"clock"},{"op":"finish"})
            stats,summary=run_telemetry_control_loop(fd=fd,scorer=scorer,command_handler=handler,sample_hz=1000)
            os.close(fd)
            samples=[json.loads(x) for x in scorer.sample_path.read_text().splitlines()]
            scorer_events=([json.loads(x) for x in scorer.event_path.read_text().splitlines()]
                           if scorer.event_path.exists() else [])
            self.assertTrue(samples)
            self.assertTrue(all(x['controller_visible'] is False for x in samples))
            self.assertTrue(all(x['controller_visible'] is False for x in scorer_events))
            controller_blob=json.dumps(events)
            self.assertNotIn('kill_count',controller_blob)
            self.assertNotIn('death_count',controller_blob)
            self.assertEqual(set(game.thread_ids),{summary['owner_thread_id']})
            self.assertEqual(stats.owner_thread_id,summary['owner_thread_id'])

    def test_kill_and_exit_become_independent_events(self):
        game=ScriptedGame([(0,0,False,False),(1,0,False,False),(1,0,True,False),(1,0,True,False)])
        with tempfile.TemporaryDirectory() as d:
            scorer=Map01IndependentScorer(game=game,kill_variable='kills',death_variable='deaths',out_dir=Path(d),control_started_ns=time.perf_counter_ns(),timeout_seconds=600)
            for _ in range(4):
                sample=scorer.sample()
                scorer.sink({'scheduled_ns':sample.sample_ns,'sample_started_ns':sample.sample_ns,'sample_finished_ns':sample.sample_ns,'start_lateness_ns':0,'missed_periods_before':0,'payload':sample})
            rows=[json.loads(x) for x in scorer.event_path.read_text().splitlines()]
            self.assertEqual([x['kind'] for x in rows],['KILL_COUNT_INCREASE','MAP_EXIT'])

    def test_timeout_terminal_is_not_map_exit(self):
        now=100_000_000_000
        game=ScriptedGame([(0,0,True,False)])
        with tempfile.TemporaryDirectory() as d:
            scorer=Map01IndependentScorer(game=game,kill_variable='kills',death_variable='deaths',out_dir=Path(d),control_started_ns=0,timeout_seconds=100,clock_ns=lambda:now)
            sample=scorer.sample()
            self.assertTrue(sample.episode_finished)
            self.assertFalse(sample.map_exit)

    def test_scorer_off_owner_thread_fails_closed(self):
        game=ScriptedGame([(0,0,False,False)])
        with tempfile.TemporaryDirectory() as d:
            scorer=Map01IndependentScorer(game=game,kill_variable='kills',death_variable='deaths',out_dir=Path(d),control_started_ns=0,timeout_seconds=600)
            errors=[]
            t=threading.Thread(target=lambda: _capture(errors, scorer.sample))
            t.start();t.join()
            self.assertEqual(len(errors),1)
            self.assertIn('owner thread',str(errors[0]))

    def test_terminal_mutation_requires_new_epoch(self):
        game=ScriptedGame([(0,0,False,False),(0,0,True,False),(1,0,True,False)])
        with tempfile.TemporaryDirectory() as d:
            scorer=Map01IndependentScorer(game=game,kill_variable='kills',death_variable='deaths',out_dir=Path(d),control_started_ns=0,timeout_seconds=600,clock_ns=_incrementing_clock())
            first=scorer.sample(); scorer.sink(_receipt(first))
            second=scorer.sample(); scorer.sink(_receipt(second))
            third=scorer.sample()
            with self.assertRaisesRegex(ValueError,'new scorer epoch'):
                scorer.sink(_receipt(third))

    def test_finish_stops_before_later_buffered_command(self):
        events=[]
        handler=make_v12_command_handler(emit=events.append,executor=FakeExecutor(),backend=FakeBackend(),on_finish=lambda:None)
        game=ScriptedGame([(0,0,False,False)]*5)
        with tempfile.TemporaryDirectory() as d:
            scorer=Map01IndependentScorer(game=game,kill_variable='kills',death_variable='deaths',out_dir=Path(d),control_started_ns=time.perf_counter_ns(),timeout_seconds=600)
            fd=pipe_with({"op":"finish"},{"op":"clock"})
            stats,_=run_telemetry_control_loop(fd=fd,scorer=scorer,command_handler=handler,sample_hz=35)
            os.close(fd)
            self.assertTrue(stats.stopped_by_command)
            self.assertEqual([e['command']['op'] for e in events if e['event']=='command'],['finish'])


def _capture(out, fn):
    try: fn()
    except Exception as e: out.append(e)

def _incrementing_clock():
    state={'n':0}
    def now(): state['n']+=1_000_000; return state['n']
    return now

def _receipt(sample):
    return {'scheduled_ns':sample.sample_ns,'sample_started_ns':sample.sample_ns,'sample_finished_ns':sample.sample_ns,'start_lateness_ns':0,'missed_periods_before':0,'payload':sample}

if __name__=='__main__': unittest.main()
