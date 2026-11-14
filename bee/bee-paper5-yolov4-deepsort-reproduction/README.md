# 第五篇论文复现：YOLOv4 + DeepSORT 蜜蜂进出监测

对应论文：Ji-Su Ryu 等，**Honeybee In-Out Monitoring System by Object Recognition and Tracking from Real-Time Webcams**，*Journal of Apiculture* 36(4), 273–280, 2021，DOI `10.17519/apiculture.2021.11.36.4.273`。

本项目复现论文的核心工程链：单类蜜蜂检测、DeepSORT 跨帧关联、垂直阈值线方向计数和本地网页。原论文的 2,600 张受控通道图像、视频、源码与权重未公开，因此本项目使用公开 BEE22 连续入口视频和身份真值做方法复现。论文作者值、本地检测结果、DeepSORT 上限实验和完整系统结果始终分开记录。

## 1. 论文做了什么

论文的创新不仅是将 YOLOv3 换成 YOLOv4。作者先后修改蜂箱入口：单宽通道、多并行通道、白色背景、窄通道、MDF 防滑底板，最后加入 0.1 mm 铜片心脏瓣膜式单向门。设计目标是让蜜蜂单向且一次一只通过，从采集端减少重叠、相向运动和死锁。软件端使用 YOLOv4 检测蜜蜂，DeepSORT 保持身份，当框中心越过图像中部竖线时按方向更新计数。

原论文报告：

- 2,600 张人工标注图，训练/测试/验证比例为 7:2:1；
- 单类别 `bee`，YOLOv4，作者称训练 6,000 epochs，并选用 5,000 次权重；
- Logitech StreamCam，1080p、60 FPS；GTX 1660 SUPER、Ubuntu 18.04；
- 新系统检测率 99.5%，旧 YOLOv3 系统为 97.5%；
- loss rate 从 2.6% 降到 0.24%。

正文另称单图检测约 98%，与摘要/结论的 99.5% 口径没有衔接。论文没有严格定义“accuracy/detection rate”和“loss rate”的统计公式，也未报告 Precision、Recall、mAP、MOTA、IDF1 或事件级 F1。因此这些作者数值不能直接与本项目的标准检测/MOT 指标比较。

## 2. 本项目复现边界

| 层级 | 原论文 | 本项目 |
|---|---|---|
| 场景 | 心脏瓣膜单向、单蜂通道 | BEE22 开放蜂箱入口，密集、交叉、遮挡更多 |
| 检测数据 | 2,600 张未公开自采图 | BEE22 1,360/240/762 帧 train/val/test |
| 检测器 | YOLOv4 | Darknet YOLOv4，608×608，官方 `yolov4.conv.137` 初始化 |
| 训练长度 | 作者称 6,000 epochs | Darknet 6,000 iterations/batches |
| 跟踪器 | DeepSORT | `deep-sort-realtime` MobileNet 外观嵌入 + 卡尔曼滤波 |
| 计数 | 中央竖线，按相机方向解释进/出 | 中央竖线、8 px 死区、事件匹配容差 ±5 帧 |
| 评价 | detection rate、loss rate | P/R/F1/mAP50、MOTA/IDF1/IDSW、事件 P/R/F1 |

## 3. 数据划分

BEE22 按完整序列隔离，避免相邻帧进入不同集合：

- 训练：12 个序列，1,360 帧，16,050 个框；
- 验证：BEE22-15，240 帧，3,093 个框；
- 测试：BEE22-12/13/16，762 帧，12,205 个框。

固定划分清单位于 `data/split_manifest.csv`，SHA256 为 `14a789a5786f1862b8b3c9b70b04b92a7815038c8594af699a0ba3b73e0a9580`。

## 4. 当前结果

正式 YOLOv4 训练与完整系统测试完成后，本节由 `generate_documents.py` 同步更新。已经完成的 DeepSORT 真值框上限实验如下：

| 指标 | 结果 |
|---|---:|
| GT 检测框数量 | 12,205 |
| MOTA | 0.9281 |
| IDF1 | 0.8255 |
| Recall | 0.9397 |
| ID switches | 142 |
| Misses | 736 |
| 端到端速度（含外观嵌入与 I/O） | 2.89 FPS |

这里给 DeepSORT 输入的是完美真值框，仍然发生身份切换和轨迹初始化漏失。这一结果说明原论文的单向、单蜂通道确实能从物理条件上简化关联和计数；开放入口中的检测框准确并不自动保证事件计数准确。

<!-- FINAL_RESULTS_START -->
### 正式检测与完整系统结果

验证集在 `yolov4-bee_5000.weights` 与 `yolov4-bee_final.weights` 之间选择，最终采用 `yolov4-bee_5000.weights`；测试集没有参与选权重。训练日志共解析 6,000 次更新，最后平均损失为 0.5379。

