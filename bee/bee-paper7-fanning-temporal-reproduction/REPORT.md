# 第七篇论文复现结果报告

论文：Tomyslav Sledevič，*Evaluation of Single-Shot Object Detection Models for Identifying Fanning Behavior in Honeybees at the Hive Entrance*，2025。

## 复现设计

使用官方 Zenodo 数据和论文的蜂箱隔离划分。为了控制变量，首轮固定 YOLO11n、初始化权重、随机种子与训练参数，只改变 RGB、TSG、TEM 输入。三类输入使用同一标签；TSG/TEM 在加载时由相邻帧动态生成。

当前下载数据包统计为 57,598 个框，比论文正文记载的 57,597 多 1 个；复现按公开数据包的实际标签计数。

论文完整实验包含 45 个模型与输入组合。本项目首轮三组实验用于验证“时间编码是否优于 RGB”的核心假设，不将 YOLO11n 结果冒充论文最佳 YOLO11m/YOLOv8l 结果。

<!-- FINAL_RESULTS_START -->
### 本地受控实验结果

| 输入 | Precision | Recall | mAP@0.50 | mAP@0.50:0.95 |
|---|---:|---:|---:|---:|
| RGB | 0.6530 | 0.6354 | 0.6697 | 0.4854 |
| TSG | 0.7604 | 0.7131 | 0.8035 | 0.5484 |
| TEM | 0.6850 | 0.6820 | 0.7382 | 0.5190 |

最佳输入为 **TSG**，mAP@0.50=0.8035；相对 RGB 变化 +0.1338。
<!-- FINAL_RESULTS_END -->

