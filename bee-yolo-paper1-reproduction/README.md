# 第一篇论文：蜜蜂视觉检测（YOLOv5m）复现

本项目对应 Alex 等的论文 [*Enhancing pollinator conservation: Monitoring of bees through object recognition*](https://doi.org/10.1016/j.compag.2024.109665)（*Computers and Electronics in Agriculture*, 2024）。核心流程是单类蜜蜂图像检测，以及将检测器用于视频抽帧、可见数量记录和网页演示。`track_video.py` 和 YOLO26m 是后续扩展，**不属于原论文的核心结果**。

这是从已保存的实验源码重新整理的独立学习项目。`reference_results/` 存放旧实验的指标和数据审计记录，供核对；它们不是重新运行后产生的新结果。仓库不包含大型数据集、模型权重、虚拟环境或论文 PDF，首次使用时按下文下载公开资源。

## 源码导览

| 文件 | 作用 |
|---|---|
| `download_assets.py` | 下载公开数据、作者权重、预训练权重、YOLOv5 v7.0 源码及示例视频，并核对 SHA256 |
| `extract_source.py` | 安全解压固定版本的 YOLOv5 源码到 `vendor/yolov5/` |
| `prepare_dataset.py` | 核验 COCO 标注和图像，转换为单类 YOLO 标签，保留原 train/valid/test 划分 |
| `run_experiments.py` | 训练 YOLOv5m；记录命令、种子、权重哈希和日志，支持断点续训 |
| `evaluate.py` | 在 test 划分评估作者权重或本地权重，输出 P、R、mAP 和速度 |
| `error_analysis.py` | 用固定置信度和 IoU 门槛查看小目标召回、误检和漏检 |
| `video_report.py` | 视频抽帧检测，输出时间戳、逐帧可见数量、逐秒出现标志和标注视频 |
| `app.py` | 本地 Flask 视频上传演示和结果下载 |
| `track_video.py` | 可选的 YOLO26m + ByteTrack 扩展示例 |

## 在本地运行

推荐 Python 3.10，并先按 [PyTorch 官方安装说明](https://pytorch.org/get-started/locally/) 安装适合本机的 CPU 或 CUDA 版本。训练 100 epoch 推荐 NVIDIA GPU；CPU 可以用来阅读源码和做小规模调试。

```bash
bash setup.sh
source .venv/bin/activate
python download_assets.py dataset author yolov5_pretrained yolov5 author_example_video
python extract_source.py
python prepare_dataset.py
python evaluate.py --model yolov5m --tag author --weights weights/author_custom_yolov5m.pt
python run_experiments.py --model yolov5m --batch 16 --epochs 100 --imgsz 416 --seed 42
python evaluate.py --model yolov5m --tag retrained --weights runs/yolov5m_416/weights/best.pt
python video_report.py --video downloads/author_example_video.mp4 --output runs/video_demo
python app.py
```

网页演示默认位于 `http://127.0.0.1:5000`。训练时设备默认自动选择，可显式指定 `--device cpu` 或 `--device 0`。YOLOv5m 的训练配置为 416 像素、100 epoch、batch 16、seed 42；若显存不足，调低 `--batch` 并记录改变。训练日志及最佳权重保存在 `runs/yolov5m_416/`。若训练意外中断且存在 `weights/last.pt`，执行 `python run_experiments.py --model yolov5m --resume`。

`prepare_dataset.py` 会生成包含当前机器绝对路径的 `dataset.yaml`，因此换电脑后要重新运行它。下载脚本将逐个核对公开文件的 SHA256；如果上游发布内容变化，会明确报错，避免把不同数据版本混成同一轮实验。

## 公开资源和复现口径

- [公开数据集 Bee Detection in the Wild](https://www.kaggle.com/datasets/birdy654/bee-detection-in-the-wild)：当前归档记录为 9,631 张图像、13,374 个蜜蜂框，原论文报告为 9,664 张、13,402 个框。下载哈希和分割清单见 `download_assets.py`、`reference_results/dataset_audit.json`。
- [作者原项目与权重](https://github.com/AjayJohnAlex/Bee_Detection)：可先用作者权重做本地测试，再运行本项目的 YOLOv5m 训练。
- [YOLOv5 v7.0](https://github.com/ultralytics/yolov5/tree/v7.0)：本项目固定的公开实现选择；原论文没有明确给出源码提交。

`REPORT.md` 说明论文数字、旧实验实测数字和它们的差异。由于数据版本与 YOLOv5 源码版本不能确认完全一致，本项目提供可审查、可重复执行的实验流程，不能承诺逐位得到论文数值。视频结果表示采样帧中**画面可见**的蜜蜂数量，不是蜂群总个体数或进出巢次数。

## 仓库体积与生成文件

`.gitignore` 排除了 `dataset/`、`downloads/`、`weights/`、`vendor/`、`runs/` 和 `.venv/`。克隆后按上述命令重新下载、生成和训练。此设计使源码仓库保持轻量，便于逐文件学习。
