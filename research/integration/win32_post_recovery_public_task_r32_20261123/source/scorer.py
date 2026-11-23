"""Independent oracle for the R07 single-A delayed-effect fixture task."""
import json
from pathlib import Path

def score(events_path: Path, effect_path: Path):
    events = [json.loads(line) for line in events_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    effect = json.loads(effect_path.read_text(encoding='utf-8'))
    downs = [e for e in events if e.get('kind') == 'key_down_accepted' and e.get('code') == 65]
    ups = [e for e in events if e.get('kind') == 'key_up_received' and e.get('code') == 65]
    delayed = [e for e in events if e.get('kind') == 'delayed_effect' and e.get('verified') is True and e.get('text') == 'a']
    success = (len(downs) == 1 and len(ups) >= 1 and len(delayed) == 1
               and effect.get('verified') is True and effect.get('text') == 'a'
               and type(effect.get('key_down_accepted_ns')) is int
               and type(effect.get('effect_observed_ns')) is int
               and effect['effect_observed_ns'] >= effect['key_down_accepted_ns'])
    state = {'accepted_a_keydowns':len(downs),'received_a_keyups':len(ups),
             'delayed_a_effects':len(delayed),'effect_verified':effect.get('verified') is True,
             'text':effect.get('text'),'key_down_accepted_ns':effect.get('key_down_accepted_ns'),
             'effect_observed_ns':effect.get('effect_observed_ns')}
    return success, json.dumps(state,sort_keys=True,separators=(',',':')).encode('utf-8'), effect
