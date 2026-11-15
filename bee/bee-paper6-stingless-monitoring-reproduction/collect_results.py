#!/usr/bin/env python3
from pathlib import Path
import csv,re
ROOT=Path(__file__).resolve().parent; text=(ROOT/'results/training_console.log').read_text(errors='ignore'); text=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',text)
pat=re.compile(r'\n\s*(\d+):\s+([0-9.eE+-]+),\s+([0-9.eE+-]+) avg loss,\s+([0-9.eE+-]+) rate,\s+([0-9.eE+-]+) seconds')
raw=[m.groups() for m in pat.finditer(text)]; latest={int(x[0]):x for x in raw}; rows=[latest[k] for k in sorted(latest)]
with (ROOT/'results/training_history.csv').open('w',newline='') as f: w=csv.writer(f); w.writerow(('iteration','loss','avg_loss','learning_rate','seconds')); w.writerows(rows)
print(len(rows),rows[-1] if rows else None)

