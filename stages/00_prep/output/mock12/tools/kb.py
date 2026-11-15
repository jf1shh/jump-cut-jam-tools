import time
from evdev import UInput, ecodes as e
MAP={"a":e.KEY_A,"d":e.KEY_D,"e":e.KEY_E,"w":e.KEY_W,"s":e.KEY_S,"r":e.KEY_R,"space":e.KEY_SPACE,"shift":e.KEY_LEFTSHIFT}
ui=UInput({e.EV_KEY:list(MAP.values())},name="mock-kbd")
time.sleep(1.0)  # let the compositor see the new device
def kd(k): ui.write(e.EV_KEY,MAP[k],1); ui.syn()
def ku(k): ui.write(e.EV_KEY,MAP[k],0); ui.syn()
def key(k,h=0.1): kd(k); time.sleep(h); ku(k)
