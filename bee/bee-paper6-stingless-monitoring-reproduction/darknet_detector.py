"""Python wrapper for the pinned Darknet YOLOv3-tiny detector."""
from pathlib import Path
import sys,cv2,numpy as np
ROOT=Path(__file__).resolve().parent; sys.path.insert(0,str(ROOT/'vendor/darknet'))
import darknet  # type: ignore
class DarknetDetector:
    def __init__(self,weights:Path,conf=.25,nms=.45):
        self.conf,self.nms=conf,nms
        self.net,self.names,_=darknet.load_network(str(ROOT/'configs/yolov3-tiny-bee.cfg'),str(ROOT/'data/bee22_darknet/bee.data'),str(weights),batch_size=1)
        self.w,self.h=darknet.network_width(self.net),darknet.network_height(self.net); self.image=darknet.make_image(self.w,self.h,3)
    def predict(self,frame:np.ndarray):
        oh,ow=frame.shape[:2]; rgb=cv2.cvtColor(cv2.resize(frame,(self.w,self.h)),cv2.COLOR_BGR2RGB); darknet.copy_image_from_bytes(self.image,rgb.tobytes())
        detections=darknet.detect_image(self.net,self.names,self.image,self.conf,nms=self.nms); out=[]; sx,sy=ow/self.w,oh/self.h
        for _,confidence,(cx,cy,w,h) in detections:
            x=max(0.,(cx-w/2)*sx); y=max(0.,(cy-h/2)*sy); out.append(([x,y,min(ow-x,w*sx),min(oh-y,h*sy)],float(confidence)/100))
        return out
    def close(self): darknet.free_image(self.image)

