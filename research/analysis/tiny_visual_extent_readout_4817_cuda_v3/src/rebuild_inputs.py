import hashlib,json,sys
from pathlib import Path
import numpy as np
from run_cuda import DATA_SEED,dataset
out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False)
train,base,held=dataset(DATA_SEED)
packed={'train_x':train[0],'train_y':train[1],'base_x':base[0],'base_y':base[1]}
for index,key in enumerate(sorted(held)): packed[f'held_{index}_x'],packed[f'held_{index}_y']=held[key]
target=out/'INPUTS.npz'; np.savez_compressed(target,**packed)
print(json.dumps({'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'numpy':np.__version__,'seed':DATA_SEED,'keys':list(packed)},sort_keys=True))

