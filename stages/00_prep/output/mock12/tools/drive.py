import subprocess,time,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kb
WID=sys.argv[1]; OUT=sys.argv[2]
def x(*a): subprocess.run(["xdotool",*a],check=False)
KD=kb.kd; KU=kb.ku
K=kb.key
W=time.sleep
x("windowactivate","--sync",WID); x("mousemove","2500","600","click","1"); W(1)
t0=time.time()
def stamp(l): print(f"{time.time()-t0:6.1f}s {l}",flush=True)
K("r",0.2); W(2.5); stamp("start"); W(1.0)
KD("d"); W(1.5); K("space"); W(.75); stamp("air"); W(.7); KD("shift"); W(.5); W(.5); KU("shift"); W(1.0)
KD("e"); KD("w"); W(1.0); W(1.5); W(1.5); W(1.5); KU("w"); KU("e")
stamp("climbed")
for i in range(4): K("space"); W(.6); W(.9)
KD("shift"); W(2.0); W(2.0); KU("shift"); W(3.0); stamp("exit"); W(3.0); KU("d"); stamp("win-hold"); W(2)
K("r",0.2); W(3); stamp("restarted")
KD("shift"); W(6); stamp("squash"); W(6); stamp("lose-hold"); W(2.5); KU("shift"); W(0.5)
K("r",0.2); W(2); stamp("done")
