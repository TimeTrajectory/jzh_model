# 第四篇论文复现：IntelliBeeHive 蜜蜂、花粉与入口跟踪系统

对应论文：Christian I. Narcia-Macias et al., **IntelliBeeHive: An Automated Honey Bee, Pollen, and Varroa Destructor Monitoring System**, arXiv:2309.08955v1, 2023。

本项目复现论文的主要工程链：YOLOv7-tiny 蜜蜂检测、普通/携粉蜜蜂检测、最近中点跟踪、入口方向计数、本地网页和 ONNX 部署导出。项目已完成两套模型各 100 epochs 的实际训练，并在按视频组隔离的测试集上得到结果。

> **复现结论边界**：作者没有公开原始训练数据、视频划分、源码和权重。本项目使用公开 Caltech Honeybee 与本机已有 BEE22 做替代验证，属于“方法与工程流程复现”，不能声称严格复现作者数值。论文的 `mite` 类由粘在死蜂上的 1.5 mm 红珠模拟，本项目没有将其写成真实瓦螨检测能力。

## 1. 已完成内容

- 固定官方 YOLOv7 源码提交与 `yolov7-tiny.pt` 权重校验值。
- 固定 Caltech Honeybee 数据提交，转换 JSON 框为 YOLO 格式。
- 按帧号编码的视频组划分 624/178/149 张 train/val/test，防止相邻帧跨集合。
- 训练蜜蜂单类 YOLOv7-tiny：416×416、batch 8、100 epochs。
- 训练普通蜜蜂/携粉蜜蜂两类 YOLOv7-tiny：416×416、batch 8、100 epochs。
- 在独立测试集计算 P、R、F1、mAP@0.5、mAP@0.5:0.95、速度和逐类别指标。
- 实现论文的最近中点、50 px 容差、上下三分之一触发线状态机。
- 用 BEE22 真值框隔离检测误差，诊断轨迹纯度、ID 切换和越线计数误差。
- 提供图片预测、视频检测与计数、Flask 本地网页、TorchScript/ONNX 导出。
- 生成结果 PDF、VS Code Word 手册和专业论文解析 Word 文档。

## 2. 结果摘要

### 2.1 独立测试集

| 任务/类别 | Labels | Precision | Recall | F1 | mAP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|---:|---:|
| 蜜蜂单类 | 1,043 | 0.930 | 0.862 | 0.895 | 0.905 | 0.512 |
| 两类总体 | 1,043 | 0.848 | 0.787 | 0.816 | 0.849 | 0.452 |
| ordinary bee | 945 | 0.922 | 0.871 | 0.896 | 0.920 | 0.527 |
| pollen-bearing bee | 98 | 0.775 | 0.704 | 0.738 | 0.778 | 0.377 |

RTX 4090、416×416、batch 8 测试：蜜蜂模型推理与 NMS 合计约 4.9 ms/图，两类模型约 5.3 ms/图。这个速度不能直接与论文 Jetson Nano TensorRT 的约 27 ms/帧作硬件等价比较。

### 2.2 跟踪规则诊断

| 项目 | 结果 |
|---|---:|
| BEE22 测试序列 | 3 |
| 关联分配 | 12,205 |
| 加权轨迹纯度 | 0.9738 |
| ID 切换 | 199 |
| Arriving 累计绝对误差 | 4 |
| Leaving 累计绝对误差 | 26 |

高轨迹纯度与频繁碎片化可以同时发生。论文的单帧最近邻规则会在漏检、快速移动和拥挤时删除旧轨迹并创建新 ID，因此只报告总计数准确率不足以描述跟踪质量。

## 3. 数据和版本

| 资源 | 固定版本 |
|---|---|
| YOLOv7 | `a207844b1ce82d204ab36d87d496728d3d2348e7` |
| Caltech Honeybee | `0a06fabcf23bbc75f03af4b028f8070bda8a2649` |
| 官方 YOLOv7-tiny 权重 SHA-256 | `0fa1423606133c06362ec716029dade1169d5631e83195b75d8efa66d2ee0b77` |
| 划分种子 | `2309` |
| manifest SHA-256 | `484cdb6625edf9add3ab05313bb590b84a086518fd5c4693b22d68185ae88905` |

