#!/usr/bin/env python3
"""Write machine-readable final metrics into README.md and REPORT.md."""
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parent

def load(name):
    p=ROOT/'results'/name
    return json.loads(p.read_text()) if p.exists() else {}

def replace(path,start,end,body):
    text=path.read_text()
    if start not in text or end not in text:
        raise RuntimeError(f'missing result markers in {path}')
    before,tail=text.split(start,1)
    _,after=tail.split(end,1)
    path.write_text(before+start+'\n'+body.rstrip()+'\n'+end+after)

def fmt(x,n=4):
    return '未生成' if x is None else f'{float(x):.{n}f}'

def event_total(report):
    sums={k:0 for k in ('tp','fp','fn','gt_events','pred_events')}
    for seq in report.get('sequences',{}).values():
        m=seq.get('event_metrics',{})
        for k in sums: sums[k]+=int(m.get(k,0))
    tp,fp,fn=sums['tp'],sums['fp'],sums['fn']
    p=tp/(tp+fp) if tp+fp else 0
    r=tp/(tp+fn) if tp+fn else 0
    f=2*p*r/(p+r) if p+r else 0
    return sums|{'precision':p,'recall':r,'f1':f}

def main():
    det=load('detector_metrics.json'); selected=load('best_checkpoint_val.json'); track=load('tracking_metrics.json')
    mot=track.get('motmetrics',{}).get('OVERALL',{}); ev=event_total(track)
    rows=[]
    hist=ROOT/'results/training_history.csv'
    if hist.exists(): rows=list(csv.DictReader(hist.open()))
    train_line=(f"训练日志共解析 {len(rows):,} 次更新，最后平均损失为 {float(rows[-1]['avg_loss']):.4f}。" if rows else '训练日志尚未生成。')
    if det:
        body=f"""### 正式检测与完整系统结果

验证集在 `yolov4-bee_5000.weights` 与 `yolov4-bee_final.weights` 之间选择，最终采用 `{Path(selected.get('weight','')).name}`；测试集没有参与选权重。{train_line}

| 层级 | 指标 | 结果 |
|---|---|---:|
| 检测 | Precision | {fmt(det.get('precision'))} |
| 检测 | Recall | {fmt(det.get('recall'))} |
| 检测 | F1 | {fmt(det.get('f1'))} |
| 检测 | mAP@0.50 | {fmt(det.get('map50'))} |
| 完整 MOT | MOTA | {fmt(mot.get('mota'))} |
| 完整 MOT | IDF1 | {fmt(mot.get('idf1'))} |
| 完整 MOT | ID switches | {int(mot.get('num_switches',0))} |
| 完整 MOT | Misses / FP | {int(mot.get('num_misses',0))} / {int(mot.get('num_false_positives',0))} |
| 越线事件 | Precision / Recall / F1 | {fmt(ev['precision'])} / {fmt(ev['recall'])} / {fmt(ev['f1'])} |
| 端到端 | FPS | {fmt(track.get('fps_end_to_end'),2)} |

这些数值来自 BEE22 开放入口测试序列，不能与论文受控单向通道的 99.5% 直接等同。"""
    else:
        body='### 正式检测与完整系统结果\n\n6000 次正式训练正在进行；完成后由 `finalize_experiment.py` 自动写入本节。'
    for name in ('README.md','REPORT.md'):
        replace(ROOT/name,'<!-- FINAL_RESULTS_START -->','<!-- FINAL_RESULTS_END -->',body)

if __name__=='__main__': main()
