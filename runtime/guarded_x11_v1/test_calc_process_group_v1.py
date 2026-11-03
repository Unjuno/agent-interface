import tempfile
import unittest
from pathlib import Path

from .calc_process_group_v1 import (
    _SIGKILL, _SIGTERM, _parse_proc_stat, advance_process_group_custody,
    cleanup_process_group, make_launcher_process_group_custody,
    make_process_group_custody, read_linux_process_group)


LEADER, LEADER_TICKS = 4100, 70001
TARGET, TARGET_TICKS = 4101, 70002


def member(pid, ticks, pgid=LEADER, sid=LEADER):
    return {'pid':pid,'start_ticks':ticks,'process_group':pgid,'session_id':sid}


def custody(rows=None):
    return make_process_group_custody(leader_pid=LEADER,
        leader_start_ticks=LEADER_TICKS,target_pid=TARGET,
        target_start_ticks=TARGET_TICKS,
        group_snapshot=(rows if rows is not None else [
            member(LEADER,LEADER_TICKS),member(TARGET,TARGET_TICKS)]))


class Clock:
    def __init__(self): self.now=0.0
    def monotonic(self): return self.now
    def sleep(self,seconds): self.now += seconds


class ProcessGroupCustodyTests(unittest.TestCase):
    def test_proc_stat_parser_handles_parentheses_in_process_name(self):
        values=['12',str(LEADER),str(LEADER)] + ['0']*15 + [str(LEADER_TICKS)]
        raw=f'{TARGET} (calc (worker)) S ' + ' '.join(values)
        row=_parse_proc_stat(TARGET,raw)
        self.assertEqual(row['process_group'],LEADER)
        self.assertEqual(row['session_id'],LEADER)
        self.assertEqual(row['start_ticks'],LEADER_TICKS)

    def test_proc_snapshot_reads_only_exact_group_and_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for pid,pgid,sid,ticks in ((LEADER,LEADER,LEADER,LEADER_TICKS),
                    (TARGET,LEADER,LEADER,TARGET_TICKS),(99,99,99,8)):
                proc=root/str(pid); proc.mkdir()
                values=['1',str(pgid),str(sid)]+['0']*15+[str(ticks)]
                (proc/'stat').write_text(
                    f'{pid} (test process) S '+' '.join(values),encoding='ascii')
            rows=read_linux_process_group(LEADER,LEADER,proc_root=root)
        self.assertEqual([row['pid'] for row in rows],[LEADER,TARGET])

    def test_custody_requires_exact_dedicated_group_members(self):
        with self.assertRaisesRegex(ValueError,'unowned or changed'):
            custody([member(LEADER,LEADER_TICKS),member(TARGET,TARGET_TICKS),
                     member(999,88)])
        with self.assertRaisesRegex(ValueError,'both be live'):
            custody([member(LEADER,LEADER_TICKS)])
        with self.assertRaisesRegex(ValueError,'unowned or changed'):
            custody([member(LEADER,LEADER_TICKS+1),member(TARGET,TARGET_TICKS)])

    def test_launcher_only_custody_advances_and_cleans_without_certifying_exit(self):
        initial=make_launcher_process_group_custody(
            leader_pid=LEADER,leader_start_ticks=LEADER_TICKS,
            group_snapshot=[member(LEADER,LEADER_TICKS)])
        self.assertIsNone(initial['target'])
        replacement=TARGET+1; replacement_ticks=TARGET_TICKS+10
        rows=[member(LEADER,LEADER_TICKS),
            dict(member(replacement,replacement_ticks),parent_pid=LEADER)]
        advanced=advance_process_group_custody(initial,target_pid=replacement,
            target_start_ticks=replacement_ticks,group_snapshot=rows)
        self.assertEqual(advanced['target'],{'pid':replacement,
            'start_ticks':replacement_ticks})
        self.assertEqual(advanced['expected_members'],{
            str(LEADER):LEADER_TICKS,str(replacement):replacement_ticks})
        group=[member(LEADER,LEADER_TICKS)]
        clock=Clock()
        result=cleanup_process_group(initial,
            group_snapshot_reader=lambda _pgid,_sid:list(group),
            killpg=lambda _pgid,_sig:group.clear(),
            monotonic=clock.monotonic,sleep=clock.sleep)
        self.assertEqual(result['status'],'terminated')
        self.assertTrue(result['verified_empty'])
        self.assertFalse(result['clean_exit_verified'])

    def test_launcher_only_custody_refuses_an_unaccounted_early_child(self):
        with self.assertRaisesRegex(ValueError,'unowned member'):
            make_launcher_process_group_custody(
                leader_pid=LEADER,leader_start_ticks=LEADER_TICKS,
                group_snapshot=[member(LEADER,LEADER_TICKS),
                    dict(member(TARGET,TARGET_TICKS),parent_pid=LEADER)])

    def test_pre_review_custody_can_advance_to_exact_replacement_child(self):
        replacement=TARGET+1; replacement_ticks=TARGET_TICKS+10
        rows=[member(LEADER,LEADER_TICKS),
            dict(member(replacement,replacement_ticks),parent_pid=LEADER)]
        result=advance_process_group_custody(custody(),target_pid=replacement,
            target_start_ticks=replacement_ticks,group_snapshot=rows,
            process_generation_reader=lambda _pid:None)
        self.assertEqual(result['launcher'],{'pid':LEADER,'start_ticks':LEADER_TICKS})
        self.assertEqual(result['target'],{'pid':replacement,
            'start_ticks':replacement_ticks})
        self.assertEqual(result['expected_members'],{
            str(LEADER):LEADER_TICKS,str(replacement):replacement_ticks})

    def test_pre_review_custody_advance_refuses_live_old_child_and_unowned_members(self):
        replacement=TARGET+1; replacement_ticks=TARGET_TICKS+10
        rows=[member(LEADER,LEADER_TICKS),
            dict(member(replacement,replacement_ticks),parent_pid=LEADER)]
        live={'pid':TARGET,'start_ticks':TARGET_TICKS}
        with self.assertRaisesRegex(ValueError,'still live'):
            advance_process_group_custody(custody(),target_pid=replacement,
                target_start_ticks=replacement_ticks,group_snapshot=rows,
                process_generation_reader=lambda _pid:live)
        with self.assertRaisesRegex(ValueError,'unowned or changed'):
            advance_process_group_custody(custody(),target_pid=replacement,
                target_start_ticks=replacement_ticks,
                group_snapshot=rows+[member(999,90)],
                process_generation_reader=lambda _pid:None)

    def test_pre_review_custody_advance_requires_replacement_direct_child(self):
        replacement=TARGET+1; replacement_ticks=TARGET_TICKS+10
        rows=[member(LEADER,LEADER_TICKS),
            dict(member(replacement,replacement_ticks),parent_pid=999)]
        with self.assertRaisesRegex(ValueError,'exact direct child'):
            advance_process_group_custody(custody(),target_pid=replacement,
                target_start_ticks=replacement_ticks,group_snapshot=rows,
                process_generation_reader=lambda _pid:None)

    def test_pre_review_custody_advance_requires_only_launcher_and_new_generation(self):
        replacement=TARGET+1; replacement_ticks=TARGET_TICKS+10
        rows=[member(LEADER,LEADER_TICKS),
            dict(member(replacement,replacement_ticks),parent_pid=LEADER),
            member(TARGET,TARGET_TICKS)]
        with self.assertRaisesRegex(ValueError,'unowned or changed'):
            advance_process_group_custody(custody(),target_pid=replacement,
                target_start_ticks=replacement_ticks,group_snapshot=rows,
                process_generation_reader=lambda _pid:None)

    def test_term_exit_is_verified_empty_but_never_clean_exit(self):
        group=[member(LEADER,LEADER_TICKS),member(TARGET,TARGET_TICKS)]
        signals=[]
        clock=Clock()
        def killpg(pgid,sig):
            signals.append((pgid,sig)); group.clear()
        result=cleanup_process_group(custody(),
            group_snapshot_reader=lambda _pgid,_sid:list(group),
            killpg=killpg,monotonic=clock.monotonic,sleep=clock.sleep)
        self.assertEqual(result['status'],'terminated')
        self.assertTrue(result['verified_empty'])
        self.assertFalse(result['clean_exit_verified'])
        self.assertEqual(result['signals_sent'],['SIGTERM'])
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])
        self.assertEqual(len(signals),1)

    def test_term_timeout_escalates_only_after_group_revalidation(self):
        group=[member(LEADER,LEADER_TICKS),member(TARGET,TARGET_TICKS)]
        signals=[]
        clock=Clock()
        def killpg(pgid,sig):
            signals.append(sig)
            if sig==_SIGKILL: group.clear()
        result=cleanup_process_group(custody(),
            group_snapshot_reader=lambda _pgid,_sid:list(group),killpg=killpg,
            monotonic=clock.monotonic,sleep=clock.sleep,
            term_grace_s=.03,kill_settle_s=.03)
        self.assertEqual(result['status'],'killed')
        self.assertTrue(result['verified_empty'])
        self.assertFalse(result['clean_exit_verified'])
        self.assertEqual(result['signals_sent'],['SIGTERM','SIGKILL'])
        self.assertEqual(signals,[_SIGTERM,_SIGKILL])

    def test_unknown_or_reused_group_member_refuses_all_signals(self):
        signals=[]
        rows=[member(LEADER,LEADER_TICKS),member(TARGET,TARGET_TICKS),
              member(999,90)]
        result=cleanup_process_group(custody(),
            group_snapshot_reader=lambda _pgid,_sid:rows,
            killpg=lambda pgid,sig:signals.append((pgid,sig)))
        self.assertEqual(result['reason'],'process_group_identity_unavailable')
        self.assertFalse(result['verified_empty'])
        self.assertEqual(signals,[])

    def test_pid_reuse_before_kill_refuses_escalation(self):
        original=[member(LEADER,LEADER_TICKS),member(TARGET,TARGET_TICKS)]
        changed=[member(LEADER,LEADER_TICKS),member(TARGET,TARGET_TICKS+1)]
        calls=[]
        def read(_pgid,_sid):
            return original if len(calls)==0 else changed
        def killpg(pgid,sig): calls.append(sig)
        clock=Clock()
        result=cleanup_process_group(custody(),group_snapshot_reader=read,
            killpg=killpg,monotonic=clock.monotonic,sleep=clock.sleep,
            term_grace_s=.02,kill_settle_s=.02)
        self.assertEqual(result['reason'],'process_group_identity_changed_after_term')
        self.assertEqual(calls,[_SIGTERM])
        self.assertNotIn('SIGKILL',result['signals_sent'])

    def test_group_that_survives_kill_remains_unknown(self):
        group=[member(LEADER,LEADER_TICKS),member(TARGET,TARGET_TICKS)]
        signals=[]; clock=Clock()
        result=cleanup_process_group(custody(),
            group_snapshot_reader=lambda _pgid,_sid:list(group),
            killpg=lambda _pgid,sig:signals.append(sig),
            monotonic=clock.monotonic,sleep=clock.sleep,
            term_grace_s=0,kill_settle_s=.02)
        self.assertEqual(result['reason'],'process_group_not_empty_after_kill')
        self.assertEqual(signals,[_SIGTERM,_SIGKILL])
        self.assertFalse(result['verified_empty'])
        self.assertIsNone(result['task_success'])

    def test_empty_group_is_not_reported_as_clean_target_exit(self):
        result=cleanup_process_group(custody(),
            group_snapshot_reader=lambda _pgid,_sid:[])
        self.assertEqual(result['status'],'already_empty')
        self.assertTrue(result['verified_empty'])
        self.assertFalse(result['clean_exit_verified'])


if __name__ == '__main__':
    unittest.main()
