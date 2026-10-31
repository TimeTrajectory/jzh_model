#!/usr/bin/env python3
"""Local Flask image demo for the trained bee and pollen models."""
from __future__ import annotations

import base64
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, render_template_string, request

from inference import Detector, draw_detections

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
MODELS: dict[str, Detector] = {}

HTML = """
<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>IntelliBeeHive 复现演示</title>
<style>body{max-width:960px;margin:32px auto;font:16px system-ui;color:#202124}section{padding:20px;border:1px solid #ddd;border-radius:12px}img{max-width:100%}button{padding:8px 18px}</style></head><body>
<h1>IntelliBeeHive 第四篇论文复现</h1><section><form method="post" enctype="multipart/form-data">
<p><input type="file" name="image" accept="image/*" required></p>
<p><select name="task"><option value="pollen">普通蜜蜂 / 携粉蜜蜂</option><option value="bee">仅蜜蜂</option></select>
置信度 <input name="confidence" type="number" min="0.01" max="0.99" step="0.01" value="0.25">
<button>执行检测</button></p></form></section>
{% if image %}<h2>结果</h2><p>{{ counts }}</p><img src="data:image/jpeg;base64,{{ image }}">{% endif %}
</body></html>
"""


def get_model(task: str) -> Detector:
    if task not in MODELS:
        path = ROOT / f"runs/train/{task}_yolov7_tiny_e100/weights/best.pt"
        if not path.exists():
            raise FileNotFoundError(f"请先训练模型：{path}")
        MODELS[task] = Detector(path)
    return MODELS[task]


@app.route("/", methods=["GET", "POST"])
def index():
    encoded = None
    counts = None
    if request.method == "POST":
        data = np.frombuffer(request.files["image"].read(), np.uint8)
        frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
        task = request.form.get("task", "pollen")
        confidence = float(request.form.get("confidence", "0.25"))
        detections = get_model(task).predict(frame, confidence)
        counts = dict(Counter(item["class_name"] for item in detections))
        ok, buffer = cv2.imencode(".jpg", draw_detections(frame, detections))
        if ok:
            encoded = base64.b64encode(buffer).decode("ascii")
    return render_template_string(HTML, image=encoded, counts=counts)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7860, debug=False)

