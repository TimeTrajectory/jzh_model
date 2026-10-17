# 第三篇论文方法摘录

## 论文

Piyush Chaudhary 等，*Estimating colony strength and pollination efficiency in honey bees using a novel dataset and deep learning-based models*，Smart Agricultural Technology 14 (2026) 102005，DOI: 10.1016/j.atech.2026.102005。

## 数据

- 官方数据 DOI：10.54718/JCHW9401。
- 4,590 帧，来自 15 段蜂箱入口视频。
- 共 79,212 个边界框。
- 三类：无花粉工蜂、带花粉工蜂、雄蜂。
- 类别分布：无花粉工蜂 73,981（约 94%），带花粉工蜂 4,272（5.4%），雄蜂 559（0.7%）。
- 论文使用 60%/20%/20% 的训练、验证、测试划分，但没有公开具体帧清单和随机种子。

## YOLOv10X 设置

- 输入尺寸：1080 × 1080。
- batch：4。
- GPU：Tesla P100 16 GB。
- COCO 预训练。
- 优化器：SGD。
- 初始学习率：0.01。
- early stopping patience：10 epoch。
- 实际训练：45 epoch。
- 论文报告：accuracy 93.9%，F1 0.92，Cohen's kappa 0.6105，速度 25.93 FPS。

## 增强

- Motion blur 与 Gaussian blur：概率 0.25，最大核大小 (3, 7)。
- brightness/contrast limit：0.25，概率 1.0。
- horizontal flip：概率 0.4。
- rotate：概率 0.4；论文未给旋转角度范围。
- 保留边界框的随机裁剪：概率 0.3。

## 可复现性限制

论文没有给出具体 train/val/test 文件列表、随机种子、YOLOv10 代码提交版本、旋转角度范围和逐模型权重。项目会固定本地随机种子并输出文件清单与哈希，使本次实验自身可重复，但不能保证与作者的样本划分逐帧一致。

