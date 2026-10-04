"""Supplementary read-only poll completeness; original frozen audit unchanged."""
def sample_errors(row):
    if row.get('mode')=='NOW_TARGET':return []
    try:
        gate=row['injection']['gate'];reads=row['pipe']['reads'];samples=gate['samples']
        start,end=gate['started_ns'],gate['decided_ns']
        if any(type(t) is not int or t<=0 for t in (start,end)) or start>end:
            return ['poll_window']
        endings=[]
        for index,read in enumerate(reads,1):
            if (read['status'] in ('EAGAIN','EOF') and start<=read['started_ns']<=read['completed_ns']<=end):
                endings.append(index)
        counts=[sample['read_attempts'] for sample in samples]
        if (not endings or any(type(count) is not int for count in counts) or counts!=endings):
            return ['missing_duplicate_or_unbound_poll']
        for index,sample in enumerate(samples):
            count=sample['read_attempts'];checked=sample['checked_ns']
            if type(checked) is not int or not reads[count-1]['completed_ns']<=checked<=end:
                return ['poll_clock']
            if index+1<len(samples):
                next_first=reads[count]
                if checked>next_first['started_ns']:return ['poll_after_next_read']
        if samples[-1]['checked_ns']!=end:return ['last_poll_not_decision']
        return []
    except (KeyError,TypeError,ValueError,IndexError):return ['malformed_poll_custody']
