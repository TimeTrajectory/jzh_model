# 第四篇论文复现结果报告

## 1. 复现对象

- 论文：*IntelliBeeHive: An Automated Honey Bee, Pollen, and Varroa Destructor Monitoring System*
- 原文：`/jzk-model/pdf-paper/2309.08955v1.pdf`
- 模型：YOLOv7-tiny
- 训练：416×416，batch 8，100 epochs，两套模型
- 日期：2026-10-31

## 2. 复现性质

作者原始数据、视频划分、源码和权重未公开。本项目用公开 Caltech Honeybee 训练检测模型，用 BEE22 诊断论文跟踪规则。结果属于公开替代数据复现，不与作者数值做严格等价比较。

论文的瓦螨训练数据是粘在死蜂上的 1.5 mm 红珠。项目保留这一事实，但没有训练或声称真实瓦螨检测。

## 3. 数据

- Caltech Honeybee 固定提交：`0a06fabcf23bbc75f03af4b028f8070bda8a2649`
- 87 个视频组，组级划分：61 train / 13 val / 13 test
- 图像：624 train / 178 val / 149 test
- 测试框：945 ordinary bee + 98 pollen-bearing bee
- manifest SHA-256：`484cdb6625edf9add3ab05313bb590b84a086518fd5c4693b22d68185ae88905`

## 4. 检测结果

| 任务/类别 | Precision | Recall | F1 | mAP@0.5 | mAP@0.5:0.95 |
|---|---:|---:|---:|---:|---:|
| 蜜蜂单类 | 0.930 | 0.862 | 0.895 | 0.905 | 0.512 |
| 两类总体 | 0.848 | 0.787 | 0.816 | 0.849 | 0.452 |
| ordinary bee | 0.922 | 0.871 | 0.896 | 0.920 | 0.527 |
| pollen-bearing bee | 0.775 | 0.704 | 0.738 | 0.778 | 0.377 |

携粉类别的 98 个测试框明显少于普通蜜蜂的 945 个，且目标属性更细。携粉类 Recall 0.704 是当前系统的主要短板，需要增加携粉样本、提高局部输入分辨率或采用检测后属性分类/局部检测。

## 5. 速度

RTX 4090、batch 8、416×416：

- 蜜蜂：3.7 ms 推理 + 1.2 ms NMS = 4.9 ms/图。
- 两类：4.1 ms 推理 + 1.2 ms NMS = 5.3 ms/图。

论文报告 Jetson Nano 原始约 56 ms/帧、TensorRT 约 27 ms/帧。硬件、运行时和批量不同，当前速度只证明代码可运行，不能证明 Jetson 速度已被复现。

## 6. 跟踪结果

论文规则：相邻帧中心点最近邻，640 px 宽下 50 px 容差；目标未匹配一帧即删除；上下三分之一为 Arriving/Leaving 触发线。

用 BEE22 真值框输入三段测试序列：

- 12,205 次关联分配。
- 加权轨迹纯度 0.9738。
- 199 次 ID 切换。
- Arriving 累计绝对计数误差 4。
- Leaving 累计绝对计数误差 26。

结论：规则具有可解释性并能处理简单运动，但会因快速运动、交叉、遮挡和一帧漏检产生轨迹碎片。高纯度不能替代 HOTA/IDF1 和碎片化指标。

## 7. 论文指标审校

- 原文 Recall 公式写成 `TP/(TP+True Negatives)`，数值实际使用 `TP/(TP+False Negatives)`。
- F1 排版公式的分母有误，后续数值计算使用 `P+R`。
- 跟踪章节把相对计数准确率称为 Error，并在公式中出现重复 `1−`，最终 96.28% 实际是各视频 Arriving/Leaving 相对计数准确率的平均。
- 蜜蜂 F1≈0.95 与 P/R=0.981 若来自同一阈值并不一致，可能来自不同置信度操作点。
- 检测曲线未报告 IoU、置信度、逐类支持数和独立测试协议。

## 8. 部署产物

两套最佳权重已导出：

- PyTorch `best.pt`
- TorchScript `best.torchscript.pt`
- TorchScript Lite `best.torchscript.ptl`
- ONNX `best.onnx`

ONNX 导出成功。TensorRT engine 需要在目标 Jetson/JetPack/TensorRT 环境构建并做数值一致性验证。

## 9. 最终判断

本轮完成了论文的核心模型、跟踪规则和部署链复现，并给出了实际训练结果。蜜蜂检测在公开替代测试集表现较好；携粉少数类仍有明显召回和定位差距；论文最近邻跟踪器可工作但身份连续性不足；真实瓦螨结论无法由红珠替代数据支持。

详细结果见 `reports/第四篇论文复现结果报告.pdf`，专业方法和写作分析见 Word 文档。