| 层级 | 指标 | 结果 |
|---|---|---:|
| 检测 | Precision | 0.9400 |
| 检测 | Recall | 0.9300 |
| 检测 | F1 | 0.9300 |
| 检测 | mAP@0.50 | 0.9321 |
| 完整 MOT | MOTA | 0.8070 |
| 完整 MOT | IDF1 | 0.8080 |
| 完整 MOT | ID switches | 212 |
| 完整 MOT | Misses / FP | 1478 / 665 |
| 越线事件 | Precision / Recall / F1 | 0.6000 / 0.2000 / 0.3000 |
| 端到端 | FPS | 2.67 |

这些数值来自 BEE22 开放入口测试序列，不能与论文受控单向通道的 99.5% 直接等同。
<!-- FINAL_RESULTS_END -->

## 5. 目录结构与文件作用

```text
bee-paper5-yolov4-deepsort-reproduction/
├── README.md                    # 本说明、结果边界和全部命令
├── REPORT.md                    # 精简的可版本管理结果报告
├── setup.sh                     # 环境、源码、权重、数据一键准备
├── requirements.txt             # 固定 Python 依赖
├── download_assets.py           # 固定 Darknet 提交与官方初始化权重
├── download_weights_parallel.py # 慢速网络下的分段权重下载器
├── build_darknet.sh             # RTX 4090/CUDA/cuDNN 编译配置
├── prepare_data.py              # BEE22 转 Darknet 格式及序列隔离划分
├── configure_yolov4.py          # 生成单类 YOLOv4 608 配置
├── train_yolov4.py              # 从头训练或断点续训
├── evaluate_detector.py         # 单权重测试集检测评价
├── evaluate_checkpoints.py      # 在验证集比较周期权重并选最佳
├── darknet_detector.py          # Python Darknet 推理封装
├── evaluate_tracking.py         # DeepSORT、MOT、越线事件评价
├── predict.py                   # 图片/目录推理
├── track_video.py               # 视频跟踪、方向计数、CSV 导出
├── render_tracks.py             # BEE22 轨迹结果视频可视化
├── app.py                       # Flask 本地上传与结果下载页
├── collect_results.py           # Darknet 日志转训练历史 CSV
├── update_markdown_results.py   # 将最终 JSON 指标写回 Markdown
├── finalize_experiment.py       # 固定顺序完成选权重、测试、跟踪和文档
├── watch_and_finalize.sh        # 等待训练完成后自动执行收尾流程
├── generate_documents.py        # 生成 PDF 与两份 Word 文档
├── configs/                     # 固定 YOLOv4 配置
├── data/                        # 配置、清单与本地数据链接
├── results/                     # JSON、CSV、评估日志和图表
├── runs/                        # 训练权重、轨迹和演示视频
├── docs/                        # VS Code 手册与专业论文解析
├── reports/                     # 中文复现结果 PDF
├── weights/                     # 官方初始化权重（不提交 Git）
└── vendor/darknet/              # 固定上游 Darknet（setup 下载）
```

## 6. VS Code 从零准备

在 VS Code 中打开本项目目录，打开“终端 → 新建终端”：

```bash
cd /jzk-model/jzh_model/bee/bee-paper5-yolov4-deepsort-reproduction
bash setup.sh
```

选择解释器：按 `Ctrl+Shift+P`，输入 `Python: Select Interpreter`，选择项目中的 `.venv/bin/python`。

如果第二篇项目已经下载 BEE22，`prepare_data.py` 会复用其图像并创建硬链接，不会复制 350 MB 数据。若移动到新电脑，需要先按第二篇项目 README 下载 BEE22，或给 `prepare_data.py --source /你的/yolo数据路径`。

## 7. 手动训练

### 7.1 正式训练

```bash
.venv/bin/python train_yolov4.py
```

实际底层命令等价于：

```bash
vendor/darknet/darknet detector train \
  data/bee22_darknet/bee.data \
  configs/yolov4-bee.cfg \
  weights/yolov4.conv.137 \
  -dont_show -clear
```

配置关键值：`batch=64`、`subdivisions=16`、`608×608`、`max_batches=6000`、`steps=4800,5400`、`classes=1`、检测头 `filters=18`。本机未编译 OpenCV，因此明确设置 `mosaic=0`；其余 Darknet 增强仍会使用。

### 7.2 断点续训

```bash
.venv/bin/python train_yolov4.py \
  --resume runs/train/backup/yolov4-bee_last.weights
```

断点续训不能加 `-clear`，脚本会自动处理。不要用 `yolov4.conv.137` 冒充训练完成权重，它只包含前 137 层的通用初始化。

### 7.3 修改训练参数

编辑 `configure_yolov4.py` 后重新运行它。常见修改：

