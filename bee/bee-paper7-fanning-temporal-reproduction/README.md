# 第七篇论文复现：蜜蜂扇风行为的 RGB、TSG 与 TEM 时序检测

对应论文：Tomyslav Sledevič，**Evaluation of Single-Shot Object Detection Models for Identifying Fanning Behavior in Honeybees at the Hive Entrance**，*Agriculture* 15(15), 1609, 2025，DOI `10.3390/agriculture15151609`。

## 复现目标

论文把蜂箱入口扇风蜂作为单类目标检测任务，并比较三种输入：

- RGB：当前帧 `I(n)`；
- TSG：蓝、绿、红通道依次为灰度帧 `I(n-1), I(n), I(n+1)`；
- TEM：蓝、绿、红通道依次为 `|I(n)-I(n-1)|, I(n), |I(n)-I(n+1)|`。

本项目首先使用完全相同的数据划分和一个固定的 YOLO11n，控制模型、训练参数和随机种子，只比较输入编码。论文完整矩阵包含 YOLOv8/11/12 的 n/s/m/l/x 共 45 个组合；首轮复现选择三组受控实验，完成后再扩展模型规模。

## 原论文关键事实

- 官方 Zenodo 数据：18,000 帧。当前下载标签统计 57,598 框，比论文正文的 57,597 多 1 框；训练按公开数据包的实际标签运行；
- 训练集为 Hive 1–3，Hive 4 为验证集；本复现用 Hive 4 做逐轮验证、早停和最佳权重选择，因此不把它称为独立测试集；
- 原始视频 1920×1080、30 FPS，相机约在入口上方 30 cm；
- 模型输入 1024×576；AdamW，学习率 0.001，momentum 0.9；
- 最多 1000 epoch，patience 100，通常在 100–200 epoch 收敛；
- 论文报告 TSG/TEM 通常比 RGB 提高约 5–10 个 mAP50 百分点，最佳约 85%。

## 磁盘受限的数据准备

官方 ZIP 为 17,336,965,310 字节。`prepare_remote_dataset.py` 使用 HTTP Range 读取 ZIP，不在本机保存完整压缩包；图像读出后立即缩放为论文输入尺寸。默认处理全部 18,000 帧：

```bash
bash setup.sh
.venv/bin/python prepare_remote_dataset.py
```

快速验证可限制每段视频的中央连续帧数：

```bash
.venv/bin/python prepare_remote_dataset.py --max-per-sequence 100
```

## 训练

为缩短本机实验时间，当前正式对比使用加速配置：每种编码最多 50 epoch、batch 32、patience 15，固定 YOLO11n 与随机种子；RGB/TSG/TEM 参数保持一致。论文原设置为最多 1000 epoch、patience 100，文中通常在 100–200 epoch 收敛。因此本次加速实验可用于编码方案的初步比较，但不等同于论文完整训练预算；报告中已标注该限制。正式训练在 RTX 4090 上的结果为：RGB 24 轮/19.5 分钟、TSG 22 轮/19.8 分钟、TEM 28 轮/27.2 分钟，均触发早停。

训练器通过 `temporal_loader.py` 在读取样本时动态生成 TSG/TEM，因此不需要额外保存两套各 18,000 张的图像。`encode_temporal.py` 仅用于导出可视化样例和调试编码结果。

```bash
.venv/bin/python train.py rgb --model weights/yolo11n.pt --epochs 50 --batch 32 --patience 15
.venv/bin/python train.py tsg --model weights/yolo11n.pt --epochs 50 --batch 32 --patience 15
.venv/bin/python train.py tem --model weights/yolo11n.pt --epochs 50 --batch 32 --patience 15
```

评价：

```bash
.venv/bin/python evaluate.py rgb
.venv/bin/python evaluate.py tsg
.venv/bin/python evaluate.py tem
```

训练结果已完成。报告与操作文档位于 `REPORT.md`、`reports/` 和 `docs/`。Hive 4 指标用于训练期间验证与早停选权重，因此只能视作验证表现；需要新增独立蜂箱或重新划分数据，才能得到无泄漏的最终测试结论。论文原始 PDF 保留在 `/jzk-model/pdf-paper/agriculture-15-01609-v2.pdf`。



<!-- FINAL_RESULTS_START -->
### 本地受控实验结果

| 输入 | Precision | Recall | mAP@0.50 | mAP@0.50:0.95 |
|---|---:|---:|---:|---:|
| RGB | 0.6530 | 0.6354 | 0.6697 | 0.4854 |
| TSG | 0.7604 | 0.7131 | 0.8035 | 0.5484 |
| TEM | 0.6850 | 0.6820 | 0.7382 | 0.5190 |

最佳输入为 **TSG**，mAP@0.50=0.8035；相对 RGB 变化 +0.1338。
<!-- FINAL_RESULTS_END -->
