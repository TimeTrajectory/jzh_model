# 第六篇论文复现：无刺蜂互联网监测与采集条件实验

对应论文：N. S. Ahmad Kamal、S. I. Safie、E. M. Mohd Yusof，**Smart Stingless Beehive Internet Based Monitoring System**，*Malaysian Journal of Industrial Technology* 6(2), 41–50, 2022。

项目复现论文的可验证工程主链：YOLOv3 系列蜜蜂检测、视频越线计数、每分钟活动判断、网页上传，以及相机视场与背景颜色的条件实验。原论文的无刺蜂图像、MATLAB 工程和权重没有公开，因此本项目使用 BEE22 蜂箱入口数据，并将物理相机高度实验实现为明确标注的合成视场代理。论文值、本地结果和代理实验不混为同一结果。

## 1. 原论文做了什么

- 目标物种为马来西亚无刺蜂 `Heterotrigona itama`；
- MATLAB 中使用 YOLOv3，对应文字描述为 SqueezeNet 特征网络和两个检测头；
- 摄像头分辨率 640×480，支持实时摄像头和离线视频；
- 每分钟检测数量不少于 20 显示 `ACTIVE`，低于 20 显示 `INACTIVE` 并告警；
- 比较 10、20、30 cm 三种相机高度与白、棕、深棕三种底板；
- 论文选择 30 cm + 棕色底板，报告“accuracy”75%；训练图给出 AP 0.69。

论文未给出 accuracy 的逐图计算公式、检测框测试真值、Precision/Recall、数据划分、训练图像数量、epoch 数、随机种子或代码。各条件通常只测试 20 张图片，10 cm 深棕仅 7 张，20/30 cm 深棕各 10 张，样本量并不平衡。

## 2. 复现边界

| 层级 | 原论文 | 本项目 |
|---|---|---|
| 数据 | 未公开无刺蜂农场图像 | BEE22 蜜蜂入口连续序列 |
| 模型 | MATLAB YOLOv3 + SqueezeNet | Darknet YOLOv3-tiny，两检测头，416×416 |
| 训练 | 细节缺失，图示约 2700 iterations | 固定 2700 iterations |
| 相机高度 | 真实 10/20/30 cm | 中央视场裁切代理 0.65/0.82/1.00 |
| 背景 | 真实底板颜色 | 标注框外像素受控重着色 |
| 活动 | 每分钟检测数阈值 20 | 越线事件/分钟阈值 20，方向保持图像坐标含义 |
| 评价 | accuracy、AP | P/R/F1/mAP50、条件矩阵、速度 |

这里选择 YOLOv3-tiny 是可运行代理。它保留 YOLOv3 的两尺度检测思想，但主干不是论文所称的 SqueezeNet，因此属于方法复现，不是架构逐层复制。

## 3. 数据划分

- train：1,360 帧、16,050 个框，BEE22-01～11、14；
- val：240 帧、3,093 个框，BEE22-15；
- test：762 帧、12,205 个框，BEE22-12、13、16；
- 完整序列隔离，清单 SHA256：`14a789a5786f1862b8b3c9b70b04b92a7815038c8594af699a0ba3b73e0a9580`。

## 4. 最终结果

<!-- FINAL_RESULTS_START -->
### 正式训练与检测结果

训练完成 2,700 次迭代，最终平均损失 2.2080。验证集 mAP@0.50 为 0.8172；独立测试集结果如下。

| Precision | Recall | F1 | mAP@0.50 |
|---:|---:|---:|---:|
| 0.8700 | 0.8700 | 0.8700 | 0.8576 |

### 3×3 采集条件代理实验

每个组合固定抽取 20 张测试帧。最佳代理组合为 `30cm + white`，mAP@0.50=0.9141。这里的高度是中央视场裁切因子，背景是框外像素重着色；结果只用于敏感性分析。
<!-- FINAL_RESULTS_END -->

## 5. 目录结构

