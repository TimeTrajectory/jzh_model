# 第三篇论文复现：蜂群强度与授粉效率三类别检测

本项目复现论文中表现最好的实时检测方案 YOLOv10X，用蜂箱入口视频帧识别三类蜜蜂，并给出固定划分、训练、断点续训、独立测试、图片/视频推理和 PDF 报告生成的完整流程。

> 对应论文：P. Chaudhary 等，*Estimating colony strength and pollination efficiency in honey bees using a novel dataset and deep learning-based models*，Smart Agricultural Technology 14 (2026) 102005。DOI：10.1016/j.atech.2026.102005。

## 1. 复现目标与范围

检测类别如下：

| ID | 类别 | 含义 |
|---:|---|---|
| 0 | `WB no pollen` | 未携带花粉的工蜂 |
| 1 | `WB pollen` | 携带花粉的工蜂 |
| 2 | `Drone bee` | 雄蜂 |

论文还比较了 Faster R-CNN、RetinaNet、FCOS 和 SSD。本仓库当前完成论文最优实时模型 YOLOv10X 的端到端复现。所有代码都围绕同一份固定数据划分运行，便于以后加入其余四种模型进行公平比较。

## 2. 已完成内容

- 审计官方 4.2 GB 补充数据压缩包并记录 SHA-256；
- 排除 ZIP 中 macOS `__MACOSX` 重复资源；
- 修复两份 `imagePath` 错误的 LabelMe 标注；
- 将 LabelMe 矩形框转换为 YOLO 格式；
- 按 seed 50 固定生成 60%/20%/20% 的训练、验证、测试划分；
- 使用 COCO 预训练 YOLOv10X 训练，并支持意外关机后的精确断点续训；
- 在从未参与训练的测试集上输出整体、逐类别和速度指标；
- 支持图片、目录和视频推理；
- 自动生成中文 PDF 复现结果报告。

## 3. 数据与审计结果

官方数据页面：<https://scholarsjunction.msstate.edu/gri-publications/4/>

数据 DOI：<https://doi.org/10.54718/JCHW9401>

把下载得到的官方文件放到：

```text
downloads/supplement.zip
```

压缩包不提交到 GitHub。当前实验使用文件：

| 项目 | 数值 |
|---|---:|
| 压缩包大小 | 4,236,622,867 字节 |
| SHA-256 | `cae66fc3d855ef1d26f570afe574cbfe23763c5da845b100625d0d490fd6c891` |
| 有效图片/标注对 | 4,590 |
| 边界框总数 | 79,212 |
| `WB no pollen` | 73,981 |
| `WB pollen` | 4,272 |
| `Drone bee` | 559 |

上述图片数、总框数和各类别计数与论文 Table 2 完全一致。类别极不平衡，其中雄蜂只占约 0.7%，因此逐类别指标比单一总体指标更有解释力。

本轮确定性划分如下：

| 划分 | 图片 | WB no pollen | WB pollen | Drone bee | 总框数 |
|---|---:|---:|---:|---:|---:|
| 训练 | 2,754 | 44,450 | 2,463 | 339 | 47,252 |
| 验证 | 918 | 14,459 | 887 | 102 | 15,448 |
| 测试 | 918 | 15,072 | 922 | 118 | 16,112 |
| 合计 | 4,590 | 73,981 | 4,272 | 559 | 79,212 |

论文公开了 60/20/20 比例，没有公开逐帧清单和随机种子。本项目固定 seed 50，并把每个样本的来源、输出文件名和所属集合写入 `dataset_manifest.json`。因此本实验可以重复，但不能声称与作者的逐帧划分完全相同。

## 4. 环境要求

本次运行环境：

- Ubuntu/Linux；
- Python 3.10；
- NVIDIA GeForce RTX 4090 24 GB；
- CUDA 可用的 PyTorch；
- Ultralytics 8.4.163。

建议至少准备 25 GB 可用磁盘。数据压缩包、解压文件、YOLO 数据目录、模型权重和运行日志都由 `.gitignore` 排除。

创建环境：

```bash
cd bee/bee-paper3-colony-strength-reproduction
chmod +x setup.sh
./setup.sh
```

检查 GPU：

