# 蜜蜂视觉监测论文复现合集

本仓库用于按论文分别保存蜜蜂视觉监测与目标检测复现项目。每篇论文使用独立子目录，避免数据、权重、依赖和实验结果相互混淆。

## 项目目录

| 编号 | 论文复现项目 | 状态 |
|---|---|---|
| 01 | [bee-yolo-paper1-reproduction](./bee-yolo-paper1-reproduction/) | 已恢复源码并完成作者权重测试集核验 |
| 02 | [bee-paper2-tracking-reproduction](./bee-paper2-tracking-reproduction/) | 已完成 YOLOv5s 训练、独立测试和 DeepSORT 跟踪评估 |

后续论文继续使用独立目录：

```text
jzh_model/
├── README.md
├── bee-yolo-paper1-reproduction/
├── bee-paper2-tracking-reproduction/
└── bee-paper3-reproduction/
```

每个子项目单独保存自己的 `README.md`、依赖文件、训练脚本、评估脚本和结果说明。大型数据集、模型权重、虚拟环境和运行输出不直接提交到 GitHub，由各子项目的下载或训练脚本生成。
