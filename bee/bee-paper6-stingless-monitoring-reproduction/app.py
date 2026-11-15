#!/usr/bin/env python3
"""Local web interface corresponding to the paper's camera/video layout."""
from pathlib import Path
import subprocess,uuid,json
from flask import Flask,request,render_template_string,send_from_directory
ROOT=Path(__file__).resolve().parent; UP=ROOT/'runs/uploads'; UP.mkdir(parents=True,exist_ok=True); app=Flask(__name__)
HTML='''<!doctype html><meta charset="utf-8"><title>Smart Stingless Beehive Reproduction</title><style>body{font:16px sans-serif;max-width:850px;margin:40px auto}pre{background:#eee;padding:12px}</style><h1>无刺蜂入口活动监测</h1><p>上传固定机位入口视频。系统检测蜜蜂、关联质心轨迹、统计图像中线越线事件，并按论文的每分钟 20 次阈值显示 ACTIVE/INACTIVE。</p><form method=post enctype=multipart/form-data><input type=file name=video accept="video/*" required><button>开始分析</button></form>{% if result %}<h2>结果</h2><pre>{{result}}</pre><a href="{{download}}">下载标注视频</a>{% endif %}'''
@app.route('/',methods=['GET','POST'])
def index():
 result=None; download=None
 if request.method=='POST':
  f=request.files['video']; job=uuid.uuid4().hex[:10]; src=UP/f'{job}_{Path(f.filename).name}'; out=UP/job; f.save(src)
  subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'monitor_video.py'),str(src),'--output',str(out)],cwd=ROOT,check=True)
  result=json.dumps(json.loads((out/'summary.json').read_text()),ensure_ascii=False,indent=2); download=f'/files/{job}/monitored.mp4'
 return render_template_string(HTML,result=result,download=download)
@app.route('/files/<job>/<name>')
def files(job,name): return send_from_directory(UP/job,name,as_attachment=True)
if __name__=='__main__': app.run(host='0.0.0.0',port=5000,debug=False)

