# 第五篇论文复现结果报告

论文：*Honeybee In-Out Monitoring System by Object Recognition and Tracking from Real-Time Webcams*（Ryu et al., 2021）。

## 复现性质

原论文自采 2,600 张受控单向通道图像未公开。本项目使用 BEE22 公开连续入口序列，复现 Darknet YOLOv4、DeepSORT、中央竖线方向计数和网页流程。作者结果与本地结果不可直接横向比较。

## 固定数据

- train：1,360 帧，16,050 框；
- val：240 帧，3,093 框；
- test：762 帧，12,205 框；
- 序列完全隔离；清单 SHA256：`14a789a5786f1862b8b3c9b70b04b92a7815038c8594af699a0ba3b73e0a9580`。

## 已完成的 DeepSORT 上限实验

真值框作为检测输入时：MOTA 0.9281、IDF1 0.8255、Recall 0.9397、142 次 ID 切换、736 个漏失，端到端 2.89 FPS。结果表明开放入口的身份关联仍然困难，也支持论文关于单向、单蜂通道可降低遮挡和交叉的工程判断。

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

## 结论边界

论文的 99.5% detection accuracy 未定义公式，本项目不会把它解释成 mAP。BEE22 的画面方向也不能自动解释为生物学进巢/出巢，除非确认相机朝向。
