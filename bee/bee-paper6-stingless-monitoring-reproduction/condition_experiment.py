#!/usr/bin/env python3
"""Controlled proxy experiment for paper camera-height/background variables.

Height is represented by central field-of-view crop; base colour is represented by
recolouring pixels outside annotated bee boxes. This is an explicit robustness proxy,
not a physical recreation of the unpublished stingless-bee farm experiment.
"""
from pathlib import Path
import argparse,json,re,subprocess,time
import cv2,numpy as np
ROOT=Path(__file__).resolve().parent
HEIGHTS={'10cm':.65,'20cm':.82,'30cm':1.0}
COLORS={'white':(235,235,235),'brown':(70,105,145),'dark_brown':(30,45,65)}

def labels(path,w,h):
    out=[]
    for line in path.read_text().splitlines():
        c,cx,cy,bw,bh=map(float,line.split()); out.append((int(c),(cx-bw/2)*w,(cy-bh/2)*h,bw*w,bh*h))
    return out
def transform(image,boxes,factor,color):
    h,w=image.shape[:2]; cw,ch=int(w*factor),int(h*factor); x0=(w-cw)//2; y0=(h-ch)//2; crop=image[y0:y0+ch,x0:x0+cw].copy(); kept=[]
    for c,x,y,bw,bh in boxes:
        ix1=max(x,x0); iy1=max(y,y0); ix2=min(x+bw,x0+cw); iy2=min(y+bh,y0+ch)
        if ix2<=ix1 or iy2<=iy1 or (ix2-ix1)*(iy2-iy1)/(bw*bh)<.5: continue
        kept.append((c,ix1-x0,iy1-y0,ix2-ix1,iy2-iy1))
    mask=np.zeros((ch,cw),np.uint8)
    for _,x,y,bw,bh in kept:
        pad=4; cv2.rectangle(mask,(max(0,int(x)-pad),max(0,int(y)-pad)),(min(cw-1,int(x+bw)+pad),min(ch-1,int(y+bh)+pad)),255,-1)
    solid=np.empty_like(crop); solid[:]=color; mixed=cv2.addWeighted(crop,.25,solid,.75,0); crop[mask==0]=mixed[mask==0]
    out=cv2.resize(crop,(w,h),interpolation=cv2.INTER_LINEAR); result=[]
    for c,x,y,bw,bh in kept: result.append((c,(x+bw/2)/cw,(y+bh/2)/ch,bw/cw,bh/ch))
    return out,result
def parse(log):
    def g(p):
        m=re.search(p,log,re.I); return float(m.group(1)) if m else None
    return {'map50':g(r'mAP@0\.50[^=]*=\s*([0-9.]+)'),'precision':g(r'precision\s*=\s*([0-9.]+)'),'recall':g(r'recall\s*=\s*([0-9.]+)'),'f1':g(r'F1-score\s*=\s*([0-9.]+)'),'tp':g(r'TP\s*=\s*([0-9.]+)'),'fp':g(r'FP\s*=\s*([0-9.]+)'),'fn':g(r'FN\s*=\s*([0-9.]+)')}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--weights',type=Path,default=ROOT/'runs/train/backup/yolov3-tiny-bee_final.weights'); p.add_argument('--samples',type=int,default=20); a=p.parse_args()
    source=sorted((ROOT/'data/bee22_darknet/images/test').rglob('*.jpg')); idx=np.linspace(0,len(source)-1,a.samples,dtype=int); selected=[source[i] for i in idx]; base=ROOT/'data/condition_images'; records=[]
    for hname,factor in HEIGHTS.items():
      for cname,color in COLORS.items():
        d=base/hname/cname; d.mkdir(parents=True,exist_ok=True); paths=[]; objects=0
        for n,src in enumerate(selected):
            im=cv2.imread(str(src)); b=labels(src.with_suffix('.txt'),im.shape[1],im.shape[0]); out,labs=transform(im,b,factor,color); dst=d/f'{n:03d}.jpg'; cv2.imwrite(str(dst),out,[cv2.IMWRITE_JPEG_QUALITY,92]); dst.with_suffix('.txt').write_text('\n'.join(f'{c} {x:.8f} {y:.8f} {w:.8f} {hh:.8f}' for c,x,y,w,hh in labs)+'\n'); paths.append(str(dst.resolve())); objects+=len(labs)
        lst=d/'test.txt'; lst.write_text('\n'.join(paths)+'\n'); data=d/'condition.data'; data.write_text(f"classes=1\nvalid={lst}\nnames={ROOT/'data/bee22_darknet/bee.names'}\n")
        cmd=[str(ROOT/'vendor/darknet/darknet'),'detector','map',str(data),str(ROOT/'configs/yolov3-tiny-bee.cfg'),str(a.weights),'-iou_thresh','0.5','-points','101']; start=time.perf_counter(); r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); log=r.stdout+'\n'+r.stderr
        (ROOT/'results'/f'condition_{hname}_{cname}.log').write_text(log)
        if r.returncode: raise SystemExit(log[-3000:])
        rec={'height_proxy':hname,'crop_factor':factor,'background':cname,'images':len(paths),'objects':objects,'elapsed_seconds':time.perf_counter()-start}|parse(log); records.append(rec); print(json.dumps(rec))
    (ROOT/'results/condition_metrics.json').write_text(json.dumps({'protocol':'synthetic field-of-view crop and background recolouring; not physical camera height','records':records},indent=2)+'\n')
if __name__=='__main__': main()

