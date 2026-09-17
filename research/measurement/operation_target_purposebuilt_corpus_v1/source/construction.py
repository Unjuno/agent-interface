import json
from generator import generate,corpus_digest
from validator import validate
rows=generate(113320260918000,units=2)
errors,stats=validate(rows,expected_rows=16,expected_units=2)
assert not errors,(errors,stats)
assert stats['positives']==8 and stats['semantic_negatives']==8
assert stats['no_local_action']==2 and stats['yield']==6
assert stats['target_alternative_rows']==4
print(json.dumps({'pass':True,'stats':stats,'digest':corpus_digest(rows)},sort_keys=True))
