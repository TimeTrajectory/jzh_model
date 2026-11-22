# 蜜蜂论文复现项目

本目录只存放正式论文复现项目。各原始论文 PDF 保留在本地 `/jzk-model/pdf-paper/`。

| 序号 | 项目目录 | 主要内容 | 状态 |
|---|---|---|---|
| 01 | `bee-yolo-paper1-reproduction/` | 蜜蜂目标检测、评估、视频跟踪 | 已完成 |
| 02 | `bee-paper2-tracking-reproduction/` | BEE22、YOLOv5s、DeepSORT 与 MOT 评估 | 已完成 |
| 03 | `bee-paper3-colony-strength-reproduction/` | YOLOv10X、蜂群强度三类检测 | 已完成 |
| 04 | `bee-paper4-intellibeehive-reproduction/` | IntelliBeeHive、YOLOv7-tiny、蜂箱监测 | 已完成 |
| 05 | `bee-paper5-yolov4-deepsort-reproduction/` | Darknet YOLOv4、DeepSORT、进出越线计数 | 已完成 |
| 06 | `bee-paper6-stingless-monitoring-reproduction/` | YOLOv3-tiny、无刺蜂活动监测 | 已完成 |
| 07 | `bee-paper7-fanning-temporal-reproduction/` | 扇风蜂检测；RGB、TSG、TEM 时序编码对比 | 已完成首轮受控实验 |

第七篇论文项目固定 YOLO11n，三种输入方案均使用相同 Hive 划分。训练结果属于 Hive 4 验证表现，因为 Hive 4 用于早停与最佳权重选择，不是独立测试集。
