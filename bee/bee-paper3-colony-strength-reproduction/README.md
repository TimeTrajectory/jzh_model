# 第三篇论文复现：三类别蜜蜂检测

对应论文：P. Chaudhary 等，*Estimating colony strength and pollination efficiency in honey bees using a novel dataset and deep learning-based models*，Smart Agricultural Technology 14 (2026) 102005。

## 复现范围

本项目首先复现论文表现最好的实时模型 YOLOv10X，用同一公开数据完成三类检测：

1. `WB no pollen`：无花粉工蜂；
2. `WB pollen`：带花粉工蜂；
3. `Drone bee`：雄蜂。

论文还比较 Faster R-CNN、RetinaNet、FCOS 和 SSD。YOLOv10X 基线完成后，可在同一固定数据划分上增加这些模型，避免不同划分造成不公平比较。

## 论文口径

- 数据集：4,590 帧、79,212 个标注、15 段视频。
- 划分：训练 60%、验证 20%、测试 20%。
- YOLOv10X：1080×1080，batch 4，SGD，初始学习率 0.01，early stopping patience 10。
- 作者报告：accuracy 93.9%、F1 0.92、25.93 FPS。

`evaluate.py` 同时保存整体与逐类别 Precision、Recall、F1、AP50、mAP50-95，以及当前硬件上的纯推理 FPS。论文将目标检测中的 TN 纳入 accuracy，但没有公开其背景 TN 的计算方式，因此本项目不会用 mAP 代替论文 accuracy。

论文没有公开逐帧划分清单和随机种子。本项目固定 seed 50，并保存 `dataset_manifest.json`，使本次划分可以审计和重复。

## 使用

```bash
./setup.sh
.venv/bin/python inspect_archive.py
.venv/bin/python prepare_dataset.py
.venv/bin/python train_yolov10.py
.venv/bin/python evaluate.py
```

继续训练：

```bash
.venv/bin/python train_yolov10.py --resume
```

图片或视频推理：

```bash
.venv/bin/python predict.py path/to/image_or_video
```

## 数据来源

官方数据页面：https://scholarsjunction.msstate.edu/gri-publications/4/

数据 DOI：https://doi.org/10.54718/JCHW9401

官方附件较大，不提交到 GitHub。`downloads/`、`data/`、训练权重和运行输出由 `.gitignore` 排除。

更详细的论文参数与复现限制见 `PAPER_NOTES.md`。

