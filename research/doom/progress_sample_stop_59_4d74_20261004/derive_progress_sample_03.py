from pathlib import Path
root=Path(__file__).resolve().parent
prep=(root/'prepare_sample_pair_02.py').read_text().replace('sample-pair-source-02','sample-pair-source-03').replace('sample_pair_entry_02','sample_pair_entry_03').replace('SAMPLE_PAIR_SOURCE_02','SAMPLE_PAIR_SOURCE_03')
(root/'prepare_sample_pair_03.py').write_text(prep)
probe=(root/'probe_sample_pair_02.py').read_text().replace('sample_pair_entry_02','sample_pair_entry_03').replace("['coast','pulse','pulse','coast','coast','pulse']","['coast']").replace("'40125'","'40126'").replace('600_000_000','5_000_000_000').replace("'duration_ms':600","'duration_ms':5000").replace('through +600ms','through +5000ms')
(root/'probe_sample_pair_03.py').write_text(probe)
driver=(root/'run_sample_pair_02.py').read_text().replace('sample-pair-02','sample-pair-03').replace('sample-pair-source-02','sample-pair-source-03').replace('sample_pair_02','sample_pair_03').replace('sample_pair_entry_02','sample_pair_entry_03').replace('SAMPLE_PAIR_SOURCE_02','SAMPLE_PAIR_SOURCE_03').replace('samplepair02','progresssample03').replace('absolute-pair-construction-02','progress-sample-construction-03')
driver=driver[:driver.index("freeze=")]+'''freeze={'argv':argv,'files':files,'source_git':json.loads((root/'SAMPLE_PAIR_SOURCE_03.json').read_text())['commit'],'model_calls':0,'allocation':'progress-sample-construction-03','H':'Same-thread scorer-only game variables can measure changing damage/progress separately from input occupancy','T':'one no-input5000ms coast from fixturev2,seed40126; clock+5s lease; HEALTH AMMO1 POSITION_X Y Z KILLCOUNT DEATHCOUNT with coherent tic bracket; normalfinish','D':'finite coherent samples in window; initial API health/ammo agrees with observed initial HUD if both available; mismatch or missing/unsupported fields FAIL, absent damage/progress exposure HOLD; no useful-efficacy PASS','C':'sampled API state not exact onset; observer timing/fixture setup affect exposure; no model or causal comparison','U':'CPU private networknone WSLc,no provider/GPU/input; first outcome retained, no retry'}
(out/'FREEZE.json').write_text(json.dumps(freeze,indent=2))
start=time.monotonic();r=subprocess.run(argv,capture_output=True,timeout=120)
(out/'stdout.txt').write_bytes(r.stdout);(out/'stderr.txt').write_bytes(r.stderr);(out/'HOST.json').write_text(json.dumps({'exit_code':r.returncode,'elapsed_s':time.monotonic()-start}));print(r.returncode);print(r.stdout.decode());print(r.stderr.decode())
'''
(root/'run_sample_pair_03.py').write_text(driver)