公开数据原始仓库约 1.2 GB，不提交到本仓库。运行 `download_assets.py` 自动获取。训练图像在两个任务目录中使用硬链接，避免重复占用磁盘。

## 4. 项目目录与文件作用

```text
bee-paper4-intellibeehive-reproduction/
├── README.md                         当前完整操作入口
├── REPORT.md                         本轮实验结果和结论
├── setup.sh                          一键安装、下载、准备数据
├── requirements.txt                  Python 依赖
├── download_assets.py                固定提交下载源码、数据和权重
├── prepare_dataset.py                JSON→YOLO、分组划分、统计与 YAML
├── run_experiments.py                bee/pollen 双模型训练和断点续训
├── evaluate.py                       独立测试集评估
├── collect_results.py                汇总 JSON/CSV/曲线到 results/
├── inference.py                      YOLOv7 推理适配器
├── predict.py                        图片、目录或视频基础预测
├── tracking.py                       论文中点跟踪器与触发线状态机
├── evaluate_tracking.py              BEE22 跟踪规则诊断
├── monitor_video.py                  视频检测、跟踪、方向和携粉计数
├── app.py                            Flask 本地图片演示
├── export_onnx.py                    best.pt → ONNX
├── generate_documents.py             Word/PDF 文档生成器
├── data/                              YAML、manifest、统计；大图被忽略
├── downloads/                         原始数据；Git 忽略
├── vendor/                            固定 YOLOv7 源码；Git 忽略
├── runs/                              训练、测试、预测和权重；Git 忽略
├── results/                           可审查指标、CSV 和结果图
├── docs/                              两份 Word 文档
└── reports/                           PDF 结果报告
```

## 5. VS Code 从零运行

### 5.1 打开项目

1. VS Code 选择“文件 → 打开文件夹”，打开本项目根目录。
2. `Ctrl+Shift+P` → `Python: Select Interpreter`。
3. 选择项目中的 `.venv/bin/python`。
4. 打开 VS Code 集成终端，后续命令均在项目根目录运行。

### 5.2 一键安装

```bash
chmod +x setup.sh
./setup.sh
source .venv/bin/activate
```

手动分步执行：

```bash
python -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
python download_assets.py
python prepare_dataset.py --clean
```

确认 GPU：

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

## 6. 手动训练

论文主配置：YOLOv7-tiny、416×416、batch 8、100 epochs。

```bash
# 蜜蜂单类
python run_experiments.py --task bee --epochs 100 --batch 8 --workers 8

# 普通/携粉两类
python run_experiments.py --task pollen --epochs 100 --batch 8 --workers 8

# 顺序训练两套
python run_experiments.py --task all --epochs 100 --batch 8 --workers 8
```

训练输出：

```text
runs/train/bee_yolov7_tiny_e100/weights/best.pt
runs/train/bee_yolov7_tiny_e100/weights/last.pt
runs/train/pollen_yolov7_tiny_e100/weights/best.pt
runs/train/pollen_yolov7_tiny_e100/weights/last.pt
```

- `best.pt`：验证适应度最佳，用于测试、推理和导出。
- `last.pt`：最后一轮，用于断点续训。
- `weights/yolov7-tiny.pt`：官方 COCO 预训练初始化，不是本项目结果。

### 6.1 中断后续训

```bash
python run_experiments.py --task bee --epochs 100 --resume
python run_experiments.py --task pollen --epochs 100 --resume
```

`--resume` 需要原运行目录中的 `last.pt`。如果改变运行名或 epoch 数，请直接使用上游 `train.py --resume /绝对路径/last.pt`。

### 6.2 调整参数

```bash
# 显存不足
python run_experiments.py --task bee --epochs 100 --batch 4

# Windows 多进程异常
python run_experiments.py --task bee --epochs 100 --workers 0

# CPU 冒烟测试
python run_experiments.py --task bee --epochs 1 --device cpu --workers 0
```

