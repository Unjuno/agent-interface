"""Lossless local model-view artifact preparation, separate from wire transport."""
from pathlib import Path
from time import perf_counter_ns
from PIL import Image


class ImageArtifactSink:
    def __init__(self, directory, *, compress_level=6, reuse=True):
        if type(compress_level) is not int or not 0 <= compress_level <= 9:
            raise ValueError("PNG compression level must be an integer from 0 to 9")
        self.directory=Path(directory)
        self.directory.mkdir(parents=True,exist_ok=True)
        self.compress_level,self.reuse=compress_level,reuse
        self.previous,self.path,self.sequence=None,None,0

    def publish(self,frame):
        start=perf_counter_ns()
        self.sequence+=1
        reused=(self.reuse and frame==self.previous and self.path is not None
                and self.path.is_file())
        if not reused:
            path=self.directory/f"{self.sequence:03d}.png"
            # Never silently overwrite evidence from another session.
            with path.open("xb") as out:
                Image.frombytes(frame.mode,(frame.width,frame.height),frame.pixels).save(
                    out,format="PNG",compress_level=self.compress_level)
            self.previous,self.path=frame,path
        ready=perf_counter_ns()
        return dict(image=str(self.path.resolve()),image_reused=reused,
                    image_prepare_ns=ready-start,image_ready_ns=ready)
