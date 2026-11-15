#!/usr/bin/env python3
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parent
def load(name):
 p=ROOT/'results'/name; return json.loads(p.read_text()) if p.exists() else {}
def replace(path,body):
 s='<!-- FINAL_RESULTS_START -->'; e='<!-- FINAL_RESULTS_END -->'; text=path.read_text(); a,tail=text.split(s,1); _,b=tail.split(e,1); path.write_text(a+s+'\n'+body.rstrip()+'\n'+e+b)
def main():
 val=load('detector_val_metrics.json'); test=load('detector_test_metrics.json'); cond=load('condition_metrics.json'); rows=list(csv.DictReader((ROOT/'results/training_history.csv').open())) if (ROOT/'results/training_history.csv').exists() else []
 if not test: body='正式训练与测试正在进行，完成后自动写入。'
 else:
  records=cond.get('records',[]); best=max(records,key=lambda x:x.get('map50') or -1) if records else {}
  body=f'''### 正式训练与检测结果

训练完成 {len(rows):,} 次迭代，最终平均损失 {float(rows[-1]['avg_loss']):.4f}。验证集 mAP@0.50 为 {val.get('map50',0):.4f}；独立测试集结果如下。

| Precision | Recall | F1 | mAP@0.50 |
|---:|---:|---:|---:|
| {test.get('precision',0):.4f} | {test.get('recall',0):.4f} | {test.get('f1',0):.4f} | {test.get('map50',0):.4f} |

### 3×3 采集条件代理实验

每个组合固定抽取 20 张测试帧。最佳代理组合为 `{best.get('height_proxy','待生成')} + {best.get('background','待生成')}`，mAP@0.50={best.get('map50',0):.4f}。这里的高度是中央视场裁切因子，背景是框外像素重着色；结果只用于敏感性分析。'''
 for name in ('README.md','REPORT.md'): replace(ROOT/name,body)
if __name__=='__main__': main()

