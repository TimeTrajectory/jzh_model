#!/usr/bin/env python3
"""Parse Darknet console output into a stable training-history CSV."""
from pathlib import Path
import csv,re
ROOT=Path(__file__).resolve().parent
text=(ROOT/'results/training_console.log').read_text(errors='ignore')
text=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',text)
pat=re.compile(r'\n\s*(\d+):\s+([0-9.eE+-]+),\s+([0-9.eE+-]+) avg loss,\s+([0-9.eE+-]+) rate,\s+([0-9.eE+-]+) seconds')
raw=[m.groups() for m in pat.finditer(text)]
# A resumed Darknet run can repeat iterations after the last periodic checkpoint.
# Keep the most recent record for each iteration so curves and counts stay monotonic.
by_iteration={int(row[0]):row for row in raw}
rows=[by_iteration[i] for i in sorted(by_iteration)]
out=ROOT/'results/training_history.csv'
with out.open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['iteration','loss','avg_loss','learning_rate','seconds']); w.writerows(rows)
print(out,len(rows),rows[-1] if rows else None,'raw_records',len(raw))
