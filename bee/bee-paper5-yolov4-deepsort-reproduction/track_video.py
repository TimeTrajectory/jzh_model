#!/usr/bin/env python3
"""YOLOv4 + DeepSORT video tracking and paper-style vertical line counting."""
from pathlib import Path
import argparse,csv,json,time,cv2,torch
from deep_sort_realtime.deepsort_tracker import DeepSort
from darknet_detector import DarknetDetector

ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser(); p.add_argument('source',type=Path); p.add_argument('--weights',type=Path,default=ROOT/'runs/train/backup/yolov4-bee_best.weights'); p.add_argument('--conf',type=float,default=.25); p.add_argument('--line-x',type=int); p.add_argument('--deadband',type=int,default=8); p.add_argument('--output',type=Path,default=ROOT/'runs/video_demo')
a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
cap=cv2.VideoCapture(str(a.source)); width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)); fps=cap.get(cv2.CAP_PROP_FPS) or 25.; line=a.line_x or width//2
writer=cv2.VideoWriter(str(a.output/'tracked.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),fps,(width,height)); csvfile=(a.output/'tracks.csv').open('w',newline=''); rows=csv.writer(csvfile); rows.writerow(['frame','track_id','x','y','w','h','score'])
det=DarknetDetector(a.weights,a.conf); tracker=DeepSort(max_age=30,n_init=3,max_cosine_distance=.2,embedder='mobilenet',embedder_gpu=torch.cuda.is_available(),half=torch.cuda.is_available())
state={}; left_to_right=right_to_left=frame_id=0; started=time.perf_counter()
while True:
    ok,frame=cap.read()
    if not ok: break
    frame_id+=1; detections=det.predict(frame); tracks=tracker.update_tracks([(b,c,'bee') for b,c in detections],frame=frame)
    for tr in tracks:
        if not tr.is_confirmed() or tr.time_since_update: continue
        box=tr.to_ltrb(orig=True,orig_strict=True)
        if box is None: continue
        x1,y1,x2,y2=map(float,box); ident=int(tr.track_id); cx=(x1+x2)/2; side=-1 if cx<line-a.deadband else (1 if cx>line+a.deadband else 0)
        if side:
            old=state.get(ident)
            if old and old!=side:
                if old<side: left_to_right+=1
                else: right_to_left+=1
            state[ident]=side
        rows.writerow([frame_id,ident,x1,y1,x2-x1,y2-y1,1.0]); color=((ident*37)%200+55,(ident*83)%200+55,(ident*129)%200+55)
        cv2.rectangle(frame,(int(x1),int(y1)),(int(x2),int(y2)),color,2); cv2.putText(frame,f'ID {ident}',(int(x1),max(15,int(y1)-3)),cv2.FONT_HERSHEY_SIMPLEX,.5,color,1)
    cv2.line(frame,(line,0),(line,height),(255,255,0),2); cv2.putText(frame,f'L->R {left_to_right}  R->L {right_to_left}',(15,30),cv2.FONT_HERSHEY_SIMPLEX,.8,(0,255,0),2); writer.write(frame)
elapsed=time.perf_counter()-started; cap.release(); writer.release(); csvfile.close(); det.close()
result={'frames':frame_id,'seconds':elapsed,'fps_end_to_end':frame_id/elapsed if elapsed else 0,'line_x':line,'left_to_right':left_to_right,'right_to_left':right_to_left,'note':'Map image directions to biological enter/leave only after confirming camera orientation.'}
(a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
