import json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
freeze=json.loads((p/'FREEZE.json').read_text(encoding='utf-8'))
trace=json.loads((p/'reduced_trace.json').read_text(encoding='utf-8'))
prior=json.loads((p/'AUDIT.json').read_text(encoding='utf-8'))
checks={
 'source_event_stream_is_sha256_pinned':freeze['runtime_events']['sha256']=='f161c89895d9e228dd1c3e49351f56b42cc60ad3e10c6e0a092926989524790a' and freeze['runtime_events']['bytes']==457736,
 'reduced_observations_have_no_pixels_or_roi_samples':all(not any(k in o for k in ('image','pixels','roi','crop','frame_bytes')) for o in trace['observations']),
 'observations_contain_only_hash_hud_and_time_fields':all(set(o)=={'id','sequence','emit_ns','frame_rgb_sha256','health','ammo'} for o in trace['observations']),
 'A14_protocol_deviation_is_explicit':'protocol-deviation' in freeze['kind'],
 'prior_overlap_arithmetic_audit_passed':prior['status']=='PASS_POSTHOC_INTERVAL_ARITHMETIC',
 'this_package_has_no_source_run_image_files':not any(p.rglob('*.png')) and not any(p.rglob('*.bmp')),
}
result={'status':'PASS_ROI_NOT_IDENTIFIABLE_FROM_RETAINED_A14_ARTIFACTS' if all(checks.values()) else 'FAIL','checks':checks,'conclusion':'ROI pixel-change counts cannot be reconstructed for A14 from the retained full-frame SHA-256, typed HUD values, and timestamped interval analysis. ROI crops from another run are not interchangeable with A14 frames.'}
(p/'ROI_IDENTIFIABILITY_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
sys.exit(0 if all(checks.values()) else 1)

