"""Two-command driver for a pinned synthetic exit calibration; no model calls."""
from map01_door_driver_protocol import DoorDriverProtocol

class SyntheticExitDriverProtocol(DoorDriverProtocol):
    PWAD='bd634d97942e6c88f5474d58f4181245d0f7475c9c2ec4595952f3657c5681f3'
    IWAD='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'

    def __init__(self,arm):
        super().__init__('use',self.PWAD,self.IWAD,self.PWAD,870,
                         traverse=True,exit_probe=True,exit_arm=arm,direct_exit=True)

    def receive(self,row,now):
        if type(row) is dict and row.get('event')=='ready':
            proof=row.get('synthetic_exit_calibration')
            if (self.ready or type(now) is not int or type(proof) is not dict
                    or proof!={'pwad_sha256':self.PWAD,'iwad_sha256':self.IWAD,
                               'arm':self.exit_arm,'scope':'synthetic calibration only'}
                    or row.get('post_load_clock_gate',{}).get('passed') is not True):
                raise ValueError('synthetic ready binding differs')
            self.ready=True
            return None
        return super().receive(row,now)