修改输入尺寸、模型 CFG 或超参数时，编辑 `run_experiments.py` 中的 `--img-size`、`--cfg`、`--hyp`。正式对比必须使用新运行名，保留基线。

## 7. 测试与结果汇总

```bash
python evaluate.py --task bee --epochs 100
python evaluate.py --task pollen --epochs 100
python evaluate_tracking.py
python collect_results.py
```

关键文件：

- `results/metrics_summary.json`：数据、环境、验证、测试、速度和跟踪汇总。
- `results/bee_training_history.csv` / `pollen_training_history.csv`：100 轮指标。
- `results/tracking_evaluation.json`：三序列跟踪诊断。
- `results/figures/`：训练曲线、PR/F1、混淆矩阵和测试预测示例。

## 8. 图片、视频与网页

### 8.1 图片/目录预测

```bash
python predict.py --task pollen --source /path/to/image_or_folder --confidence 0.25
```

输出到 `runs/predict/pollen/`。

### 8.2 入口视频监测

```bash
python monitor_video.py \
  --source /path/to/hive.mp4 \
  --output runs/video/hive_result.mp4 \
  --confidence 0.25
```

输出 MP4、CSV 和 JSON。默认语义要求画面上方是蜂箱内部、下方是外部；相机方向相反时必须调整状态定义。

### 8.3 本地网页

```bash
python app.py
```

浏览器打开 `http://127.0.0.1:7860`，上传图片、选择模型和置信度。

这个 Flask 页面是学习演示，不等同于论文的 Laravel/MySQL/REST 多用户平台。

## 9. ONNX 与 Jetson 部署

```bash
python export_onnx.py --task bee --epochs 100
python export_onnx.py --task pollen --epochs 100
```

本轮已成功生成两套 `best.onnx`，固定输入为 `1×3×416×416`。TensorRT engine 应在目标 Jetson Nano 和配套 JetPack/TensorRT 上构建，然后用同一验证图比较 PyTorch 与 TensorRT 输出。不要把 RTX 4090 上生成的 engine 当作 Jetson 可移植文件。

## 10. 真实瓦螨扩展要求

论文用红珠模拟螨体，其高指标不具有真实诊断效度。扩展真实瓦螨时应：

1. 采集真实活蜂螨图像并由养蜂/昆虫专家复核。
2. 先检测蜜蜂，再在高分辨率蜂体裁剪上标注螨框或掩膜。
3. 按蜂箱、日期和场地分组，保留完全未见蜂场测试。
4. 报告逐类 AP、敏感度、特异度、校准曲线和置信区间。
5. 与酒精洗、糖滚或标准黏板得到的蜂群感染率校准。
6. 把模型作为筛查/复核工具，不直接据此给出用药决定。

## 11. 文档下载

- [`docs/第四篇论文_VSCode项目结构与训练操作手册.docx`](docs/第四篇论文_VSCode项目结构与训练操作手册.docx)
- [`docs/第四篇论文_IntelliBeeHive专业深度解析与论文写作评析.docx`](docs/第四篇论文_IntelliBeeHive专业深度解析与论文写作评析.docx)
- [`reports/第四篇论文复现结果报告.pdf`](reports/第四篇论文复现结果报告.pdf)

专业解析包含系统架构、数据有效性、模型、跟踪状态机、网站/数据库、指标公式审校、创新分层、实验结论、论文写作优点与不足，以及可发表级改进实验方案。

## 12. GitHub 与大文件

代码、文档、指标、CSV 和结果图上传到 `TimeTrajectory/jzh_model` 的 `bee/bee-paper4-intellibeehive-reproduction/`。

原始数据、第三方源码、虚拟环境和完整 `runs/` 被 `.gitignore` 排除，可由脚本重建。训练权重与 ONNX 保留在当前电脑；如 GitHub 版本提供分卷权重，使用仓库中的合并脚本恢复。公开数据与第三方源码遵守其各自许可。

