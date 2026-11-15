#!/usr/bin/env python3
"""Create sequence-disjoint Darknet data from BEE22 or an existing YOLO export."""
from pathlib import Path
import argparse,configparser,csv,hashlib,json,os
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT.parent/'bee-paper2-tracking-reproduction/data/yolo'

def make_yolo_from_archive(archive_path):
    raw=ROOT/'data/BEE22'; yolo=ROOT/'data/yolo'
    if not raw.exists():
        with ZipFile(archive_path) as archive:
            for entry in archive.infolist():
                path=Path(entry.filename)
                if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!='BEE22':
                    raise ValueError(f'unsafe archive member: {entry.filename}')
                if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError(f'symlink in archive: {entry.filename}')
            archive.extractall(ROOT/'data')
    split_map={'train':'train','val':'train','test':'test'}
    sequences={
        'train':[f'BEE22-{n:02d}' for n in list(range(1,12))+[14]],
        'val':['BEE22-15'],
        'test':['BEE22-12','BEE22-13','BEE22-16'],
    }
    for split,names in sequences.items():
        for name in names:
            seq=raw/split_map[split]/name
            image_dir=yolo/'images'/split/name; label_dir=yolo/'labels'/split/name
            image_dir.mkdir(parents=True,exist_ok=True); label_dir.mkdir(parents=True,exist_ok=True)
            if split!='test':
                for image in sorted((seq/'img1').glob('*.jpg')):
                    label=seq/'labels_with_ids'/f'{image.stem}.txt'; converted=[]
                    for row in label.read_text().splitlines():
                        cols=row.split()
                        if len(cols)!=6 or cols[0]!='0': raise ValueError(f'unexpected label: {label}: {row}')
                        converted.append('0 '+' '.join(f'{float(v):.8f}' for v in cols[2:]))
                    link(image,image_dir/image.name); (label_dir/f'{image.stem}.txt').write_text('\n'.join(converted)+'\n')
            else:
                info=configparser.ConfigParser(); info.read(seq/'seqinfo.ini')
                width=int(info['Sequence']['imWidth']); height=int(info['Sequence']['imHeight']); labels={}
                with (seq/'gt/gt.txt').open() as file:
                    for row in csv.reader(file):
                        frame=int(row[0]); x,y,w,h=map(float,row[2:6])
                        labels.setdefault(frame,[]).append(f'0 {(x+w/2)/width:.8f} {(y+h/2)/height:.8f} {w/width:.8f} {h/height:.8f}')
                for image in sorted((seq/'img1').glob('*.jpg')):
                    link(image,image_dir/image.name); (label_dir/f'{image.stem}.txt').write_text('\n'.join(labels.get(int(image.stem),[]))+'\n')
    return yolo

def link(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists() or dst.is_symlink(): return
    try: os.link(src.resolve(),dst)
    except OSError: dst.symlink_to(src.resolve())

def main():
    p=argparse.ArgumentParser(); p.add_argument('--source',type=Path); a=p.parse_args()
    source=(a.source or DEFAULT).resolve()
    if not source.exists():
        archive=ROOT/'downloads/BEE22.zip'
        if not archive.exists():
            raise SystemExit('BEE22 is missing. Run: .venv/bin/python download_bee22.py')
        source=make_yolo_from_archive(archive)
    out=ROOT/'data/bee22_darknet'; rows=[]; summary={'source':str(source),'substitute_for':'unpublished stingless-bee data','splits':{}}
    for split in ('train','val','test'):
        images=sorted((source/'images'/split).rglob('*.jpg')); boxes=0; seqs=set(); lines=[]
        for image in images:
            seq=image.parent.name; seqs.add(seq); label=source/'labels'/split/seq/(image.stem+'.txt')
            dst=out/'images'/split/seq/image.name; link(image,dst); link(label,dst.with_suffix('.txt'))
            n=sum(bool(x.strip()) for x in label.read_text().splitlines()); boxes+=n; lines.append(str(dst.resolve())); rows.append((split,seq,image.name,n))
        (out/f'{split}.txt').write_text('\n'.join(lines)+'\n'); summary['splits'][split]={'images':len(images),'boxes':boxes,'sequences':sorted(seqs)}
    (out/'bee.names').write_text('bee\n')
    common=f"classes = 1\ntrain = {out/'train.txt'}\nnames = {out/'bee.names'}\nbackup = {ROOT/'runs/train/backup'}\n"
    (out/'bee.data').write_text(common+f"valid = {out/'val.txt'}\n")
    (out/'bee_test.data').write_text(common+f"valid = {out/'test.txt'}\n")
    manifest=ROOT/'data/split_manifest.csv'
    with manifest.open('w',newline='') as f: w=csv.writer(f); w.writerow(('split','sequence','image','boxes')); w.writerows(rows)
    summary['manifest_sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest(); summary['policy']='complete BEE22 sequences are disjoint'
    (ROOT/'data/dataset_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(summary,indent=2,ensure_ascii=False))
if __name__=='__main__': main()

