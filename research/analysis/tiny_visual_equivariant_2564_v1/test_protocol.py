from __future__ import annotations

import numpy as np
from prepare import (CONSTRUCTION_SEED, EVAL_CENTERS, FORMAL_SEEDS, SUPPORT_CENTERS,
                     construction_summary, evaluation_data, training_data)
from models import cnn_fit, cnn_predict, mlp_fit, mlp_predict


def test_protocol():
    summary=construction_summary()
    assert summary["train_rows_per_arm"] == 160
    assert len(summary["heldout"]) == 8
    assert all(v["centers_disjoint_from_support"] for v in summary["heldout"].values())
    for seed in FORMAL_SEEDS:
        a,ay,_=training_data(seed+1,"control")
        b,by,_=training_data(seed+1,"treatment")
        assert np.array_equal(ay,by) and np.array_equal(a[1::2],b[1::2])
        assert np.isfinite(a).all() and np.isfinite(b).all()
    x,y,_=training_data(CONSTRUCTION_SEED+1,"treatment")
    cm=cnn_fit(x,y.astype(np.float32),CONSTRUCTION_SEED+5)
    mm=mlp_fit(x.reshape(160,-1),y.astype(np.float32),CONSTRUCTION_SEED+5)
    assert cnn_predict(cm,x).shape == mlp_predict(mm,x.reshape(160,-1)).shape == (160,)
    assert np.isfinite(cnn_predict(cm,x)).all()
    # CNN has 4 shared 3x3 filters, biases, pooled dense vector and output bias.
    assert sum(p.size for p in cm) == 45
    assert sum(p.size for p in mm) == 1200*16+16+16+1
    assert len(SUPPORT_CENTERS)==5 and len(EVAL_CENTERS)==8
    return True


if __name__ == "__main__":
    print("protocol checks passed" if test_protocol() else "failed")

