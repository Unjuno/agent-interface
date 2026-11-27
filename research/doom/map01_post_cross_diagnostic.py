"""Finite passive observations after a rejected MAP01 visual gate."""
import hashlib
import os

def collect(directory, *, capture, neutral, clock, wait):
    frames=[]
    for index in range(3):
        wait(0.1)
        if neutral() is not True:
            raise ValueError("input is not neutral before diagnostic capture")
        started=clock()
        image=capture().convert("RGB")
        captured=clock()
        if type(started) is not int or type(captured) is not int or captured < started:
            raise ValueError("invalid diagnostic clock")
        if neutral() is not True:
            raise ValueError("input is not neutral after diagnostic capture")
        name=f"post-cross-{index}.png"
        with (directory/name).open("xb") as stream:
            image.save(stream,format="PNG",compress_level=1)
            stream.flush()
            os.fsync(stream.fileno())
        frames.append({"file":name,"started_ns":started,"capture_ns":captured,
                       "rgb_sha256":hashlib.sha256(image.tobytes()).hexdigest(),
                       "size":list(image.size),"neutral":True})
    return {"schema":"map01-post-cross-diagnostic-v1","authority":"none",
            "scope":"passive screen samples; not control source or task proof","frames":frames}
