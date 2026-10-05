const f=require("./fixture.json");
const rows=[];
for (const m of f.moderators) for (const a of [0,1]) { const p1=f.treatment_propensity[m]; const prob=a===1?p1:1-p1; rows.push({m,a,prob,p1,y:f.potential_outcomes[m][String(a)]}); }
function hte(rows,m) { const n=rows.filter(r=>r.m===m).length; const treated=rows.filter(r=>r.m===m&&r.a===1).reduce((s,r)=>s+r.prob*r.y/r.p1,0)/n; const control=rows.filter(r=>r.m===m&&r.a===0).reduce((s,r)=>s+r.prob*r.y/(1-r.p1),0)/n; return treated-control; }
const effects=Object.fromEntries(f.moderators.map(m=>[m,hte(rows,m)]));
const pooled=(effects.M0+effects.M1)/2;
console.log(JSON.stringify({allocation:f.allocation,rows,effects,pooled,heterogeneity:effects.M0-effects.M1}));
