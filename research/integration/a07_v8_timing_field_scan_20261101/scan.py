"""Read-only timing field scan of a fixed, published non-A07 trace family."""
import collections,json,subprocess
BASE='37f8ffeadba7d7522ec95ff74a5febc3a1f9ef9a'
PREFIX='research/doom/absolute_pair_59_4d74_20261004/'
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,PREFIX],text=True).splitlines()
paths=sorted(p for p in paths if p.endswith('/runtime/events.jsonl'))
totals=collections.Counter(); files=[]
for path in paths:
    data=subprocess.check_output(['git','show',BASE+':'+path])
    rows=[json.loads(line) for line in data.splitlines() if line.strip()]
    admissions=[r for r in rows if r.get('event')=='input_admission']
    releases=[r for r in rows if r.get('event')=='input_release_transition']
    key=lambda r:(r.get('id'),r.get('step'),r.get('key'),r.get('intent_token'))
    def valid(k):
        return (type(k[0]) is str and bool(k[0]) and type(k[1]) is int and
                type(k[2]) is str and bool(k[2]) and type(k[3]) is str and bool(k[3]))
    groups=collections.defaultdict(list)
    for row in admissions:
        ident=key(row)
        if valid(ident):groups[ident].append(row)
    counts=collections.Counter()
    release_counts=collections.Counter(key(r) for r in releases if valid(key(r)))
    for release in releases:
        ident=key(release)
        if not valid(ident):counts['identity_missing']+=1;continue
        candidates=groups[ident]
        if len(candidates)!=1 or release_counts[ident]!=1:counts['identity_not_unique_or_missing']+=1;continue
        a=candidates[0]
        times=(a.get('admitted_ns'),a.get('input_ack_ns'),release.get('release_call_started_ns'),release.get('release_call_returned_ns'))
        if not all(type(t) is int for t in times):counts['timing_missing_or_malformed']+=1
        elif times[0]<=times[1]<times[2]<=times[3]:counts['timing_consistent']+=1
        else:counts['timing_inconsistent']+=1
    totals.update(counts);files.append({'path':path,'admissions':len(admissions),'releases':len(releases),'counts':dict(counts)})
print(json.dumps({'base':BASE,'scope':'non-A07 historical runtime trace timing-field scan; not a v8 audit',
                  'files':files,'totals':dict(totals)},indent=2))
