# 第三篇论文复现结果报告

## 论文与复现范围

对应论文：P. Chaudhary 等，*Estimating colony strength and pollination efficiency in honey bees using a novel dataset and deep learning-based models*，Smart Agricultural Technology 14 (2026) 102005。

本项目完成论文最佳实时检测模型 YOLOv10X 的官方数据审计、LabelMe 到 YOLO 转换、固定数据划分、训练、断点续训、独立测试、推理和 PDF 报告生成。检测类别为无花粉工蜂、带花粉工蜂和雄蜂。

## 官方数据审计

- 官方附件：`supplement.zip`，4,236,622,867 字节；
- SHA-256：`cae66fc3d855ef1d26f570afe574cbfe23763c5da845b100625d0d490fd6c891`；
- 有效数据：4,590 帧、79,212 个原始边界框；
- 类别：WB no pollen 73,981、WB pollen 4,272、Drone bee 559，与论文 Table 2 完全一致；
- 排除了 ZIP 中的 `__MACOSX` 资源叉；
- 修复了两份 LabelMe JSON 的错误 `imagePath`，没有跳过有效标注。

固定 seed 50 的 60%/20%/20% 划分：

| 划分 | 图片 | WB no pollen | WB pollen | Drone bee | 总框数 |
|---|---:|---:|---:|---:|---:|
| 训练 | 2,754 | 44,450 | 2,463 | 339 | 47,252 |
| 验证 | 918 | 14,459 | 887 | 102 | 15,448 |
| 测试 | 918 | 15,072 | 922 | 118 | 16,112 |
| 合计 | 4,590 | 73,981 | 4,272 | 559 | 79,212 |

论文没有公开逐帧划分清单和随机种子，所以本轮数值不能描述为论文原划分的逐位重现。

## YOLOv10X 训练

- COCO 预训练 YOLOv10X；
- 31,660,658 个训练参数，论文报告 31.6M；
- 请求输入 1080，Ultralytics 按最大步长 32 自动补齐到 1088；
- batch 4、SGD、初始学习率 0.01、patience 10、seed 50；
- 硬件：NVIDIA GeForce RTX 4090 24 GB；
- 训练按 early stopping 自然结束于第 43 轮，最佳为第 33 轮。论文报告在其划分上实际训练 45 轮。

最佳验证集结果：

| epoch | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|---:|---:|---:|---:|---:|
| 33 | 0.9607 | 0.9025 | 0.9644 | 0.6558 |

## 固定测试集结果

| 范围 | Precision | Recall | F1 | AP50 / mAP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|---:|
| 整体 | 0.9455 | 0.9254 | 0.9353 | 0.9629 | 0.6374 |
| WB no pollen | 0.9746 | 0.9465 | 0.9603 | 0.9881 | 0.6716 |
| WB pollen | 0.8967 | 0.8937 | 0.8952 | 0.9317 | 0.6354 |
| Drone bee | 0.9650 | 0.9359 | 0.9502 | 0.9690 | 0.6053 |

测试集清单有 16,112 个原始框。Ultralytics 检出一个坐标完全相同的重复标签并在计分时自动删除，因此实际计分实例数为 16,111。数据审计仍保留论文口径的 79,212 个原始标注。

RTX 4090、batch 4 下，纯模型推理耗时为 6.248 ms/图，约 160.04 FPS，不包含读图、可视化和写盘。最佳权重 SHA-256 为：

```text
46e72c5b4eb13251a160a5a932616196226f18546f6116f0bea1cc9be4fbc407
```

## 与论文结果的关系

论文报告 YOLOv10X accuracy 93.9%、F1 0.92、Cohen's kappa 0.6105、速度 25.93 FPS。本轮标准检测 F1 为 0.9353，比论文数值高 0.0153，但由于逐帧划分未公开，不能把差异完全归因于模型。

论文把背景 TN 纳入 accuracy，却没有公开 TN 的构造和实现，无法可靠复算 accuracy 与 kappa。本项目报告标准目标检测 Precision、Recall、F1、AP50 和 mAP@0.5:0.95，不用 mAP 替代论文 accuracy。速度也受 GPU、CUDA、batch 和计时范围影响，不宜与论文的端到端 FPS 直接等价。

## 结论

本轮已经完整跑通第三篇论文 YOLOv10X 路线。官方数据规模与类别计数得到复核，最佳权重在固定测试集达到 F1 0.9353、mAP@0.5 0.9629、mAP@0.5:0.95 0.6374。无花粉工蜂 AP 最高；雄蜂的 mAP@0.5:0.95 最低，符合其训练样本仅 339 个且总数据仅 559 个的类别不平衡风险。

完整操作方法、断点续训方式和各文件用途见 `README.md`。机器可读指标见 `results/detector_metrics.json`，可下载版见 `reports/第三篇论文复现结果报告.pdf`。
