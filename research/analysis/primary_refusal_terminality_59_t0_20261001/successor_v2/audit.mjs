import fs from 'node:fs';
const rows=fs.readFileSync(process.argv[2],'utf8').trim().split('\n').filter(Boolean).map(JSON.parse);
const expected={explicit_refusal:'unexpected MCP refusal',malformed_envelope:'transport, presentation, or response validation failure',valid_input:null,transport_throw:'transport, presentation, or response validation failure'};
const errors=[], seen=new Set();
for(const row of rows){
  if(seen.has(row.case_id)) errors.push('duplicate '+row.case_id);
  seen.add(row.case_id);
  if(!(row.case_id in expected)) {errors.push('unknown case '+row.case_id);continue;}
  if(row.stopped!==expected[row.case_id]) errors.push(row.case_id+': wrong stop state');
  if(row.close!=='allowed') errors.push(row.case_id+': close blocked');
  if(row.case_id==='valid_input') {
    if(row.first.status!=='returned'||row.next.status!=='returned'||row.calls.length!==3) errors.push('valid input control failed');
  } else {
    if(row.next.status!=='blocked') errors.push(row.case_id+': post-fault input not blocked');
    if(row.calls.length!==2||row.calls[1].tool!=='interface_close') errors.push(row.case_id+': post-fault effectful call reached host');
  }
  if(row.case_id==='explicit_refusal' && !row.original_refusal_image_preserved) errors.push('refusal image not preserved');
}
if(seen.size!==Object.keys(expected).length||Object.keys(expected).some(k=>!seen.has(k))) errors.push('case inventory mismatch');
process.stdout.write(JSON.stringify({audit:errors.length?'FAIL':'PASS',rows:rows.length,errors})+'\n');
process.exitCode=errors.length?1:0;
