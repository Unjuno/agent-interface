const f=require("./fixture.json");
const A=f.segmentations.A,B=f.segmentations.B;
function occupancy(rows,stratum){const xs=rows.filter(x=>x.phase==="train"&&x.stratum===stratum),counts={};for(const x of xs)counts[x.mode]=(counts[x.mode]||0)+1;const vals=Object.values(counts);return {units:xs.length,mode_counts:counts,singletons:vals.filter(n=>n===1).length,doubletons:vals.filter(n=>n===2).length};}
function newRate(rows){const train=new Set(rows.filter(x=>x.phase==="train").map(x=>x.mode));const held=rows.filter(x=>x.phase==="heldout");return {units:held.length,new_units:held.filter(x=>!train.has(x.mode)).length,rate:held.filter(x=>!train.has(x.mode)).length/held.length};}
function exactSpanF1(a,b,trace){const aa=a.filter(x=>x.trace===trace),bb=b.filter(x=>x.trace===trace),key=x=>x.start+":"+x.end;const aset=new Set(aa.map(key)),bset=new Set(bb.map(key));let matches=0;for(const k of aset)if(bset.has(k))matches++;return aa.length+bb.length===0?1:2*matches/(aa.length+bb.length);}
function spansF1(a,b){const aa=a.map(x=>x.trace+":"+x.start+":"+x.end),bb=b.map(x=>x.trace+":"+x.start+":"+x.end),bs=new Set(bb);let m=0;for(const k of new Set(aa))if(bs.has(k))m++;return 2*m/(aa.length+bb.length);}
const strata=["S1","S2"],occ={A:Object.fromEntries(strata.map(s=>[s,occupancy(A,s)])),B:Object.fromEntries(strata.map(s=>[s,occupancy(B,s)]))};
const heldout={A:newRate(A),B:newRate(B)};
const perTrace=Object.fromEntries(f.traces.map(t=>[t.id,exactSpanF1(A,B,t.id)]));
const category={agreements:f.aligned_category_pairs.filter(x=>x.a===x.b).length,total:f.aligned_category_pairs.length,rate:f.aligned_category_pairs.filter(x=>x.a===x.b).length/f.aligned_category_pairs.length};
const occupancyChanged=strata.some(s=>occ.A[s].singletons!==occ.B[s].singletons||occ.A[s].doubletons!==occ.B[s].doubletons);
const unstable=occupancyChanged||Math.abs(heldout.A.rate-heldout.B.rate)>f.thresholds.heldout_new_rate_delta_flag;
const saturation=Object.fromEntries(["A","B"].map(k=>[k,(strata.reduce((n,s)=>n+occ[k][s].singletons,0)/strata.reduce((n,s)=>n+occ[k][s].units,0)<=f.thresholds.saturation_singleton_fraction)&&(heldout[k].rate<=f.thresholds.saturation_new_mode_rate)]));
console.log(JSON.stringify({allocation:f.allocation,annotationsA:A,annotationsB:B,occupancy:occ,heldout,unitizing:{exact_span_match_f1:spansF1(A,B),per_trace:perTrace},category_agreement:category,occupancy_changed:occupancyChanged,sensitivity_gate:unstable,control_flag:perTrace.control<f.thresholds.max_unitizing_f1_for_control_flag,saturation}));
