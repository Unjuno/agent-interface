"""Independent A09 byte/publication custody audit, no producer imports."""
import hashlib
import json


def pipe_errors(row, freeze_sha256):
    errors=[]
    try:
        pipe=row['pipe'];producer=row['app']['focus_pipe']
        identity=pipe['identity'];child=producer['identity']
        if (type(identity['pipe_buf']) is not int or identity['pipe_buf']<512 or
                child['pipe_buf']!=identity['pipe_buf'] or child['nonblocking'] is not True or
                identity['read_inode']!=identity['write_inode'] or
                identity['write_inode']!=child['inode'] or child['fd']!=identity['write_fd']):
            errors.append('pipe_identity')
        if producer['first_error'] is not None:errors.append('producer_first_error')
        reads=pipe['reads'];buffer=b'';decoded=[];eof=False;previous=0;total=0
        for read in reads:
            start,end=read['started_ns'],read['completed_ns']
            if any(type(t) is not int for t in (start,end)) or not previous<=start<=end:
                errors.append('read_clock')
            previous=end
            if eof:errors.append('read_after_eof')
            if read['status']=='EAGAIN':continue
            if read['status'] not in ('DATA','EOF'):
                errors.append('read_error');continue
            chunk=bytes.fromhex(read['hex'])
            if read['bytes']!=len(chunk) or read['sha256']!=hashlib.sha256(chunk).hexdigest():
                errors.append('read_bytes')
            if read['status']=='EOF':
                eof=True
                if chunk or buffer:errors.append('partial_or_nonempty_eof')
                continue
            if not chunk:errors.append('empty_data')
            total+=len(chunk)
            if total>16384:errors.append('total_budget')
            buffer+=chunk
            while b'\n' in buffer:
                line,buffer=buffer.split(b'\n',1)
                if len(line)+1>512:errors.append('frame_budget')
                value=json.loads(line.decode('utf-8'))
                canonical=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
                if canonical!=line+b'\n':errors.append('noncanonical_frame')
                decoded.append({'value':value,'seen_ns':end})
        if not eof or pipe['eof'] is not True:errors.append('missing_eof')
        if decoded!=pipe['frames']:errors.append('decoded_frame_binding')
        for retained in pipe['frames']:
            if type(retained.get('seen_ns')) is not int or any(
                    type(retained['value'].get(name)) is not int for name in
                    ('pid','target_id','sequence','event_ns','written_ns')):
                errors.append('retained_frame_types')
        publications=producer['publications']
        events=[event for event in row['app']['events'] if event['kind'] in ('FocusIn','FocusOut')]
        if len(publications)!=len(decoded) or len(events)!=len(decoded):errors.append('publication_count')
        for index,(frame,publication,event) in enumerate(zip(decoded,publications,events),1):
            value=frame['value'];trace=publication['trace']
            if any(type(value.get(name)) is not int or value[name]<=0
                   for name in ('pid','target_id','sequence','event_ns','written_ns')):
                errors.append('frame_types')
            if any(type(trace.get(name)) is not int or trace[name]<=0
                   for name in ('started_ns','completed_ns','requested_bytes','written_bytes')):
                errors.append('publication_types')
            blob=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
            if (value!=publication['value'] or trace['frame_utf8'].encode()!=blob or
                    trace['sha256']!=hashlib.sha256(blob).hexdigest() or
                    trace['requested_bytes']!=len(blob) or trace['written_bytes']!=len(blob) or
                    trace['write_error'] is not None):errors.append('publication_bytes')
            if (value.get('schema')!='issue5260-a09-focus-pipe-v1' or
                    value.get('token')!=row['token'] or value.get('pid')!=row['app_pid'] or
                    value.get('target_id')!=row['ready']['geometry']['target_id'] or
                    value.get('freeze_sha256')!=freeze_sha256):errors.append('source_binding')
            if (value['sequence']!=index or event['sequence']!=index or
                    value['kind']!=event['kind'] or value['widget']!=event['widget'] or
                    value['event_ns']!=event['monotonic_ns']):errors.append('event_binding')
            if not (value['event_ns']<=value['written_ns']<=trace['started_ns']<=frame['seen_ns'] and
                    trace['started_ns']<=trace['completed_ns']):errors.append('publication_clock')
        closes=pipe['closes']
        if ([(close['name'],close['fd']) for close in closes]!=
                [('write_fd',identity['write_fd']),('read_fd',identity['read_fd'])] or
                any('error' in close or close['started_ns']>close['completed_ns'] for close in closes)):
            errors.append('parent_close')
        close=producer['close']
        if close['fd']!=child['fd'] or 'error' in close or close['started_ns']>close['completed_ns']:
            errors.append('producer_close')
    except (KeyError,TypeError,ValueError,AttributeError,IndexError) as error:
        errors.append('malformed_pipe:'+type(error).__name__)
    return errors
