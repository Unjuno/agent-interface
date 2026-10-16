"""Reader retirement unit contract; controlled owned objects, no native producer."""
import hashlib,json,os,threading,unittest
from pathlib import Path
from codex_app_server_client_v2 import CodexAppServerClient

class RetiredProcess:
    def poll(self):return 0

class Reader:
    def __init__(self,alive=False,error=None):self.alive=alive;self.error=error;self.joins=[]
    def join(self,timeout=None):
        self.joins.append(timeout)
        if self.error:raise self.error
    def is_alive(self):return self.alive

class Journal:
    def __init__(self,closed=False,error=None):self.closed=closed;self.error=error;self.closes=0
    def close(self):
        self.closes+=1
        if self.error:raise self.error
        self.closed=True

class JournalLock:
    def __init__(self,forbidden=False):self.forbidden=forbidden;self.entries=0;self.releases=0
    def __enter__(self):
        self.entries+=1
        if self.forbidden:raise AssertionError('journal touched while reader remains live')
    def __exit__(self,*args):self.releases+=1

def client(alive=False,journal=True,closed=False,journal_error=None,reader_error=None):
    c=CodexAppServerClient.__new__(CodexAppServerClient)
    c.process=RetiredProcess();c._reader=Reader(alive,reader_error)
    c._journal=Journal(closed,journal_error) if journal else None
    c._journal_lock=JournalLock(forbidden=alive)
    return c

class ReaderRetirementTests(unittest.TestCase):
    def attempt(self,c,timeout=0.125):
        result={}
        try:
            value=c.close(timeout=timeout);result['return_value']=value;return value
        except BaseException as error:
            result.update(error_type=type(error).__name__,error_message=str(error));raise
        finally:
            root=os.environ.get('READER_CLOSE_UNIT_EVIDENCE')
            if root:
                data={'method':self._testMethodName,'kind':'controlled-owned-unit-objects','outcome':result,
                      'reader_alive':c._reader.is_alive(),'join_timeouts':c._reader.joins,
                      'journal_closed':c._journal.closed if c._journal else None,
                      'journal_close_calls':c._journal.closes if c._journal else None,
                      'journal_lock_entries':c._journal_lock.entries,'journal_lock_releases':c._journal_lock.releases}
                with (Path(root)/(self._testMethodName+'.json')).open('x',encoding='utf-8') as f:json.dump(data,f,indent=2);f.write('\n')
    def test_live_reader_preserves_open_journal_and_existing_holder(self):
        c=client(alive=True)
        with self.assertRaisesRegex(TimeoutError,'app-server reader close timed out'):self.attempt(c)
        self.assertFalse(c._journal.closed);self.assertEqual(c._journal.closes,0);self.assertEqual(c._journal_lock.entries,0)
    def test_live_reader_without_journal_reports_incomplete(self):
        c=client(alive=True,journal=False)
        with self.assertRaisesRegex(TimeoutError,'reader close timed out'):self.attempt(c)
        self.assertEqual(c._journal_lock.entries,0)
    def test_live_reader_with_closed_journal_reports_incomplete(self):
        c=client(alive=True,closed=True)
        with self.assertRaisesRegex(TimeoutError,'reader close timed out'):self.attempt(c)
        self.assertEqual(c._journal.closes,0)
    def test_retired_reader_closes_open_journal(self):
        c=client();self.assertIsNone(self.attempt(c));self.assertTrue(c._journal.closed)
        self.assertEqual(c._reader.joins,[0.125]);self.assertEqual(c._journal.closes,1);self.assertEqual(c._journal_lock.releases,1)
    def test_retired_reader_without_journal_returns_normally(self):
        c=client(journal=False);self.assertIsNone(self.attempt(c));self.assertEqual(c._journal_lock.entries,0)
    def test_explicit_none_timeout_preserves_unlimited_mode(self):
        c=client();self.assertIsNone(self.attempt(c,timeout=None));self.assertEqual(c._reader.joins,[None]);self.assertTrue(c._journal.closed)
    def test_journal_error_instance_preserved_and_lock_released(self):
        error=ValueError('owned journal failure');c=client(journal_error=error)
        with self.assertRaises(ValueError) as caught:self.attempt(c)
        self.assertIs(caught.exception,error);self.assertEqual(c._journal_lock.releases,1);self.assertFalse(c._journal.closed)
    def test_join_error_instance_preserved_without_journal_access(self):
        error=RuntimeError('owned reader join failure');c=client(reader_error=error)
        with self.assertRaises(RuntimeError) as caught:self.attempt(c)
        self.assertIs(caught.exception,error);self.assertEqual(c._journal_lock.entries,0);self.assertEqual(c._journal.closes,0)

if __name__=='__main__':unittest.main()
