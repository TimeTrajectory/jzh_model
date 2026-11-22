#!/usr/bin/env python3
"""Generate the paper's TSG or TEM pseudo-RGB representations."""
from pathlib import Path
import argparse, json, os
import cv2

ROOT = Path(__file__).resolve().parent


def sequence(name): return Path(name).stem.rsplit("_", 1)[0]


def link_label(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists(): return
    try: os.link(source, target)
    except OSError: target.symlink_to(source.resolve())


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("encoding", choices=("tsg","tem")); parser.add_argument("--quality",type=int,default=82); args=parser.parse_args()
    source=ROOT/"data/rgb"; target=ROOT/f"data/{args.encoding}"
    for split in ("train","val"):
        images=sorted((source/split/"images").glob("*.jpg")); groups={}
        for image in images: groups.setdefault(sequence(image.name),[]).append(image)
        for name,frames in groups.items():
            for i,current_path in enumerate(frames):
                previous_path=frames[max(0,i-1)]; next_path=frames[min(len(frames)-1,i+1)]
                previous=cv2.imread(str(previous_path),cv2.IMREAD_GRAYSCALE); current=cv2.imread(str(current_path),cv2.IMREAD_GRAYSCALE); following=cv2.imread(str(next_path),cv2.IMREAD_GRAYSCALE)
                if args.encoding=="tsg": encoded=cv2.merge((previous,current,following))
                else: encoded=cv2.merge((cv2.absdiff(current,previous),current,cv2.absdiff(current,following)))
                out=target/split/"images"/current_path.name; out.parent.mkdir(parents=True,exist_ok=True); cv2.imwrite(str(out),encoded,[cv2.IMWRITE_JPEG_QUALITY,args.quality])
                link_label(source/split/"labels"/f"{current_path.stem}.txt",target/split/"labels"/f"{current_path.stem}.txt")
        print(args.encoding,split,len(images),flush=True)
    (ROOT/f"dataset_{args.encoding}.yaml").write_text(f"path: {target.resolve()}\ntrain: train/images\nval: val/images\nnames:\n  0: fanning_bee\n")
    (target/"encoding.json").write_text(json.dumps({"encoding":args.encoding,"channels":"B=I(n-1),G=I(n),R=I(n+1)" if args.encoding=="tsg" else "B=|I(n)-I(n-1)|,G=I(n),R=|I(n)-I(n+1)|"},indent=2)+"\n")


if __name__=="__main__": main()

