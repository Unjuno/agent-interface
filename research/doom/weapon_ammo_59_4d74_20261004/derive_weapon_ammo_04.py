from pathlib import Path
root=Path(__file__).resolve().parent
prep=(root/'prepare_sample_pair_03.py').read_text().replace('sample-pair-source-03','sample-pair-source-04').replace('sample_pair_entry_03','sample_pair_entry_04').replace('SAMPLE_PAIR_SOURCE_03','SAMPLE_PAIR_SOURCE_04')
(root/'prepare_sample_pair_04.py').write_text(prep)
probe=(root/'probe_sample_pair_03.py').read_text().replace('sample_pair_entry_03','sample_pair_entry_04').replace("'40126'","'40127'")
(root/'probe_sample_pair_04.py').write_text(probe)
driver=(root/'run_sample_pair_03.py').read_text().replace('sample-pair-03','sample-pair-04').replace('sample-pair-source-03','sample-pair-source-04').replace('sample_pair_03','sample_pair_04').replace('sample_pair_entry_03','sample_pair_entry_04').replace('SAMPLE_PAIR_SOURCE_03','SAMPLE_PAIR_SOURCE_04').replace('progresssample03','weaponammo04').replace('progress-sample-construction-03','weapon-ammo-construction-04')
driver=driver.replace('same-thread scorer-only game variables can measure changing damage/progress separately from input occupancy','scorer-only selected-weapon ammo and inventory variables can be reconciled to captured HUD values').replace('HEALTH AMMO1 POSITION_X Y Z KILLCOUNT DEATHCOUNT','HEALTH SELECTED_WEAPON SELECTED_WEAPON_AMMO AMMO0-AMMO9 POSITION_X Y Z KILLCOUNT DEATHCOUNT')
(root/'run_sample_pair_04.py').write_text(driver)
