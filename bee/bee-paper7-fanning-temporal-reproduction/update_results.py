#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
def main():
 rows=[]
 for encoding in ("rgb","tsg","tem"):
  p=ROOT/"results"/f"metrics_yolo11n_{encoding}.json"
  if p.exists(): rows.append(json.loads(p.read_text()))
 if not rows: return
 lines=["### 本地受控实验结果","","| 输入 | Precision | Recall | mAP@0.50 | mAP@0.50:0.95 |", "|---|---:|---:|---:|---:|"]
 for x in rows: lines.append(f"| {x['encoding'].upper()} | {x['precision']:.4f} | {x['recall']:.4f} | {x['map50']:.4f} | {x['map50_95']:.4f} |")
 if len(rows)==3:
  best=max(rows,key=lambda x:x['map50']); rgb=next(x for x in rows if x['encoding']=='rgb'); lines += ["",f"最佳输入为 **{best['encoding'].upper()}**，mAP@0.50={best['map50']:.4f}；相对 RGB 变化 {best['map50']-rgb['map50']:+.4f}。"]
 block='\n'.join(lines)
 for name in ('README.md','REPORT.md'):
  p=ROOT/name
  if not p.exists(): continue
  text=p.read_text(); start='<!-- FINAL_RESULTS_START -->'; end='<!-- FINAL_RESULTS_END -->'
  if start in text: text=text[:text.index(start)+len(start)]+'\n'+block+'\n'+text[text.index(end):]
  else: text += f'\n\n{start}\n{block}\n{end}\n'
  p.write_text(text)
if __name__=='__main__':main()

