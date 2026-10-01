"""Fixture-specific pixel conditions, not generic warning recognition."""
import numpy as np


def detect(frame):
    pixels=np.frombuffer(frame.pixels,dtype=np.uint8).reshape(frame.height,frame.width,3)
    red=(pixels[:,:,0]>220)&(pixels[:,:,1]<60)&(pixels[:,:,2]<60)
    green=(pixels[:,:,1]>220)&(pixels[:,:,0]<60)&(pixels[:,:,2]<60)
    yellow=(pixels[:,:,0]>220)&(pixels[:,:,1]>220)&(pixels[:,:,2]<60)
    if yellow.sum()>=100:return 'yellow_alert'
    if red.sum()<100:return 'target_lost'
    if green.sum()<100:return 'player_lost'
    return None
