#!/usr/bin/env python3
"""Minimal local Flask page for paper-style video monitoring."""
from pathlib import Path
import subprocess,uuid
from flask import Flask,request,send_from_directory,render_template_string

ROOT=Path(__file__).resolve().parent; UPLOAD=ROOT/'runs/web'; UPLOAD.mkdir(parents=True,exist_ok=True)
app=Flask(__name__)
HTML='''<!doctype html><meta charset="utf-8"><title>Paper 5 Bee Counter</title><style>body{max-width:850px;margin:40px auto;font:16px sans-serif;line-height:1.6}button{padding:9px 18px}code{background:#eee;padding:2px 5px}</style><h1>YOLOv4 + DeepSORT 蜜蜂通行监测</h1><p>上传固定机位入口视频。左右方向必须结合实际相机朝向解释为进巢或出巢。</p><form method=post enctype=multipart/form-data><input type=file name=video accept="video/*" required><button>分析视频</button></form>{% if result %}<h2>处理完成</h2><a href="{{result}}">下载跟踪视频</a>{% endif %}'''
@app.route('/',methods=['GET','POST'])
def index():
    result=None
    if request.method=='POST':
        f=request.files['video']; job=UPLOAD/uuid.uuid4().hex; job.mkdir(); source=job/Path(f.filename).name; f.save(source)
        subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'track_video.py'),str(source),'--output',str(job)],check=True)
        result=f'/files/{job.name}/tracked.mp4'
    return render_template_string(HTML,result=result)
@app.route('/files/<job>/<name>')
def files(job,name): return send_from_directory(UPLOAD/job,name,as_attachment=True)
if __name__=='__main__': app.run(host='0.0.0.0',port=5000,debug=False)
