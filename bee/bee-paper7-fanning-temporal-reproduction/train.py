#!/usr/bin/env python3
"""Train one controlled RGB/TSG/TEM YOLO comparison arm."""
from pathlib import Path
import argparse, json, platform, subprocess, time
import torch, ultralytics, yaml
from ultralytics import YOLO
from temporal_loader import install

ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(); p.add_argument("encoding",choices=("rgb","tsg","tem")); p.add_argument("--model",default=str(ROOT/"weights/yolo11n.pt")); p.add_argument("--epochs",type=int,default=50); p.add_argument("--batch",type=int,default=32); p.add_argument("--workers",type=int,default=8); p.add_argument("--device",default="0"); p.add_argument("--patience",type=int,default=15); p.add_argument("--fraction",type=float,default=1.0); p.add_argument("--name"); a=p.parse_args()
    run=a.name or f"{Path(a.model).stem}_{a.encoding}"; start=time.time(); install(a.encoding); model=YOLO(a.model)
    dataset=yaml.safe_load((ROOT/f"dataset_{a.encoding}.yaml").read_text()); dataset["path"]=str(ROOT/f"data/{a.encoding}")
    model.train(data=dataset,epochs=a.epochs,imgsz=1024,rect=True,batch=a.batch,optimizer="AdamW",lr0=0.001,momentum=0.9,weight_decay=0.0005,translate=0.1,scale=0.5,fliplr=0.5,hsv_h=0.0,hsv_s=0.0,hsv_v=0.2,close_mosaic=10,patience=a.patience,save_period=10,seed=42,deterministic=True,workers=a.workers,device=a.device,fraction=a.fraction,project=str(ROOT/"runs/train"),name=run,exist_ok=False,plots=True)
    meta={"encoding":a.encoding,"model":a.model,"epochs_max":a.epochs,"batch":a.batch,"patience":a.patience,"workers":a.workers,"imgsz":1024,"rect":True,"seed":42,"elapsed_seconds":time.time()-start,"python":platform.python_version(),"torch":torch.__version__,"cuda":torch.version.cuda,"ultralytics":ultralytics.__version__,"gpu":torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}
    meta["fraction"]=a.fraction; out=ROOT/"results"; out.mkdir(exist_ok=True); (out/f"train_{run}.json").write_text(json.dumps(meta,indent=2)+"\n")

if __name__=="__main__": main()