```text
bee-paper6-stingless-monitoring-reproduction/
├── README.md                         # 论文边界、结果和全部命令
├── setup.sh                          # 环境、Darknet、权重、数据准备
├── download_bee22.py                 # 断点下载 BEE22 并做大小、CRC、SHA256 校验
├── prepare_data.py                   # 序列隔离数据与审计清单
├── configure_yolov3_tiny.py          # 单类两检测头配置
├── train_yolov3.py                   # 正式训练与断点续训
├── evaluate_detector.py              # val/test 标准检测评价
├── condition_experiment.py           # 3×3 视场与背景代理实验
├── darknet_detector.py               # libdarknet Python 推理封装
├── predict.py                        # 图片推理
├── monitor_video.py                  # 视频检测、关联、越线与活动判断
├── app.py                            # 本地视频上传网页
├── collect_results.py                # 训练日志转 CSV
├── finalize_experiment.py             # 固定顺序完成评价和文档
├── watch_and_finalize.sh              # 长训练结束后的自动收尾
├── generate_documents.py             # PDF 与 Word 文档生成
├── configs/                          # YOLOv3-tiny 固定配置
├── data/                             # 数据摘要、划分清单与本地链接
├── results/                          # JSON、CSV 和图表
├── runs/                             # 本地权重和视频输出
├── docs/                             # VS Code 手册与论文解析
└── reports/                          # 中文结果报告
```

## 6. VS Code 从零准备

```bash
cd /jzk-model/jzh_model/bee/bee-paper6-stingless-monitoring-reproduction
bash setup.sh
```

在 VS Code 中按 `Ctrl+Shift+P`，运行 `Python: Select Interpreter`，选择 `.venv/bin/python`。

数据集和训练权重因体积较大，不提交到 GitHub。若本机没有第二篇项目已经转换好的 BEE22，继续执行：

```bash
.venv/bin/python download_bee22.py
.venv/bin/python prepare_data.py
```

下载包约 354.8 MB，脚本支持分段重试，并校验固定大小、ZIP CRC 和 SHA256。也可以把已转换的 BEE22 YOLO 目录传给 `prepare_data.py --source /path/to/yolo`。准备完成后再开始训练。

## 7. 手动训练与续训

```bash
.venv/bin/python train_yolov3.py

.venv/bin/python train_yolov3.py \
  --resume runs/train/backup/yolov3-tiny-bee_last.weights
```

固定配置：`batch=64`、`subdivisions=16`、`416×416`、`max_batches=2700`、`steps=2160,2430`、`classes=1`、两个检测头前均为 `filters=18`。

## 8. 检测与条件实验

```bash
.venv/bin/python evaluate_detector.py --split val
.venv/bin/python evaluate_detector.py --split test
.venv/bin/python condition_experiment.py --samples 20
```

条件实验中的“10/20/30 cm”是视场裁切代理，不代表真实物理距离。其用途是验证系统对目标尺度、画面覆盖和背景颜色的敏感程度。

## 9. 图片、视频与网页

```bash
.venv/bin/python predict.py path/to/image.jpg
.venv/bin/python monitor_video.py path/to/video.mp4 --output runs/videos/demo
.venv/bin/python app.py
```

网页地址为 `http://127.0.0.1:5000`。输出包括标注视频、逐帧轨迹 CSV、越线事件 JSON 和活动摘要。图像左右方向只有结合实际摄像机安装方位后才能解释为 fly-in/fly-out。

## 10. 自建无刺蜂数据时必须记录

1. 物种、蜂箱编号、日期和天气；
2. 相机到入口的真实距离、焦距、分辨率、曝光和帧率；
3. 底板颜色的标准色值和光照；
4. 按完整视频和蜂箱划分 train/val/test；
5. 检测框、轨迹 ID 和真实进出事件分别标注；
6. 报告置信区间，避免用十几张图得出稳定结论；
7. 活动阈值应由多蜂箱长期数据验证，不能把固定 20 次/分钟直接解释为健康诊断。

原始论文 PDF 保留在 `/jzk-model/pdf-paper/4.-SMART-STINGLESS-BEEHIVE-INTERNET-BASED-MONITORING-SYSTEM.pdf`，未移动或提交仓库。

