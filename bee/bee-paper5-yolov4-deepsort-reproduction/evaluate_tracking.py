#!/usr/bin/env python3
"""YOLOv4+DeepSORT MOT and vertical midline event-count evaluation on BEE22."""
from __future__ import annotations
import argparse,csv,json,time
from collections import defaultdict
from pathlib import Path
import cv2, motmetrics as mm, numpy as np, torch
from deep_sort_realtime.deepsort_tracker import DeepSort
from darknet_detector import DarknetDetector

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'bee-paper2-tracking-reproduction'/'data'/'BEE22'/'test'

def read_gt(path):
    frames=defaultdict(list)
    with path.open() as f:
        for r in csv.reader(f): frames[int(r[0])].append((int(r[1]),list(map(float,r[2:6]))))
    return frames

def crossing_events(frame_centers, line_x, deadband=8):
    events=[]; state={}
    for frame in sorted(frame_centers):
        for ident,(x,_) in frame_centers[frame].items():
            side=-1 if x<line_x-deadband else (1 if x>line_x+deadband else 0)
            if not side: continue
            old=state.get(ident)
            if old and old!=side: events.append((frame,'right_to_left' if old==1 else 'left_to_right'))
            state[ident]=side
    return events

def event_scores(gt,pred,tolerance=5):
    used=set(); tp=0
    for pf,pd in pred:
        choices=[(abs(pf-gf),i) for i,(gf,gd) in enumerate(gt) if i not in used and gd==pd and abs(pf-gf)<=tolerance]
        if choices: _,i=min(choices); used.add(i); tp+=1
    fp=len(pred)-tp; fn=len(gt)-tp
    p=tp/(tp+fp) if tp+fp else 0.; r=tp/(tp+fn) if tp+fn else 0.; f=2*p*r/(p+r) if p+r else 0.
    return {'tp':tp,'fp':fp,'fn':fn,'precision':p,'recall':r,'f1':f,'gt_events':len(gt),'pred_events':len(pred)}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--weights',type=Path,default=ROOT/'runs/train/backup/yolov4-bee_best.weights'); p.add_argument('--sequences',nargs='*',default=['BEE22-12','BEE22-13','BEE22-16']); p.add_argument('--conf',type=float,default=.25); p.add_argument('--oracle-gt',action='store_true',help='Use GT boxes as detections to isolate DeepSORT association'); a=p.parse_args()
    detector=None if a.oracle_gt else DarknetDetector(a.weights,a.conf); out=ROOT/'runs'/('tracking_oracle' if a.oracle_gt else 'tracking'); out.mkdir(parents=True,exist_ok=True)
    accs=[]; names=[]; detail={}; total_frames=0; total_time=0
    for name in a.sequences:
        seq=SOURCE/name; gt=read_gt(seq/'gt/gt.txt'); acc=mm.MOTAccumulator(auto_id=True)
        tracker=DeepSort(max_age=30,n_init=3,max_cosine_distance=.2,embedder='mobilenet',embedder_gpu=torch.cuda.is_available(),half=torch.cuda.is_available())
        gt_centers=defaultdict(dict); pred_centers=defaultdict(dict); mot=[]; start=time.perf_counter()
        images=sorted((seq/'img1').glob('*.jpg'))
        for path in images:
            fid=int(path.stem); frame=cv2.imread(str(path)); detections=[(b,1.0) for _,b in gt.get(fid,[])] if a.oracle_gt else detector.predict(frame)
            tracks=tracker.update_tracks([(b,c,'bee') for b,c in detections],frame=frame); active={}
            for tr in tracks:
                if not tr.is_confirmed() or tr.time_since_update: continue
                box=tr.to_ltrb(orig=True,orig_strict=True)
                if box is None: continue
                x1,y1,x2,y2=map(float,box); ident=int(tr.track_id); b=[x1,y1,x2-x1,y2-y1]
                active[ident]=b; pred_centers[fid][ident]=(x1+b[2]/2,y1+b[3]/2); mot.append([fid,ident,*b,1,-1,-1,-1])
            truth=gt.get(fid,[])
            for ident,b in truth: gt_centers[fid][ident]=(b[0]+b[2]/2,b[1]+b[3]/2)
            ids,boxes=zip(*truth) if truth else ([],[])
            acc.update(list(ids),list(active),mm.distances.iou_matrix(boxes,list(active.values()),max_iou=.5))
        elapsed=time.perf_counter()-start; total_time+=elapsed; total_frames+=len(images)
        with (out/f'{name}.txt').open('w',newline='') as f: csv.writer(f).writerows(mot)
        line_x=cv2.imread(str(images[0])).shape[1]/2
        detail[name]={'frames':len(images),'seconds':elapsed,'event_metrics':event_scores(crossing_events(gt_centers,line_x),crossing_events(pred_centers,line_x))}
        accs.append(acc); names.append(name)
    metrics=['mota','motp','idf1','precision','recall','num_objects','num_switches','num_misses','num_false_positives']
    summary=mm.metrics.create().compute_many(accs,names=names,metrics=metrics,generate_overall=True)
    motmetrics={}
    for name,row in summary.iterrows():
        motmetrics[name]={k:(None if np.isnan(float(v)) else float(v)) for k,v in row.items()}; motmetrics[name]['mean_matched_iou']=1-motmetrics[name]['motp']
    report={'mode':'oracle_ground_truth_detections' if a.oracle_gt else 'yolov4_deepsort','weights':None if a.oracle_gt else str(a.weights),'fps_end_to_end':total_frames/total_time,'sequences':detail,'motmetrics':motmetrics,'count_protocol':'vertical image midline, 8 px deadband, event frame tolerance ±5; directions are image coordinates, not biological in/out.'}
    result_name='tracking_oracle_metrics.json' if a.oracle_gt else 'tracking_metrics.json'
    (ROOT/'results'/result_name).write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
    if detector: detector.close()
if __name__=='__main__': main()
