#!/usr/bin/env python3
"""Video detector, lightweight centroid association, crossing count and activity alert."""
from pathlib import Path
import argparse,csv,json,time,cv2,numpy as np
from darknet_detector import DarknetDetector
ROOT=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser(); p.add_argument('video',type=Path); p.add_argument('--weights',type=Path,default=ROOT/'runs/train/backup/yolov3-tiny-bee_final.weights'); p.add_argument('--output',type=Path,default=ROOT/'runs/videos/demo'); p.add_argument('--threshold',type=int,default=20); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
 cap=cv2.VideoCapture(str(a.video)); fps=cap.get(cv2.CAP_PROP_FPS) or 25; w=int(cap.get(3)); h=int(cap.get(4)); line=w//2; writer=cv2.VideoWriter(str(a.output/'monitored.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),fps,(w,h)); detector=DarknetDetector(a.weights); tracks={}; next_id=1; events=[]; rows=[]; frame_id=0; start=time.perf_counter()
 while True:
  ok,frame=cap.read()
  if not ok: break
  frame_id+=1; detections=detector.predict(frame); centers=[(b[0]+b[2]/2,b[1]+b[3]/2,b,c) for b,c in detections]; unused=set(range(len(centers)))
  for ident,state in list(tracks.items()):
   candidates=[(np.hypot(centers[i][0]-state['x'],centers[i][1]-state['y']),i) for i in unused]
   if not candidates or min(candidates)[0]>80: state['age']+=1; continue
   _,i=min(candidates); unused.remove(i); x,y,b,conf=centers[i]; old=state['side']; side=-1 if x<line-8 else (1 if x>line+8 else old)
   if old and side!=old: events.append({'frame':frame_id,'track_id':ident,'direction':'left_to_right' if side==1 else 'right_to_left'})
   state.update(x=x,y=y,side=side,age=0,box=b,conf=conf)
  for i in unused:
   x,y,b,conf=centers[i]; tracks[next_id]={'x':x,'y':y,'side':-1 if x<line else 1,'age':0,'box':b,'conf':conf}; next_id+=1
  tracks={k:v for k,v in tracks.items() if v['age']<=12}
  cv2.line(frame,(line,0),(line,h),(255,180,0),2)
  for ident,s in tracks.items():
   x,y,bw,bh=map(int,s['box']); cv2.rectangle(frame,(x,y),(x+bw,y+bh),(0,255,0),2); cv2.putText(frame,f'ID {ident}',(x,max(15,y-4)),0,.45,(0,255,0),1); rows.append((frame_id,ident,x,y,bw,bh,s['conf']))
  writer.write(frame)
 cap.release(); writer.release(); detector.close(); minutes=max(frame_id/fps/60,1/60); count=len(events); summary={'frames':frame_id,'fps_input':fps,'crossing_events':count,'events_per_minute':count/minutes,'activity_threshold_per_minute':a.threshold,'status':'ACTIVE' if count/minutes>=a.threshold else 'INACTIVE','processing_fps':frame_id/(time.perf_counter()-start),'direction_is_image_coordinate_only':True}
 with (a.output/'tracks.csv').open('w',newline='') as f: cw=csv.writer(f); cw.writerow(('frame','track_id','x','y','w','h','confidence')); cw.writerows(rows)
 (a.output/'events.json').write_text(json.dumps(events,indent=2)); (a.output/'summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
if __name__=='__main__': main()