```bash
.venv/bin/python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

如果机器没有 NVIDIA GPU，可以把训练和评估命令中的 `--device 0` 改为 `--device cpu`，但 YOLOv10X 在 CPU 上训练会非常慢。

## 5. 从零复现

### 5.1 审计压缩包

```bash
.venv/bin/python inspect_archive.py
```

脚本不会直接信任压缩包路径，会拒绝绝对路径、目录穿越和符号链接条目。结果写入 `archive_manifest.json`。

### 5.2 转换并固定数据划分

```bash
.venv/bin/python prepare_dataset.py
```

重新生成已有数据目录时使用：

```bash
.venv/bin/python prepare_dataset.py --force
```

输出：

```text
data/yolo/images/{train,val,test}/
data/yolo/labels/{train,val,test}/
dataset.yaml
dataset_manifest.json
```

图片使用指向解压原图的符号链接，避免额外复制数 GB 数据；标签是标准 YOLO 文本格式。

### 5.3 训练 YOLOv10X

```bash
.venv/bin/python train_yolov10.py
```

论文和本项目的核心设置：

| 参数 | 值 |
|---|---|
| 模型 | YOLOv10X，COCO 预训练 |
| 参数量 | 31,660,658（论文为 31.6M） |
| 请求输入尺寸 | 1080 × 1080 |
| 实际张量尺寸 | 1088 × 1088，按最大步长 32 自动补齐 |
| batch | 4 |
| 优化器 | SGD |
| 初始学习率 | 0.01 |
| early stopping patience | 10 |
| 随机种子 | 50 |
| 最大轮数 | 100 |
| 论文实际轮数 | 45 |

训练输出位于：

```text
runs/detector/yolov10x_seed50/
```

其中 `weights/best.pt` 是验证集 mAP@0.5:0.95 最好的权重，`weights/last.pt` 是最近一个完整 epoch 的权重，`results.csv` 保存每轮损失和验证指标。

### 5.4 关机或中断后继续训练

```bash
.venv/bin/python train_yolov10.py --resume
```

`--resume` 会加载 `runs/detector/yolov10x_seed50/weights/last.pt`，同时恢复 epoch、优化器、学习率调度器和 early stopping 状态。必须使用这个参数；直接把 `last.pt` 当作普通模型重新调用训练会重新开始 epoch 计数。

查看最新完整轮次：

```bash
tail -n 2 runs/detector/yolov10x_seed50/results.csv
```

### 5.5 在固定测试集上评估

```bash
.venv/bin/python evaluate.py
```

输出：

- `results/detector_metrics.json`：整体与逐类别指标、速度、权重 SHA-256；
- `runs/evaluation/test/`：混淆矩阵、PR/F1/P/R 曲线和预测可视化；
- 终端：同一份 JSON 指标摘要。

主要指标含义：

- Precision：预测为该类的检测中有多少是正确的；
- Recall：真实目标中有多少被检出；
- F1：Precision 与 Recall 的调和平均；
- AP50：IoU=0.5 时的平均精度；
- mAP@0.5:0.95：IoU 从 0.5 到 0.95 的 COCO 标准平均值；
- inference FPS：只根据 Ultralytics 报告的单图模型推理耗时换算，不含读取、绘图和写文件。

### 5.6 图片或视频推理

```bash
.venv/bin/python predict.py path/to/image.jpg
.venv/bin/python predict.py path/to/video.mp4 --conf 0.25
```

标注后的媒体保存在 `runs/predict/demo/`，终端输出各类别检测数量。视频中的数量是逐帧检测框累计值，不等同于经多目标跟踪去重后的个体数。

### 5.7 生成 PDF 结果报告

完成测试后运行：

```bash
.venv/bin/python generate_report.py
```

报告输出：

```text
reports/第三篇论文复现结果报告.pdf
```

### 5.8 生成 VS Code Word 操作手册

```bash
.venv/bin/python generate_word_manual.py
```

手册输出：

```text
docs/第三篇论文复现项目目录结构与VSCode训练操作手册.docx
```

手册详细解释项目目录、每个文件的用途、VS Code 环境配置、数据准备、从零训练、断点续训、权重管理、参数调整、替换数据与类别、评估推理、实验管理和常见错误。

## 6. 本轮复现结果

训练按 `patience=10` 自然早停于第 43 轮，最佳模型来自第 33 轮。论文在其未公开的原始划分上训练了 45 轮；本轮早 2 轮停止来自样本划分和软件环境差异。

最佳验证集指标：

| 最佳 epoch | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---:|---:|---:|---:|---:|
| 33 | 0.9607 | 0.9025 | 0.9644 | 0.6558 |

`best.pt` 在固定测试集上的结果：

| 范围 | Precision | Recall | F1 | AP50 / mAP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|---:|
| 整体 | 0.9455 | 0.9254 | 0.9353 | 0.9629 | 0.6374 |
| WB no pollen | 0.9746 | 0.9465 | 0.9603 | 0.9881 | 0.6716 |
| WB pollen | 0.8967 | 0.8937 | 0.8952 | 0.9317 | 0.6354 |
| Drone bee | 0.9650 | 0.9359 | 0.9502 | 0.9690 | 0.6053 |

RTX 4090、batch 4 下，Ultralytics 报告的纯模型推理耗时为 6.248 ms/图，即约 160.04 FPS。该数值不包含读图、可视化和写盘。最佳权重 SHA-256：

```text
46e72c5b4eb13251a160a5a932616196226f18546f6116f0bea1cc9be4fbc407
```

测试划分清单包含 16,112 个原始框。Ultralytics 在评估时发现并删除一个坐标完全相同的重复标签，因此实际计分实例数为 16,111；原始数据审计仍按论文口径保留 79,212 个标注。

论文报告 YOLOv10X 的 accuracy 为 93.9%、F1 为 0.92、Cohen's kappa 为 0.6105、速度为 25.93 FPS。论文把目标检测中的背景 TN 纳入 accuracy，但没有公开 TN 的构造方式，所以本项目不会把 mAP 改名为 accuracy，也不会伪造不可复算的 accuracy/kappa。可以直接比较 F1；FPS 还会受 GPU、CUDA、计时范围和软件版本影响。

## 7. 文件作用

| 文件/目录 | 作用 | 是否提交 GitHub |
|---|---|---|
| `README.md` | 完整复现手册、结果和文件说明 | 是 |
| `PAPER_NOTES.md` | 从论文整理出的数据、训练参数、增强和复现限制 | 是 |
| `requirements.txt` | Python 依赖及主要版本约束 | 是 |
| `setup.sh` | 创建 `.venv` 并安装依赖 | 是 |
| `inspect_archive.py` | 安全审计官方 ZIP，计算大小、结构与 SHA-256 | 是 |
| `prepare_dataset.py` | 解压嵌套 ZIP、修正异常路径、LabelMe 转 YOLO、固定划分 | 是 |
| `train_yolov10.py` | 按论文参数训练 YOLOv10X，支持 `--resume` | 是 |
| `evaluate.py` | 用最佳权重评估固定测试集并输出机器可读指标 | 是 |
| `predict.py` | 对图片、目录或视频推理并汇总类别数量 | 是 |
| `generate_report.py` | 根据清单、训练 CSV 和测试 JSON 生成中文 PDF | 是 |
| `generate_word_manual.py` | 生成详细的 VS Code 项目结构与训练操作手册 | 是 |
| `REPORT.md` | 便于版本管理和快速查看的结果报告 | 是 |
| `results/` | 最终测试 JSON、训练指标副本等小型复现结果 | 是 |
| `reports/` | 可下载的 PDF 结果报告 | 是 |
| `docs/` | 可下载的 Word 项目结构与训练操作手册 | 是 |
| `downloads/` | 4.2 GB 官方压缩包 | 否 |
| `data/` | 解压数据及生成的 YOLO 数据集 | 否 |
| `runs/` | 训练、评估、推理输出及大模型权重 | 否 |
| `weights/` | 初始预训练权重 | 否 |
| `.venv/` | 本地 Python 虚拟环境 | 否 |
| `archive_manifest.json` | 当前本机压缩包审计明细 | 否，摘要写入报告 |
| `dataset.yaml` | 指向本机生成数据集的 Ultralytics 配置 | 否，由脚本重建 |
| `dataset_manifest.json` | 4,590 个样本的固定划分清单 | 否，体积较大且由脚本重建 |

## 8. 复现限制

1. 论文没有公开 train/val/test 的逐帧列表和随机种子，本项目的 seed 50 划分不保证与作者相同。
2. 论文没有公开 YOLOv10 代码提交版本、逐模型权重、完整 accuracy/kappa 计算实现和部分增强细节。
3. 本项目尽量匹配论文的 YOLOv10X 参数；当前 Ultralytics 会把 1080 自动补齐至 1088。
4. 随机按视频帧划分可能让相邻帧跨越训练集与测试集。当前实现遵循论文给出的随机帧划分口径；如果研究跨视频泛化，应另做按视频分组的严格划分。
5. 数据类别高度不平衡，总体指标主要受无花粉工蜂影响，必须结合少数类逐类别 AP、Recall 和混淆矩阵解读。

## 9. GitHub 与大文件说明

GitHub 保存可以审查和重复执行的源码、说明、最终小型指标文件与 PDF 报告。官方数据集和 `.pt` 权重体积很大且有独立授权/来源，因此不写入普通 Git 历史。使用者需从官方 DOI 下载数据，再按本文步骤生成数据集和权重。
