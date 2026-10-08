from __future__ import annotations
class AuthorityEndedNotReady(ValueError): pass

def _captures(post):
    n=post.get('captures'); seq=post.get('sequence')
    if type(n) is not int or n<1 or n>2: raise AuthorityEndedNotReady('one or two bounded post-authority captures required')
    if type(seq) is not int or seq<1: raise AuthorityEndedNotReady('fresh post-authority sequence required')
    if n==1:
        seqs=post.get('sequences')
        if seqs is not None and seqs != [seq]: raise AuthorityEndedNotReady('single-capture sequence evidence mismatch')
        return
    seqs=post.get('sequences')
    if type(seqs) is not list or len(seqs)!=n or any(type(x) is not int or x<1 for x in seqs): raise AuthorityEndedNotReady('multi-capture sequence evidence required')
    if any(b<=a for a,b in zip(seqs,seqs[1:])): raise AuthorityEndedNotReady('post-authority sequences must increase')
    if post.get('selection_rule')!='latest' or seq!=seqs[-1]: raise AuthorityEndedNotReady('multi-capture evidence must select latest sequence')

def to_caller_execution_decision(receipt):
    if type(receipt) is not dict: raise AuthorityEndedNotReady('terminal receipt object required')
    if receipt.get('terminal_status')!='authority_ended': raise AuthorityEndedNotReady('scheduled authority_ended status required')
    if receipt.get('release_verified') is not True: raise AuthorityEndedNotReady('verified release required')
    if receipt.get('keys_down')!=[] or receipt.get('buttons_down')!=[]: raise AuthorityEndedNotReady('verified empty input state required')
    if receipt.get('post_release_input_admissions')!=0: raise AuthorityEndedNotReady('post-release input admission forbidden')
    completed=receipt.get('steps_completed')
    if type(completed) is not int or completed<0: raise AuthorityEndedNotReady('nonnegative completed step count required')
    post=receipt.get('post_authority')
    if type(post) is not dict: raise AuthorityEndedNotReady('post-authority observation required')
    if post.get('grants_input_authority') is not False: raise AuthorityEndedNotReady('post-authority observation must not grant input authority')
    if post.get('tail_program_steps_resumed')!=0: raise AuthorityEndedNotReady('old program tail must not resume')
    _captures(post)
    if post.get('sequence_advanced') is not True: raise AuthorityEndedNotReady('post-authority observation must advance sequence')
    if post.get('error') is not None: raise AuthorityEndedNotReady('post-authority observation error')
    if post.get('within_lifecycle_deadline') is not True: raise AuthorityEndedNotReady('post-authority observation outside lifecycle deadline')
    f=post.get('snapshot_finished_ns'); d=post.get('lifecycle_deadline_ns')
    if type(f) is not int or type(d) is not int or f>d: raise AuthorityEndedNotReady('post-authority timing receipt invalid')
    return {'status':'safe_yield','reason':'authority_unavailable','completed_actions':completed}