- 显存不足：增大 `subdivisions`；
- 速度优先：将宽高改为 416；
- 小目标定位优先：保留 608，或先统计目标像素尺寸；
- 类别数改变：每个 `[yolo]` 的 `classes` 必须同步修改，前一层 `filters=(classes+5)×3`；
- 训练长度改变：同步调整 `max_batches` 和 `steps`。

## 8. 检测评估

```bash
.venv/bin/python evaluate_detector.py \
  --weights runs/train/backup/yolov4-bee_best.weights

.venv/bin/python evaluate_checkpoints.py \
  runs/train/backup/yolov4-bee_5000.weights \
  runs/train/backup/yolov4-bee_final.weights
```

`evaluate_checkpoints.py` 默认只在验证集比较权重，并把最佳权重复制为 `yolov4-bee_best.weights`。随后用 `evaluate_detector.py` 在测试集评价一次。测试集不参与权重选择。原始 Darknet 日志和汇总 JSON 会保存到 `results/`。

训练完成后也可以用固定流水线一次完成全部后处理：

```bash
.venv/bin/python finalize_experiment.py
```

长时间训练时可在另一个终端启动自动收尾监视器：

```bash
nohup bash watch_and_finalize.sh >/dev/null 2>&1 &
tail -f results/finalization.log
```

## 9. DeepSORT 与计数

完整 YOLOv4+DeepSORT：

```bash
.venv/bin/python evaluate_tracking.py \
  --weights runs/train/backup/yolov4-bee_best.weights
```

只评价 DeepSORT 关联上限：

```bash
.venv/bin/python evaluate_tracking.py --oracle-gt
```

`--oracle-gt` 直接使用真值框作为检测结果，用于回答“如果检测完全正确，DeepSORT 还会产生多少 ID 切换和计数误差”。它不是完整系统成绩。

## 10. 图片、视频与网页

图片或目录：

```bash
.venv/bin/python predict.py path/to/image.jpg
```

视频跟踪与方向计数：

```bash
.venv/bin/python track_video.py path/to/video.mp4 \
  --line-x 475 --output runs/my_video
```

输出包括 `tracked.mp4`、`tracks.csv` 和 `summary.json`。画面左到右/右到左不能自动等同于进巢/出巢，必须根据相机安装方向映射。

网页：

```bash
.venv/bin/python app.py
```

浏览器访问 `http://127.0.0.1:5000`。

## 11. 如何替换成自己的单向通道数据

1. 固定相机、通道、照明、焦距和入口方向；
2. 以完整视频或拍摄日期划分 train/val/test，不能随机拆相邻帧；
3. 每张图与标签同名，例如 `000001.jpg` 和 `000001.txt`；
4. Darknet 标签每行是 `class cx cy width height`，全部归一化到 0–1；
5. 明确制定截断蜂和重叠蜂规则；原论文只标身体可见超过 90% 的蜂，并限制重叠框；
6. 额外标注轨迹 ID 和真实过线事件，检测框标签不能评价 IDF1 或进出 F1；
7. 单独记录通道拒入、停留、逆行和拥堵，否则高检测率可能掩盖硬件对蜂行为的影响。

## 12. 论文复现中最容易误解的地方

- 原文“6,000 epochs”更像 Darknet 的 6,000 iterations/batches；2,600 张图若真做 6,000 个完整 epoch，训练量会完全不同。
- 99.5% detection accuracy 没有给出公式，不能当作 mAP50。
- DeepSORT 不会修复检测错误，它只能利用运动和外观关联已有检测框。
- 原文称 DeepSORT 使用 YOLOv4 训练得到的连接权重，这在标准实现中并不准确；DeepSORT 的外观嵌入网络与 YOLO 检测权重是两个模块。
- 单向门提高视觉可分性，也会改变蜜蜂行为。论文已观察到角落停留、逆行尝试和拥堵。
- 开放入口 BEE22 比论文的单蜂通道更困难，因此本地分数主要验证方法和失败模式，不是对作者结果的直接重复。

## 13. 文档

- `reports/第五篇论文复现结果报告.pdf`
- `docs/第五篇论文_VSCode项目结构与训练操作手册.docx`
- `docs/第五篇论文_专业深度解析与论文写作评析.docx`
- `docs/第五篇论文_详细分析与训练复现实验报告.docx`（论文解析与本次真实实验合并版）

原始 PDF 保持在 `/jzk-model/pdf-paper/31356.pdf`，没有移动或写入仓库。

## 14. GitHub 中包含与不包含的内容

仓库包含复现源码、固定配置、数据划分清单、训练历史 CSV、最终指标 JSON、训练曲线、PDF 报告和 Word 文档。BEE22 原始图像、Darknet 源码副本、初始化权重和约 245 MB 的训练权重不提交 Git；它们分别由 `prepare_data.py`、`download_assets.py` 和训练命令在本地建立。这样可以避免重复分发数据及 GitHub 单文件大小限制。
