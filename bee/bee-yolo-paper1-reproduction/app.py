"""Minimal local Flask interface for the P01 video upload and count report."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

from flask import Flask, abort, render_template_string, request, send_from_directory, url_for

ROOT = Path(__file__).resolve().parent
UPLOADS = ROOT / 'runs/web_uploads'
REPORTS = ROOT / 'runs/web_reports'
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024
PAGE = '''<!doctype html><html lang="zh"><meta charset="utf-8"><title>蜜蜂视频监测</title>
<style>body{font:16px system-ui,sans-serif;max-width:780px;margin:4rem auto;padding:0 1rem;color:#243221}h1{font-size:2rem}form{background:#f5f8ef;padding:1.5rem;border-radius:12px}button{background:#395f27;color:white;border:0;padding:.7rem 1.2rem;border-radius:6px;cursor:pointer}li{margin:.5rem 0}video{max-width:100%}</style>
<h1>蜜蜂视频监测</h1><p>上传视频后，系统约每半秒分析一帧，记录时间戳和画面中可见的蜜蜂数量。数量不代表不同个体数或进出巢次数。</p>
<form method="post" enctype="multipart/form-data"><label>选择视频 <input type="file" name="video" accept=".mp4,.mov,.avi" required></label> <button>生成报告</button></form>
{% if error %}<p role="alert">{{ error }}</p>{% endif %}
{% if job %}<h2>分析结果</h2><ul><li><a href="{{ url_for('download', job=job, filename='counts.csv') }}">逐帧数量 CSV</a></li><li><a href="{{ url_for('download', job=job, filename='detections.csv') }}">检测框 CSV</a></li><li><a href="{{ url_for('download', job=job, filename='presence_by_second.csv') }}">逐秒出现事件 CSV</a></li><li><a href="{{ url_for('download', job=job, filename='report.json') }}">处理参数 JSON</a></li></ul>
<video controls src="{{ url_for('download', job=job, filename='annotated.mp4') }}"></video>{% endif %}</html>'''


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template_string(PAGE, error=None, job=None)
    upload = request.files.get('video')
    if not upload or Path(upload.filename or '').suffix.lower() not in {'.mp4', '.mov', '.avi'}:
        return render_template_string(PAGE, error='请选择 MP4、MOV 或 AVI 视频。', job=None), 400
    job = uuid4().hex
    upload_dir = UPLOADS / job
    upload_dir.mkdir(parents=True)
    video = upload_dir / ('input' + Path(upload.filename).suffix.lower())
    upload.save(video)
    command = [sys.executable, str(ROOT / 'video_report.py'), '--video', str(video),
               '--weights', str(ROOT / 'weights/author_custom_yolov5m.pt'),
               '--output', str(REPORTS / job)]
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = str(Path(sys.base_prefix) / 'lib') + ':' + env.get('LD_LIBRARY_PATH', '')
    try:
        with (upload_dir / 'process.log').open('w') as log:
            completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, timeout=1800)
        if completed.returncode:
            raise RuntimeError('分析失败；请检查视频编码或模型文件。')
    except (subprocess.TimeoutExpired, RuntimeError) as error:
        return render_template_string(PAGE, error=str(error), job=None), 500
    return render_template_string(PAGE, error=None, job=job)


@app.route('/reports/<job>/<filename>')
def download(job: str, filename: str):
    if not re.fullmatch(r'[0-9a-f]{32}', job) or filename not in {'counts.csv', 'detections.csv', 'presence_by_second.csv', 'report.json', 'annotated.mp4'}:
        abort(404)
    return send_from_directory(REPORTS / job, filename)


if __name__ == '__main__':
    app.run(host=os.environ.get('BEE_HOST', '127.0.0.1'), port=int(os.environ.get('BEE_PORT', '5000')))
