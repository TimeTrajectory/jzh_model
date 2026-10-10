# 第二篇论文：BEE22 蜜蜂检测与跟踪复现

本项目对应 Zheng 等发表于 *Smart Agricultural Technology* (2024) 的论文 [Intelligent beehive monitoring system based on internet of things and colony state analysis](https://doi.org/10.1016/j.atech.2024.100584)。项目复现论文中可由公开 BEE22 数据验证的视觉部分：YOLOv5 蜜蜂检测、DeepSORT 多目标跟踪，以及可配置蜂巢门区域的进出计数。

论文还包含温湿度、声音传感器、MySQL、天气分析和蜂群状态分析。这些部分依赖未随 BEE22 发布的硬件和传感器数据，因此本项目不生成对应实验结果。

## 目录和脚本

| 文件 | 作用 |
|---|---|
| `download_bee22.py` | 从论文给出的公开链接分段下载 BEE22，并校验文件大小、ZIP CRC 和 SHA256 |
| `download_assets.py` | 下载并校验 YOLOv5 v7.0 源码和 YOLOv5s 预训练权重 |
| `prepare_data.py` | 安全解压 BEE22，转换检测标签，并生成训练、验证清单 |
| `prepare_test_eval.py` | 从 MOT 真值生成只用于最终检测评估的测试标签 |
| `train_detector.py` | 按本轮复现参数启动 YOLOv5s 训练 |
| `evaluate_detector.py` | 在 BEE22-12、13、16 独立测试序列上评估检测器 |
| `evaluate_tracking.py` | 运行 YOLOv5s + DeepSORT，输出 MOT 文件、MOTA、MOTP/IoU 和 IDF1 |
| `render_tracks.py` | 把 MOT 跟踪结果绘制成带轨迹 ID 的视频 |
| `results/` | 已完成实验的小型指标记录，不含模型权重、数据集或本机路径 |

## 从零运行

推荐 Python 3.10。先根据本机环境安装 [PyTorch](https://pytorch.org/get-started/locally/)，训练建议使用 NVIDIA GPU。

```bash
bash setup.sh
source .venv/bin/activate

python download_bee22.py
python prepare_data.py
python prepare_test_eval.py

python train_detector.py
python evaluate_detector.py
python evaluate_tracking.py
python render_tracks.py --sequence BEE22-12
```

默认训练设置为 YOLOv5s v7.0、640×640、batch 32、Adam、初始学习率 0.001、seed 50、14 epoch。训练集为 BEE22 的 12 段序列、1,360 帧；BEE22-15 单独作为验证集、240 帧；原始 test 目录中的 BEE22-12、13、16 仅用于最终测试，共 762 帧。

训练输出位于 `runs/detector/yolov5s_seed50/`。如果显存不足，可用 `python train_detector.py --batch 8`；这会改变实验条件，应在报告中记录。`--device auto` 自动选择 CUDA 或 CPU。

## 蜂巢门区域计数

跟踪器支持使用像素坐标设置门区域：

```bash
python evaluate_tracking.py --roi 300 100 700 400
```

同一条已确认轨迹的中心由区域外进入时计一次 `enter`，由内离开时计一次 `exit`。不同序列的相机位置不同，应分别确定门区域。BEE22 没有提供独立的进出事件真值和统一门区域，因此本项目不报告计数 RMSE；未指定 `--roi` 时结果中的两个计数为 0，含义是未执行计数。

## 已完成结果与复现边界

本轮已完成的 seed 50 实验：独立测试集检测 mAP@0.5 为 0.950，YOLOv5s + DeepSORT 总体 MOTA 为 73.26%，匹配框平均 IoU 为 75.19%，IDF1 为 69.93%。完整分序列结果见 `REPORT.md` 和 `results/`。

论文未公开精确的 YOLOv5 模型尺寸、源码提交和所有实现细节。论文报告 10 个随机种子 50–59；当前只完成 seed 50。DeepSORT 使用 `deep-sort-realtime` 的预训练 MobileNet 外观编码器，没有重做论文所述的 600 次外观网络训练。因此这是可运行、可核验的近似复现基线，不是论文数值的逐位复制。

`.gitignore` 排除了数据集、下载包、第三方 YOLOv5 源码、模型权重、虚拟环境和训练输出。克隆后通过上述脚本重新生成，避免 GitHub 仓库过大。
