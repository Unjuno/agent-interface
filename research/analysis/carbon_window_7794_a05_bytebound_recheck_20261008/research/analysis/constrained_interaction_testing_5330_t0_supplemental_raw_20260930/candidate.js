(() => {
  const names = ["freshness","lease","handoff","owner","capability","protocol","backend","retry","concurrent","summary"];
  const n = names.length, size = 1 << n;
  const combos = (m,k) => {
    const out = [];
    const walk = (start, picked) => {
      if (picked.length === k) { out.push(picked.slice()); return; }
      for (let i=start; i<=m-(k-picked.length); i++) { picked.push(i); walk(i+1,picked); picked.pop(); }
    };
    walk(0,[]); return out;
  };
  const bit = (id,i) => (id >> (n-1-i)) & 1;
  const valid = id => !(bit(id,2) && !bit(id,3)) && !(bit(id,7) && !bit(id,6) && !bit(id,2));
  const faultNames = id => {
    const b = i => bit(id,i), f = [];
    if (b(0)&&b(1)) f.push("STALE_WITH_EXPIRED_LEASE");
    if (b(2)&&b(3)&&b(8)) f.push("LOST_HANDOFF_WITH_CONCURRENT_OWNER");
    if (b(4)&&b(5)) f.push("CAPABILITY_BYPASS_WITH_REORDERED_PROTOCOL");
    if (b(1)&&b(6)&&b(7)) f.push("EXPIRED_LEASE_DELAYED_DUPLICATE_RETRY");
    if (b(0)&&b(9)&&b(4)) f.push("STALE_COMPRESSED_EVIDENCE_WITH_BYPASS");
    return f;
  };
  const classify = input => {
    const id = input.id;
    if (!valid(id)) return {decision:"STOP_INVALID_CONFIGURATION", faults:[], effects:0};
    const faults = faultNames(id);
    return {decision:faults.length ? "STOP_HAZARD" : "SAFE_NO_EFFECT", faults, effects:0};
  };
  const all = Array.from({length:size},(_,i)=>i);
  const admissible = all.filter(valid);
  const pattern = (id,idxs) => idxs.map(i => i+":"+bit(id,i)).join(",");
  const cover = t => {
    const idxs = combos(n,t), remaining = new Set();
    for (const id of admissible) for (const c of idxs) remaining.add(pattern(id,c));
    const target = remaining.size, selected = [];
    while (remaining.size) {
      let best = -1, gain = -1;
      for (const id of admissible) {
        let score = 0;
        for (const c of idxs) { const key=pattern(id,c); if (remaining.has(key)) score++; }
        if (score > gain) { gain=score; best=id; }
      }
      if (best < 0 || gain <= 0) throw new Error("cover stalled");
      selected.push(best);
      for (const c of idxs) remaining.delete(pattern(best,c));
    }
    return {strength:t, rows:selected, target_patterns:target, covered_patterns:target};
  };
  const base = 0, one = [base];
  for (let i=0;i<n;i++) { const id=1<<(n-1-i); if (valid(id)) one.push(id); }
  const pair = cover(2), triple = cover(3);
  let state = 0x5330;
  const rand = () => { state ^= state<<13; state ^= state>>>17; state ^= state<<5; return state>>>0; };
  const shuffled = all.slice();
  for (let i=shuffled.length-1;i>0;i--) { const j=rand()%(i+1); [shuffled[i],shuffled[j]]=[shuffled[j],shuffled[i]]; }
  const chaos = shuffled.slice(0,triple.rows.length);
  const evaluate = (policy,ids) => {
    const rows = ids.map((id,seq) => ({seq,id,bits:id.toString(2).padStart(n,"0"),valid:valid(id),...classify({id})}));
    const discovered = [...new Set(rows.flatMap(r=>r.faults))].sort();
    return {policy,run_count:rows.length,invalid_count:rows.filter(r=>!r.valid).length,
      hazards_discovered:discovered,discovery_count:discovered.length,
      unsafe_effect_count:rows.reduce((s,r)=>s+r.effects,0),rows};
  };
  const policies = [
    evaluate("ONE_FAULT_AT_A_TIME",one),
    evaluate("CONSTRAINED_PAIRWISE",pair.rows),
    evaluate("CONSTRAINED_THREE_WAY",triple.rows),
    evaluate("UNCONSTRAINED_RANDOM_CHAOS_FIXED_SEED_21296",chaos)
  ];
  const metamorphicBases = pair.rows.slice(0,12);
  const transforms = ["OPAQUE_ID_RENAME","EVIDENCE_ORDER_REVERSAL","IRRELEVANT_METADATA_ADD"];
  const metamorphic = [];
  for (const id of metamorphicBases) for (const transform of transforms) {
    const baseline=classify({id,task_id:"opaque-a",evidence_order:[1,2,3],metadata:{}});
    const changed=classify(transform==="OPAQUE_ID_RENAME"
      ? {id,task_id:"renamed-z",evidence_order:[1,2,3],metadata:{}}
      : transform==="EVIDENCE_ORDER_REVERSAL"
        ? {id,task_id:"opaque-a",evidence_order:[3,2,1],metadata:{}}
        : {id,task_id:"opaque-a",evidence_order:[1,2,3],metadata:{unused:"x"}});
    metamorphic.push({id,transform,baseline:baseline.decision,changed:changed.decision,
      invariant:baseline.decision===changed.decision && JSON.stringify(baseline.faults)===JSON.stringify(changed.faults)});
  }
  const stages=[["ONE_FAULT_AT_A_TIME",one],["PAIRWISE_ESCALATION",pair.rows],["THREE_WAY_ESCALATION",triple.rows]];
  const adaptiveRows=[], seen=new Set(), shrinks=[];
  let seq=0;
  const minimize = id => {
    const active=[]; for(let i=0;i<n;i++) if(bit(id,i)) active.push(i);
    let best=id, trials=0; const probes=[];
    for(let mask=0;mask<(1<<active.length);mask++) {
      let candidate=0;
      for(let j=0;j<active.length;j++) if((mask>>j)&1) candidate|=1<<(n-1-active[j]);
      if(!valid(candidate)) continue;
      trials++;
      const faults=faultNames(candidate), decision=faults.length?"STOP_HAZARD":"SAFE_NO_EFFECT";
      probes.push({id:candidate,decision});
      const count=x=>x.toString(2).replace(/0/g,"").length;
      if(faults.length && (count(candidate)<count(best) ||
        (count(candidate)===count(best) && candidate<best))) best=candidate;
    }
    return {minimal_id:best,trials,probes};
  };
  for(const [stage,ids] of stages) for(const id of ids) {
    if(seen.has(id)) continue; seen.add(id);
    const out=classify({id});
    adaptiveRows.push({seq:seq++,stage,id,bits:id.toString(2).padStart(n,"0"),valid:valid(id),...out});
    if(out.decision==="STOP_HAZARD") shrinks.push({trigger_id:id,...minimize(id)});
  }
  const faultCounts={}; for(const id of admissible) for(const f of faultNames(id)) faultCounts[f]=(faultCounts[f]||0)+1;
  return {
    schema:"constrained-interaction-5330-t0-v1",
    freeze:{issue:5330,base_main:"1a27aff369ad1f690d4df6dc1664226ecc0726bb",factor_count:n,assignment_count:size,valid_assignment_count:admissible.length,seed:"0x5330"},
    factors:names.map((name,i)=>({name,levels:["BASE","FAULT_STRESS"],index:i})),
    constraints:["lost handoff requires active owner","duplicate retry requires delayed backend or lost handoff"],
    declared_fault_model:[
      {id:"STALE_WITH_EXPIRED_LEASE",requires:[0,1]},
      {id:"LOST_HANDOFF_WITH_CONCURRENT_OWNER",requires:[2,3,8]},
      {id:"CAPABILITY_BYPASS_WITH_REORDERED_PROTOCOL",requires:[4,5]},
      {id:"EXPIRED_LEASE_DELAYED_DUPLICATE_RETRY",requires:[1,6,7]},
      {id:"STALE_COMPRESSED_EVIDENCE_WITH_BYPASS",requires:[0,9,4]}
    ],
    feasible_fault_assignment_counts:faultCounts,
    pairwise_design:pair,triple_design:triple,
    policies,
    adaptive_strength_escalation:{policy:"ADAPTIVE_STRENGTH_ESCALATION_T0",run_count:adaptiveRows.length,
      invalid_count:adaptiveRows.filter(r=>!r.valid).length,
      discovered_faults:[...new Set(adaptiveRows.flatMap(r=>r.faults))].sort(),
      rows:adaptiveRows,shrink_probes:shrinks},
    metamorphic:{case_count:metamorphic.length,passed:metamorphic.filter(x=>x.invariant).length,failed:metamorphic.filter(x=>!x.invariant).length,cases:metamorphic},
    safety_envelope:{external_effects:0,simulated_effects:0,all_hazards_stop_before_effect:true,live_system_calls:0}
  };
})()