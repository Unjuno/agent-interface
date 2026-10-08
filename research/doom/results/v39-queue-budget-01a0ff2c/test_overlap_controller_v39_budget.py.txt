"""Deterministic source/caller regressions; no controller/game/client imports."""
import ast
import io
import json
import os
from pathlib import Path
import queue
from types import SimpleNamespace
import unittest

SOURCE = Path(os.environ.get('V39_WAIT_SOURCE', Path(__file__).with_name('map01_overlap_controller_v39.py')))

class Clock:
    def __init__(self): self.value = 0.
    def monotonic(self): return self.value

class Events:
    def __init__(self, clock, rows):
        self.clock, self.rows = clock, list(rows)
    def get(self, timeout):
        start = self.clock.value
        if self.rows and self.rows[0][0] <= start + timeout:
            at,row = self.rows.pop(0)
            self.clock.value = max(start,at)
            return row
        self.clock.value += timeout
        raise queue.Empty()

def harness(rows, done_at=None, invalidation=False):
    tree = ast.parse(SOURCE.read_bytes())
    main = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    wait = next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='wait')
    loop = next(n for n in ast.walk(main) if isinstance(n,ast.While) and ast.unparse(n.test)=='not future.done()')
    post = next(n for n in main.body if isinstance(n,ast.For))
    post = next(n for n in ast.walk(post) if isinstance(n,ast.If) and ast.unparse(n.test)=='current_terminal is None')
    setup = '''def factory(incoming, process, future, invalidation_monitor, planner):
 latest = None
 current_cover = 'cover'
 current_terminal = None
 invalidation = None
 planner_interrupt = None
 planner_handle = object()
 cover_terminals = []
'''
    factory = ast.parse(setup).body[0]
    factory.body.append(wait)
    factory.body.extend(ast.parse('return wait, lambda: latest').body)
    outer = ast.parse(setup).body[0]
    outer.name = 'caller'
    outer.body += [wait, loop, post]
    outer.body.extend(ast.parse('return current_terminal, invalidation, planner_interrupt, latest').body)
    clock = Clock()
    process = SimpleNamespace(poll=lambda:None,stdin=io.StringIO())
    terminal = {'event':'terminal','id':'cover','terminal_ns':130000000}
    def cancelled(planner,handle,process,wait,identifier):
        process.stdin.write(json.dumps({'op':'cancel','id':identifier})+'\n')
        return planner.interrupt(handle),wait(lambda r:r['event']=='terminal')
    scope = {'time':clock,'queue':queue,'json':json,'cancel_invalidated_cover':cancelled}
    module = ast.fix_missing_locations(ast.Module(body=[factory,outer],type_ignores=[]))
    exec(compile(module,str(SOURCE),'exec'),scope)
    monitor = SimpleNamespace(observe=lambda row:{'reason':'fixture_decline'} if invalidation else None)
    planner = SimpleNamespace(interrupt=lambda handle:'interrupted')
    future = SimpleNamespace(done=lambda:clock.value>=done_at) if done_at is not None else None
    args = (Events(clock,rows),process,future,monitor,planner)
    wait,latest = scope['factory'](*args)
    return wait,latest,clock,process,lambda:scope['caller'](*args)

OBS = {'event':'observation','sequence':7}
TERM = {'event':'terminal','id':'cover','terminal_ns':180000000}

class BudgetTests(unittest.TestCase):
    def test_empty_short_budget_returns_at_deadline(self):
        wait,latest,clock,process,caller = harness([])
        with self.assertRaises(TimeoutError): wait(lambda r:False,timeout=.05)
        self.assertAlmostEqual(clock.value,.05)
    def test_late_terminal_remains_available_for_followup(self):
        wait,latest,clock,process,caller = harness([(.075,TERM)])
        with self.assertRaises(TimeoutError): wait(lambda r:r['event']=='terminal',timeout=.05)
        self.assertIs(wait(lambda r:True,timeout=.1),TERM)
        self.assertAlmostEqual(clock.value,.075)
    def test_unrelated_observation_does_not_restart_budget(self):
        wait,latest,clock,process,caller = harness([(.09,OBS),(.18,TERM)])
        with self.assertRaises(TimeoutError): wait(lambda r:r['event']=='terminal',timeout=.1)
        self.assertAlmostEqual(clock.value,.1)
        self.assertIs(latest(),OBS)
    def test_fresh_terminal_wins_before_deadline(self):
        wait,latest,clock,process,caller = harness([(.02,TERM)])
        self.assertIs(wait(lambda r:True,timeout=.05),TERM)
        self.assertAlmostEqual(clock.value,.02)
    def test_late_policy_is_monitored_on_next_call(self):
        wait,latest,clock,process,caller = harness([(.075,OBS)],invalidation=True)
        with self.assertRaises(TimeoutError): wait(lambda r:True,timeout=.05)
        monitor = SimpleNamespace(observe=lambda row:{'reason':'decline'})
        self.assertEqual(wait(lambda r:True,timeout=.1,observation_monitor=monitor)['event'],'policy_invalidation')
        self.assertIs(latest(),OBS)
    def test_completed_model_cancels_then_processes_late_policy(self):
        wait,latest,clock,process,caller = harness([(.09,{'event':'unrelated'}),(.125,OBS),(.13,TERM)],done_at=.095,invalidation=True)
        terminal,invalid,interrupt,last = caller()
        self.assertIs(terminal,TERM)
        self.assertEqual(invalid,{'reason':'fixture_decline'})
        self.assertEqual(interrupt,'interrupted')
        self.assertIs(last,OBS)
        self.assertEqual([json.loads(x) for x in process.stdin.getvalue().splitlines()],[{'op':'cancel','id':'cover'}])
    def test_pending_model_invalidates_before_matching_terminal(self):
        wait,latest,clock,process,caller = harness([(.09,{'event':'unrelated'}),(.125,OBS),(.13,TERM)],done_at=.5,invalidation=True)
        terminal,invalid,interrupt,last = caller()
        self.assertIs(terminal,TERM)
        self.assertEqual(invalid,{'reason':'fixture_decline'})
        self.assertEqual(interrupt,'interrupted')
        self.assertEqual(len(process.stdin.getvalue().splitlines()),1)
    def test_completed_model_does_not_renew_late_terminal(self):
        wait,latest,clock,process,caller = harness([(.09,OBS),(.18,TERM)],done_at=.095)
        terminal,invalid,interrupt,last = caller()
        self.assertIs(terminal,TERM)
        self.assertIsNone(invalid)
        self.assertEqual([json.loads(x) for x in process.stdin.getvalue().splitlines()],[{'op':'cancel','id':'cover'}])

if __name__=='__main__': unittest.main()
