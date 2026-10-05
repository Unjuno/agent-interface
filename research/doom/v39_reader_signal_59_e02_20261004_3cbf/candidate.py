def repair(source):
    import hashlib
    if hashlib.sha256(source).hexdigest()!='a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e':
        raise ValueError('original source identity')
    newline=b'\n'  # pinned function sites are LF; original mixed final CRLF retained
    before=b'    def reader():'+newline+b'        for line in process.stdout:'+newline+b'            row = json.loads(line); all_events.append(row); incoming.put(row)'
    after=newline.join([b'    class _SessionReaderFailure(RuntimeError):',b'        pass',b'    def reader():',b'        try:',b'            for line in process.stdout:',b'                row = json.loads(line); all_events.append(row); incoming.put(row)',b'        except Exception as exc:',b'            incoming.put(_SessionReaderFailure(exc))'])
    target=b'            if row["event"] == "observation":'
    replacement=newline.join([b'            if isinstance(row, _SessionReaderFailure):',b'                raise row from row.args[0]',target])
    if source.count(before)!=1 or source.count(target)!=1:
        raise ValueError('literal boundary mismatch')
    result=source.replace(before,after).replace(target,replacement)
    if result.replace(after,before).replace(replacement,target)!=source:
        raise ValueError('inverse repair mismatch')
    return result

def extract(source):
    import ast
    import json
    import queue
    import time
    tree=ast.parse(source.decode())
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    nodes=[n for n in main.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('reader','wait','_SessionReaderFailure')]
    if [n.name for n in nodes]!=['_SessionReaderFailure','reader','wait']:
        raise ValueError('candidate extraction cardinality')
    factory=ast.parse('def factory(process,incoming):\n latest=None\n all_events=[]\n').body[0]
    factory.body.extend(nodes)
    factory.body.extend(ast.parse('return reader,wait,all_events').body)
    module=ast.fix_missing_locations(ast.Module(body=[factory],type_ignores=[]))
    scope=dict(json=json,queue=queue,time=time)
    exec(compile(module,'candidate-v39-reader-wait','exec'),scope)
    return scope['factory']

if __name__=='__main__':
    import pathlib
    import hashlib
    root=pathlib.Path(__file__).parent
    original=(root/'source/v39-original.py.txt').read_bytes()
    result=repair(original)
    (root/'source/v39-candidate.py.txt').write_bytes(result)
    print(hashlib.sha256(result).hexdigest())
