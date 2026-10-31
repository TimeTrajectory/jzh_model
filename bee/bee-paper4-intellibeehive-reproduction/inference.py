#!/usr/bin/env python3
"""Small reusable YOLOv7 inference adapter for image, video and web tools."""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent
YOLO = ROOT / "vendor/yolov7"
if str(YOLO) not in sys.path:
    sys.path.insert(0, str(YOLO))

from models.experimental import attempt_load  # noqa: E402
from utils.datasets import letterbox  # noqa: E402
from utils.general import non_max_suppression, scale_coords  # noqa: E402


class Detector:
    def __init__(self, weights: str | Path, device: str = "0", image_size: int = 416):
        self.device = torch.device(f"cuda:{device}" if device != "cpu" and torch.cuda.is_available() else "cpu")
        self.model = attempt_load(str(weights), map_location=self.device)
        self.model.eval()
        self.names = self.model.module.names if hasattr(self.model, "module") else self.model.names
        self.image_size = image_size

    @torch.inference_mode()
    def predict(self, frame: np.ndarray, confidence: float = 0.25, iou: float = 0.45) -> list[dict]:
        resized = letterbox(frame, self.image_size, stride=32)[0]
        tensor = resized[:, :, ::-1].transpose(2, 0, 1)
        tensor = np.ascontiguousarray(tensor)
        tensor = torch.from_numpy(tensor).to(self.device).float() / 255.0
        if tensor.ndimension() == 3:
            tensor = tensor.unsqueeze(0)
        predictions = non_max_suppression(self.model(tensor)[0], confidence, iou)[0]
        output = []
        if predictions is not None and len(predictions):
            predictions[:, :4] = scale_coords(tensor.shape[2:], predictions[:, :4], frame.shape).round()
            for x1, y1, x2, y2, score, class_id in predictions.tolist():
                class_id = int(class_id)
                output.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": score,
                    "class_id": class_id,
                    "class_name": self.names[class_id],
                })
        return output


def draw_detections(frame: np.ndarray, detections: list[dict]) -> np.ndarray:
    output = frame.copy()
    colors = [(52, 199, 89), (0, 149, 255), (64, 64, 255)]
    for detection in detections:
        x1, y1, x2, y2 = map(int, detection["bbox"])
        color = colors[detection["class_id"] % len(colors)]
        label = f"{detection['class_name']} {detection['confidence']:.2f}"
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
        cv2.putText(output, label, (x1, max(18, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    return output

