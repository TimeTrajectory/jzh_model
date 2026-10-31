#!/usr/bin/env python3
"""Generate the two requested Word manuals and the reproduction PDF report."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image as RLImage
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
METRICS = json.loads((ROOT / "results/metrics_summary.json").read_text())
DOCS = ROOT / "docs"
REPORTS = ROOT / "reports"
ASSETS = ROOT / "assets"
DOCS.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True); ASSETS.mkdir(exist_ok=True)
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), fill); tc_pr.append(shd)


def set_cell_text(cell, text: str, bold: bool = False, color: str | None = None) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    r = p.add_run(str(text)); r.bold = bold; r.font.name = "微软雅黑"; r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    if color: r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("第 ")
    fld = OxmlElement("w:fldSimple"); fld.set(qn("w:instr"), "PAGE"); run._r.addnext(fld)
    paragraph.add_run(" 页")


def configure_document(title: str, subtitle: str) -> Document:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.2); section.bottom_margin = Cm(2.0); section.left_margin = Cm(2.5); section.right_margin = Cm(2.2)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "微软雅黑"; normal._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑"); normal.font.size = Pt(10.5)
    normal.paragraph_format.line_spacing = 1.45; normal.paragraph_format.space_after = Pt(6)
    for name, size, color in [("Title", 26, "17365D"), ("Subtitle", 14, "5B6573"), ("Heading 1", 18, "17365D"), ("Heading 2", 14, "2F5597"), ("Heading 3", 12, "4472C4")]:
        style = styles[name]; style.font.name = "微软雅黑"; style._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑"); style.font.size = Pt(size); style.font.color.rgb = RGBColor.from_string(color)
    if "Code Block" not in styles:
        code = styles.add_style("Code Block", WD_STYLE_TYPE.PARAGRAPH)
        code.font.name = "DejaVu Sans Mono"; code._element.rPr.rFonts.set(qn("w:eastAsia"), "文泉驿等宽正黑"); code.font.size = Pt(8.5)
        code.paragraph_format.left_indent = Cm(0.6); code.paragraph_format.right_indent = Cm(0.3); code.paragraph_format.space_before = Pt(4); code.paragraph_format.space_after = Pt(6)
    header = section.header.paragraphs[0]; header.text = title; header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header.runs[0].font.size = Pt(8); header.runs[0].font.color.rgb = RGBColor(120, 120, 120)
    add_page_number(section.footer.paragraphs[0])
    p = doc.add_paragraph(style="Title"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.add_run(title)
    p = doc.add_paragraph(style="Subtitle"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.add_run(subtitle)
    doc.add_paragraph("")
    meta = doc.add_table(rows=4, cols=2); meta.alignment = WD_TABLE_ALIGNMENT.CENTER; meta.style = "Table Grid"
    entries = [("对应论文", "IntelliBeeHive: An Automated Honey Bee, Pollen, and Varroa Destructor Monitoring System"), ("论文来源", "arXiv:2309.08955v1，2023-09-16；本项目按本地 PDF 分析"), ("项目位置", str(ROOT)), ("文档日期", "2026-10-31（Asia/Shanghai）")]
    for row, pair in zip(meta.rows, entries):
        set_cell_text(row.cells[0], pair[0], True, "FFFFFF"); set_cell_shading(row.cells[0], "2F5597"); set_cell_text(row.cells[1], pair[1])
    doc.add_page_break()
    return doc


def add_toc(doc: Document, entries: list[str]) -> None:
    doc.add_heading("目录（章节导航）", 1)
    for i, entry in enumerate(entries, 1):
        doc.add_paragraph(f"{i}. {entry}", style="List Number")
    doc.add_page_break()


def add_callout(doc: Document, label: str, text: str, color: str = "D9EAF7") -> None:
    table = doc.add_table(rows=1, cols=1); table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0); set_cell_shading(cell, color)
    p = cell.paragraphs[0]; r = p.add_run(f"{label}："); r.bold = True; r.font.color.rgb = RGBColor.from_string("17365D"); p.add_run(text)
    doc.add_paragraph("")


def add_table(doc: Document, headers: list[str], rows: list[list], widths=None) -> None:
    table = doc.add_table(rows=1, cols=len(headers)); table.style = "Table Grid"; table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, header in enumerate(headers): set_cell_text(table.rows[0].cells[i], header, True, "FFFFFF"); set_cell_shading(table.rows[0].cells[i], "2F5597")
    for row_data in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row_data): set_cell_text(cells[i], value)
    doc.add_paragraph("")


def add_code(doc: Document, code: str) -> None:
    table = doc.add_table(rows=1, cols=1); table.style = "Table Grid"; set_cell_shading(table.cell(0, 0), "F2F2F2")
    p = table.cell(0, 0).paragraphs[0]; p.style = doc.styles["Code Block"]
    p.add_run(code)
    doc.add_paragraph("")


def add_figure(doc: Document, path: Path, caption: str, width: float = 6.2) -> None:
    if not path.exists(): return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(str(path), width=Inches(width))
    c = doc.add_paragraph(caption); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; c.runs[0].italic = True; c.runs[0].font.size = Pt(9)


def make_metric_chart() -> Path:
    pollen = {x["class"]: x for x in METRICS["experiments"]["pollen"]["independent_test"]}
    bee = METRICS["experiments"]["bee"]["independent_test"][0]
    labels = ["蜜蜂检测", "普通蜜蜂", "携粉蜜蜂"]
    rows = [bee, pollen["ordinary_bee"], pollen["pollen_bearing_bee"]]
    x = range(len(labels)); width = 0.18
    cn_font = FontProperties(fname=FONT)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for offset, key, title, color in [(-1.5, "precision", "Precision", "#2F5597"), (-0.5, "recall", "Recall", "#70AD47"), (0.5, "f1", "F1", "#ED7D31"), (1.5, "map50", "mAP@0.5", "#A5A5A5")]:
        ax.bar([i + offset * width for i in x], [r[key] for r in rows], width, label=title, color=color)
    ax.set_ylim(0, 1.05); ax.set_ylabel("指标值", fontproperties=cn_font); ax.set_xticks(list(x), labels, fontproperties=cn_font); ax.grid(axis="y", alpha=.25); ax.legend(ncol=4, loc="upper center")
    ax.set_title("第四篇论文公开替代数据复现实测（独立测试集）", fontproperties=cn_font)
    fig.tight_layout(); path = ASSETS / "test_metrics_comparison.png"; fig.savefig(path, dpi=180); plt.close(fig); return path


def build_manual(metric_chart: Path) -> Path:
    title = "第四篇论文复现项目：VS Code 项目结构与训练操作手册"
    chapters = ["文档定位与复现边界", "项目目录总览", "VS Code 首次打开与解释器配置", "环境安装和数据准备", "论文方法与代码映射", "手动训练两套模型", "断点续训与参数调整", "独立测试、图片预测与视频监测", "本地网页演示", "ONNX 与 Jetson/TensorRT 部署", "结果目录和指标解读", "如何修改数据、类别、模型与权重", "常见故障排查", "完整复现实验记录", "命令速查表"]
    doc = configure_document(title, "面向自行训练、改代码、替换数据与部署的完整操作说明")
    add_toc(doc, chapters)
    doc.add_heading("1. 文档定位与复现边界", 1)
    doc.add_paragraph("本手册针对当前 VS Code 项目，目标是让读者从打开文件夹开始，独立完成环境配置、公开数据下载、YOLO 标注转换、双模型训练、测试、推理、视频越线计数、网页演示和 ONNX 导出。所有命令默认在项目根目录执行。")
    add_callout(doc, "关键边界", "原论文没有公开作者的 1235 张蜜蜂图、约 1000 张携粉蜜蜂图、约 700 张红珠“螨”图、训练/验证划分、最佳权重或完整源码。因此本项目属于“方法与工程流程复现 + 公开替代数据实测”，不能声称数值严格复现作者实验。")
    add_table(doc, ["层级", "本项目完成内容", "能否与论文直接比较"], [
        ["模型结构", "官方 YOLOv7-tiny、416×416、batch 8、100 epochs", "结构和主训练配置对齐"],
        ["蜜蜂检测", "Caltech Honeybee 两类框合并为 bee", "数据不同，不做同分布等价比较"],
        ["花粉任务", "普通蜜蜂/携粉蜜蜂入口场景检测", "论文在蜜蜂裁剪图上检测 pollen；任务定义不同"],
        ["瓦螨", "不训练、不宣称检测", "论文仅用 1.5 mm 红珠替代物，缺少真实有效性"],
        ["跟踪", "复现最近中点、50 px 容差、上下三分之一触发线", "规则对齐；用 BEE22 标签诊断关联能力"],
        ["部署", "PyTorch、TorchScript、ONNX；保留 TensorRT 操作接口", "TensorRT engine 必须在目标 Jetson 上构建"],
    ])

    doc.add_heading("2. 项目目录总览", 1)
    tree = """bee-paper4-intellibeehive-reproduction/
├── README.md / REPORT.md              项目入口与结果报告
├── setup.sh                            一键创建环境、下载和准备数据
├── download_assets.py                  固定版本下载 YOLOv7、Caltech 数据和预训练权重
├── prepare_dataset.py                  JSON→YOLO、按视频组划分、生成两套任务视图
├── run_experiments.py                  训练 bee / pollen 两套 YOLOv7-tiny
├── evaluate.py / collect_results.py    独立测试与结构化结果汇总
├── inference.py / predict.py           可复用推理封装与命令行预测
├── tracking.py                         论文最近中点跟踪器与触发线计数
├── evaluate_tracking.py                在 BEE22 真值框上诊断跟踪规则
├── monitor_video.py                    视频检测、跟踪、到达/离开/携粉计数
├── app.py                              Flask 本地图片检测网页
├── export_onnx.py                      最佳权重导出 ONNX
├── data/                               YAML、划分清单、小型统计；大图像被忽略
├── downloads/ / vendor/                原始数据和固定第三方源码；Git 忽略
├── runs/                               训练、测试、推理和权重；默认 Git 忽略
├── results/                            可审查指标、CSV、曲线和示例图
├── docs/                               两份 Word 文档
└── reports/                            PDF 复现结果报告"""
    add_code(doc, tree)
    add_table(doc, ["文件", "输入", "输出", "何时使用"], [
        ["prepare_dataset.py", "Caltech JSON+JPG", "YOLO 标签、硬链接图片、YAML、manifest", "首次准备或修改划分"],
        ["run_experiments.py", "YAML、官方预训练权重", "runs/train/.../best.pt", "训练或 --resume 续训"],
        ["evaluate.py", "best.pt、test YAML", "测试曲线、混淆矩阵、日志", "训练后固定测试"],
        ["tracking.py", "逐帧检测框", "轨迹状态、越线事件、计数", "视频监测核心"],
        ["monitor_video.py", "视频、pollen best.pt", "标注视频、CSV、JSON", "真实入口视频"],
        ["app.py", "上传图片", "浏览器检测图和类别计数", "交互演示"],
        ["collect_results.py", "训练/测试日志", "metrics_summary.json、CSV、可提交图", "更新报告前"],
    ])

    doc.add_heading("3. VS Code 首次打开与解释器配置", 1)
    for text in ["在 VS Code 选择“文件 → 打开文件夹”，打开本项目根目录，不能只打开某一个 .py 文件。", "按 Ctrl+Shift+P，运行 Python: Select Interpreter，选择 .venv/bin/python。", "选择“终端 → 新建终端”，确认提示符路径是项目根目录。", "运行下面的环境检查；若 cuda 为 True 且显示 NVIDIA GPU，则可用 GPU 训练。"]:
        doc.add_paragraph(text, style="List Number")
    add_code(doc, "source .venv/bin/activate\npython -c \"import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))\"\npython -c \"import pandas, cv2; print(pandas.__version__, cv2.__version__)\"")
    doc.add_paragraph("VS Code 的“运行 Python 文件”按钮适合短脚本；训练建议在集成终端运行，这样参数、日志、断点续训和错误堆栈都可见。")

    doc.add_heading("4. 环境安装和数据准备", 1)
    doc.add_heading("4.1 一键安装", 2); add_code(doc, "chmod +x setup.sh\n./setup.sh")
    doc.add_paragraph("脚本创建带系统 CUDA/PyTorch 的 .venv，安装 Python 依赖，下载固定提交的 YOLOv7 与 Caltech Honeybee，并生成训练数据。若已有环境，可分步执行。")
    doc.add_heading("4.2 分步执行", 2); add_code(doc, "python -m venv --system-site-packages .venv\nsource .venv/bin/activate\npip install -r requirements.txt\npython download_assets.py\npython prepare_dataset.py --clean")
    doc.add_heading("4.3 数据版本与划分", 2)
    add_table(doc, ["项目", "值"], [["Caltech 提交", "0a06fabcf23bbc75f03af4b028f8070bda8a2649"], ["YOLOv7 提交", "a207844b1ce82d204ab36d87d496728d3d2348e7"], ["随机种子", "2309"], ["分组规则", "frame id // 10000；组内帧不跨 train/val/test"], ["图像划分", "624 / 178 / 149"], ["测试框", "945 ordinary + 98 pollen-bearing = 1043"]])
    doc.add_paragraph("data/split_manifest.csv 是逐图审计清单；data/dataset_summary.json 记录统计、提交号和 manifest SHA-256。修改 seed 会改变划分，新的结果不能与本报告直接混合。")

    doc.add_heading("5. 论文方法与代码映射", 1)
    add_table(doc, ["论文模块", "论文实现", "本项目对应"], [
        ["蜜蜂检测", "YOLOv7-tiny，416，batch 8，100 epoch", "bee.yaml + run_experiments.py --task bee"],
        ["花粉/螨", "蜜蜂裁剪图，YOLOv7-tiny，64×64，两类", "pollen.yaml 入口场景两类；真实螨未复现"],
        ["个体跟踪", "相邻帧最近中点、50 px 容差", "tracking.IntelliBeeTracker"],
        ["方向统计", "Y=1/3、2/3 触发线；Arriving/Leaving/Deck", "monitor_video.py 与 evaluate_tracking.py"],
        ["边缘部署", "ONNX→TensorRT，Jetson Nano", "export_onnx.py；Jetson 上再构建 engine"],
        ["网页", "Laravel/MySQL/REST，5 分钟刷新", "本地 Flask 图片演示；生产数据库服务不伪造"],
    ])

    doc.add_heading("6. 手动训练两套模型", 1)
    doc.add_heading("6.1 蜜蜂单类检测", 2); add_code(doc, "python run_experiments.py --task bee --epochs 100 --batch 8 --workers 8")
    doc.add_heading("6.2 普通/携粉蜜蜂检测", 2); add_code(doc, "python run_experiments.py --task pollen --epochs 100 --batch 8 --workers 8")
    doc.add_heading("6.3 连续执行", 2); add_code(doc, "python run_experiments.py --task all --epochs 100 --batch 8 --workers 8")
    doc.add_paragraph("训练名称包含 epoch 数，例如 bee_yolov7_tiny_e100。脚本使用官方 cfg/training/yolov7-tiny.yaml 和 data/hyp.scratch.tiny.yaml，并从官方 yolov7-tiny.pt 迁移可匹配层。")
    add_table(doc, ["参数", "论文值/默认值", "调整建议", "影响"], [["--epochs", "100", "小数据可先 10 冒烟，再 100 正式", "影响训练时长和收敛"], ["--batch", "8", "显存不足改 4；显存充足仍建议保留 8 做对照", "改变优化噪声和可比性"], ["--workers", "8", "Windows 可先设 0 或 2", "只影响数据加载"], ["--device", "0", "CPU 用 cpu，多卡需改上游启动方式", "影响速度"], ["img-size", "416", "源码中可改为 640 做小目标实验", "提高细节与计算量"]])

    doc.add_heading("7. 断点续训与参数调整", 1)
    add_code(doc, "python run_experiments.py --task bee --epochs 100 --resume\npython run_experiments.py --task pollen --epochs 100 --resume")
    doc.add_paragraph("--resume 读取对应运行目录的 weights/last.pt。不要把 best.pt 当作断点文件：best.pt 用于推理和测试，last.pt 保留最后轮状态。若训练名称、epoch 数或目录被改动，应直接调用 vendor/yolov7/train.py --resume <last.pt>。")
    doc.add_paragraph("调学习率、Mosaic、颜色增强等参数时复制 vendor/yolov7/data/hyp.scratch.tiny.yaml 到项目 data/ 下，再修改 run_experiments.py 指向新文件。保留原文件和实验名，避免覆盖基线。")

    doc.add_heading("8. 独立测试、图片预测与视频监测", 1)
    add_code(doc, "python evaluate.py --task bee --epochs 100\npython evaluate.py --task pollen --epochs 100\npython collect_results.py")
    add_code(doc, "python predict.py --task pollen --source /绝对路径/图片或目录 --confidence 0.25")
    add_code(doc, "python monitor_video.py --source /绝对路径/hive.mp4 --output runs/video/hive_result.mp4 --confidence 0.25")
    doc.add_paragraph("视频命令输出同名 MP4、CSV 和 JSON。CSV 保存每帧检测数与累计 Arriving/Leaving/Pollen；JSON 保存最终计数和越线事件。入口方向必须与论文一致：画面上方为蜂箱内部、下方为外部；相反安装方向需交换状态命名。")
    add_callout(doc, "跟踪限制", "论文跟踪器只比较前一帧，目标漏检一帧就会生成新 ID；拥挤、交叉、快速运动会导致错误匹配。正式研究应增加 Kalman 预测、Hungarian/ByteTrack 关联、遮挡缓冲，并报告 HOTA/IDF1。", "FFF2CC")

    doc.add_heading("9. 本地网页演示", 1); add_code(doc, "python app.py\n# 浏览器打开 http://127.0.0.1:7860")
    doc.add_paragraph("网页支持上传图片、选择单类蜜蜂或普通/携粉模型、调整置信度并显示框和计数。它用于本地学习与演示，不等同于论文的 Laravel/MySQL/REST 多蜂箱生产平台。")

    doc.add_heading("10. ONNX 与 Jetson/TensorRT 部署", 1)
    add_code(doc, "python export_onnx.py --task bee --epochs 100\npython export_onnx.py --task pollen --epochs 100")
    doc.add_paragraph("导出得到 best.onnx，输入固定为 1×3×416×416。可用 Netron 检查图结构。论文在 Jetson Nano 上把 ONNX 转为 TensorRT 后将单帧约 56 ms 降至约 27 ms；该数字来自作者硬件和软件栈。")
    add_table(doc, ["部署步骤", "操作重点"], [["1. 对齐 JetPack", "Jetson Nano 通常使用 JetPack 4.6；TensorRT/CUDA/驱动必须配套"], ["2. 复制 ONNX", "只复制已验证的 best.onnx 与类别文件"], ["3. 构建 engine", "必须在目标 Jetson 或完全兼容环境执行；设置 FP16 前先验证精度"], ["4. 校验数值", "同一组图对比 PyTorch 与 TensorRT 框、类别和置信度"], ["5. 测性能", "记录预处理、推理、NMS、跟踪、I/O 的分项延迟与功耗"], ["6. 长期运行", "测试温度、掉帧、磁盘、断网重连和服务自动恢复"]])

    doc.add_heading("11. 结果目录和指标解读", 1)
    add_figure(doc, metric_chart, "图 1  独立测试集指标对比")
    add_table(doc, ["任务/类别", "P", "R", "F1", "mAP@0.5", "mAP@0.5:0.95"], [["蜜蜂", "0.930", "0.862", "0.895", "0.905", "0.512"], ["普通蜜蜂", "0.922", "0.871", "0.896", "0.920", "0.527"], ["携粉蜜蜂", "0.775", "0.704", "0.738", "0.778", "0.377"], ["两类宏观", "0.848", "0.787", "0.816", "0.849", "0.452"]])
    doc.add_paragraph("Precision 高表示误报少；Recall 高表示漏报少；F1 是 P/R 的调和平均；mAP@0.5 衡量 IoU≥0.5 的检测；mAP@0.5:0.95 对定位更严格。论文只给出若干 F1/PR 曲线读数，没有 mAP、IoU 阈值和置信度操作点，本项目补充这些指标但不做直接等价比较。")

    doc.add_heading("12. 如何修改数据、类别、模型与权重", 1)
    for heading, body in [
        ("替换为自己的蜂箱视频", "先按固定间隔抽帧，用 LabelImg/Label Studio 标注 YOLO 框。按拍摄日期、蜂箱或视频分组划分，不能随机打散连续帧。修改 prepare_dataset.py 或直接建立 images/{train,val,test} 与 labels/{...}。"),
        ("增加真实瓦螨类别", "只接受真实螨体框和明确的专家复核标准。建议采用两阶段：先检测蜜蜂，再在高分辨率蜂体裁剪上检测/分割螨。names 增加 varroa 后重新训练；红珠结果必须标为合成替代实验。"),
        ("调整类别", "data/*.yaml 的 nc 与 names 必须一致，所有 label 第一列必须落在 0..nc-1。类别变更后不能加载旧模型检测头作为最终结果。"),
        ("更换模型", "修改 run_experiments.py 的 --cfg 和 --weights。必须重新测速度、显存和独立测试指标，不能只比较参数量。"),
        ("管理权重", "best.pt 用于测试/推理，last.pt 用于续训，官方 yolov7-tiny.pt 只作初始化，best.onnx 用于部署。记录 SHA-256、训练数据 manifest 和代码提交。"),
    ]:
        doc.add_heading(heading, 2); doc.add_paragraph(body)

    doc.add_heading("13. 常见故障排查", 1)
    add_table(doc, ["现象", "原因", "处理"], [["Dataset not found", "旧 YOLOv7 不识别新版 path: YAML", "使用 prepare_dataset.py 生成的绝对路径 YAML"], ["CUDA out of memory", "batch/图像过大", "batch 8→4→2；关闭其他 GPU 进程"], ["Windows 多进程报错", "dataloader worker 兼容", "--workers 0"], ["pandas.util.version 缺失", "系统 pandas 安装损坏", "在 .venv 内 pip install pandas==2.2.3"], ["找不到 best.pt", "未训练或运行名不一致", "检查 runs/train/<task>_yolov7_tiny_e100/weights"], ["ONNX 缺包", "未装 onnx", "pip install onnx==1.17.0"], ["视频计数方向反了", "摄像机方向与论文相反", "交换 Arriving/Leaving 定义或旋转视频"], ["携粉召回低", "类别不平衡、目标小、域偏移", "补充携粉样本、提高分辨率、按蜂箱分层验证"]])

    doc.add_heading("14. 完整复现实验记录", 1)
    add_table(doc, ["项目", "实测"], [["GPU", "NVIDIA GeForce RTX 4090"], ["PyTorch", "2.1.2+cu121"], ["训练", "两模型各 100 epochs，416×416，batch 8"], ["蜜蜂最佳验证 epoch", "zero-based 96"], ["携粉最佳验证 epoch", "zero-based 97"], ["RTX 4090 测试速度", "蜜蜂 4.9 ms/图；两类 5.3 ms/图（含 NMS，batch 8）"], ["跟踪诊断", "3 序列，12205 次分配，纯度 0.9738，199 次 ID 切换；越线绝对误差 Arriving 4 / Leaving 26"]])
    doc.add_paragraph("跟踪纯度高并不等于轨迹连续：预测轨迹可以被频繁切碎，同时每个碎片内部仍保持单一真值 ID。199 次 ID 切换和 Leaving 漏计说明简单最近邻规则对速度、拥挤和短时丢失敏感。")

    doc.add_heading("15. 命令速查表", 1)
    add_code(doc, """# 安装与数据
./setup.sh
python prepare_dataset.py --clean

# 训练与续训
python run_experiments.py --task all --epochs 100 --batch 8
python run_experiments.py --task bee --epochs 100 --resume

# 测试和汇总
python evaluate.py --task bee --epochs 100
python evaluate.py --task pollen --epochs 100
python evaluate_tracking.py
python collect_results.py

# 推理、视频、网页、导出
python predict.py --task pollen --source sample.jpg
python monitor_video.py --source hive.mp4
python app.py
python export_onnx.py --task bee --epochs 100""")
    path = DOCS / "第四篇论文_VSCode项目结构与训练操作手册.docx"; doc.save(path); return path


def build_analysis(metric_chart: Path) -> Path:
    title = "IntelliBeeHive 论文专业深度解析与论文写作评析"
    chapters = ["论文信息与分析框架", "研究问题、应用背景与科学假设", "贡献结构与系统总览", "硬件与成像通道设计", "数据采集、标注与样本有效性", "YOLOv7-tiny 双模型方法", "最近中点跟踪与状态机", "花粉与瓦螨分析链", "网站、数据库与 REST 架构", "实验设计与指标重建", "实验结果和结论边界", "创新性分层评价", "内部、外部与统计有效性", "复现结果与差异解释", "论文写作的优秀之处", "论文写作与报告规范的不足", "可发表级改进方向", "推荐实验矩阵与统计方案", "专业读者的最终判断"]
    doc = configure_document(title, "面向研究人员：方法、实验、有效性、创新与写作方法的系统评析")
    add_toc(doc, chapters)
    doc.add_heading("1. 论文信息与分析框架", 1)
    add_table(doc, ["字段", "内容"], [["题目", "IntelliBeeHive: An Automated Honey Bee, Pollen, and Varroa Destructor Monitoring System"], ["作者", "Christian I. Narcia-Macias 等；本地 arXiv v1 列 6 位作者"], ["版本", "arXiv:2309.08955v1，16 Sep 2023"], ["领域", "计算机视觉、嵌入式系统、目标跟踪、智慧蜂业"], ["核心对象", "蜂箱入口蜜蜂流量、携粉活动、瓦螨替代物、环境与设备状态"], ["分析材料", "本地 16 页原论文 PDF + 本项目公开替代数据复现实测"]])
    add_callout(doc, "标记规则", "“论文事实”只复述原文；“复现实测”来自本项目；“方法批判”是基于证据的评价；“改进建议”属于未来方案。四类内容不混写。")

    doc.add_heading("2. 研究问题、应用背景与科学假设", 1)
    doc.add_paragraph("论文从三个蜂群管理痛点建立研究动机：人工开箱和传统计数成本高；花粉陷阱会移除蜂粮且捕获效率有限；糖滚、酒精洗与黏板等瓦螨检测方式需要人工并可能具有破坏性。作者将入口视觉通道视为一个低干扰观测点，希望同时获得流量、觅食和寄生风险代理变量。")
    add_table(doc, ["问题层", "隐含假设", "需要的证据"], [["检测", "入口画面可稳定识别完整蜜蜂", "跨光照/季节/蜂箱的检测测试"], ["行为", "上下方向越线可代表进入和离开", "轨迹身份、方向真值、重复计数分析"], ["觅食", "携粉蜜蜂计数可反映花粉采集活动", "与人工计数/花粉重量/植物来源的关联"], ["健康", "可见瓦螨能代表蜂群感染水平", "真实螨数据、敏感度/特异度、与标准洗检的校准"], ["部署", "Jetson Nano 可在采集间隔内完成处理", "端到端延迟、功耗、温度、掉帧与长期稳定性"]])
    doc.add_paragraph("论文真正验证得较充分的是“在单一装置和有限视频中可检测并统计入口蜜蜂与携粉个体”。从入口计数推断蜂群健康、从可见螨推断感染率，还需要生物学标定和跨场地验证。")

    doc.add_heading("3. 贡献结构与系统总览", 1)
    doc.add_paragraph("该工作的主要贡献是系统集成：成像通道、Jetson 边缘推理、两个 YOLOv7-tiny 模型、规则跟踪、环境传感器、PoE 网络、REST API、MySQL 数据库和面向养蜂人的网站。算法组件大多采用已有方法，创新重心位于低成本、非侵扰、端云协同和可操作的业务闭环。")
    add_table(doc, ["层", "组件", "数据流"], [["物理层", "3D 打印箱体、钓鱼线网格、磨砂亚克力、木质底板", "约束蜜蜂通行、减少重叠与反光"], ["采集层", "Raspberry Pi Camera V2.1、BME680、10 fps 视频", "1280×720 采集，保存/处理为约 640×420"], ["边缘智能", "Jetson Nano、YOLOv7-tiny、TensorRT", "5 分钟视频批处理，下一段同步录制"], ["行为层", "最近中点关联、双触发线、尺寸估计", "Arriving/Leaving/Deck/New、平均尺寸"], ["服务层", "Laravel、MySQL、REST", "上传环境、视频、网络与活动数据"], ["交互层", "账户、图表、表格、权限", "5 分钟更新；年度数据按小时抽样展示"]])
    add_callout(doc, "方法批判", "论文将‘实时’表述为约 5 分钟延迟的周期批处理，更准确的工程术语是 near-real-time。这个差别影响系统需求、吞吐预算和事件响应解释。", "FFF2CC")

    doc.add_heading("4. 硬件与成像通道设计", 1)
    doc.add_paragraph("作者选择 Jetson Nano 的理由是当时约 99 美元、具备 GPU 推理能力，优于 Raspberry Pi 独立执行实时视觉。箱体分为 Top Box、Camera Room 和 Mesh Frame，摄像机距通道约 155 mm，视场约 150×80 mm；后续尺寸换算使用约 110×65 mm 的工作区域。钓鱼线网格限制蜜蜂接近镜头并降低个体重叠，磨砂亚克力降低太阳反光，木底板提供中性背景。")
    doc.add_paragraph("这是论文写作中较好的“设计决策—约束—结果”链：不是只列硬件，而是说明每个部件如何改善视觉可观测性。但视场数字在不同段落出现 150×80 mm 与 110×65 mm，未解释两者分别是物理窗口、有效区域还是标定区域；尺寸估计缺少相机内参、透视校正和误差传播。")
    add_table(doc, ["潜在误差", "机制", "改进"], [["透视缩放", "不同位置像素/毫米比例不同", "平面单应性标定或相机模型"], ["姿态偏差", "最长框边随蜜蜂旋转变化", "关键点/分割主轴长度"], ["反光与阴影", "自然光跨时段变化", "遮光、偏振、HDR、颜色校准"], ["运动模糊", "10 fps 下快速蜜蜂模糊", "更短曝光、更高帧率、补光"], ["网格遮挡", "钓鱼线仍会切割目标", "遮挡增强和网格位置标定"]])

    doc.add_heading("5. 数据采集、标注与样本有效性", 1)
    doc.add_paragraph("论文采集约 50 段、每段 5 分钟、10 fps、1280×720 的视频，跨 4 天和不同光照；每 3 秒抽一帧。蜜蜂检测集含 1235 张图、约 9700 个蜜蜂框，只标注身体大部分可见的个体。此标注政策服务于稳定跟踪，但改变了任务定义：边缘部分个体被有意当作背景，模型的‘漏检’不能直接解释为真实流量漏计。")
    doc.add_paragraph("花粉数据来自作者视频中筛选的约 1000 个携粉蜜蜂裁剪图。瓦螨数据由于缺少真实螨，使用黏在死蜂上的 1.5 mm 不透明红珠，约 700 张。这是一个装置可检测性原型，而不是瓦螨诊断数据。颜色、纹理、附着位置、体积、光泽、活体姿态和背景关系均与真实 Varroa destructor 不同。")
    add_callout(doc, "外部有效性结论", "论文的 mite 高指标只能支持‘系统能检测红色珠状替代物’，不能支持‘系统能以相同准确率检测真实瓦螨’，更不能支持蜂群感染率诊断。作者在结果和讨论中承认该限制，这是负责任的表述，但摘要中的“detect Varroa mites”仍容易被过度解读。", "FCE4D6")
    doc.add_paragraph("论文未报告按原始视频、日期或蜂箱分组的 train/validation/test 划分。连续视频帧具有强相关性；若随机按图划分，背景、个体和光照近重复会导致数据泄漏。专业复现应以视频/日期/蜂箱为组，并保留完全未见场地测试。")

    doc.add_heading("6. YOLOv7-tiny 双模型方法", 1)
    doc.add_paragraph("模型 A 在 416×416 输入上检测单类 Honey bee，batch 8、100 epochs、RTX 3070 训练。模型 B 在蜜蜂裁剪上检测 Pollen/Mite，论文称输入为 64×64，其他训练参数相同。两者均从 PyTorch 导出 ONNX，再在 Jetson Nano 生成 TensorRT engine。模型 A 原始推理约 56 ms/帧，TensorRT 后约 27 ms/帧。")
    doc.add_paragraph("双阶段设计的工程逻辑是先在全场景定位蜜蜂，再仅在触发线附近保存完整蜂体裁剪，视频处理结束后批量执行花粉/螨推理。这减少了第二模型的输入区域和运行次数，也提高微小属性的相对像素占比。")
    add_table(doc, ["设计", "优势", "风险"], [["YOLOv7-tiny", "适合边缘设备，速度与精度折中", "缺少与其他轻量模型同数据比较"], ["两模型串联", "分离场景检测与局部属性", "第一阶段漏检无法被第二阶段恢复"], ["触发线才保存裁剪", "降低重复推理、选择完整蜂体", "错误轨迹或未越线个体无属性结果"], ["64×64 局部输入", "吞吐高", "对真实 1–2 mm 螨体细节可能过度压缩"], ["TensorRT", "作者报告近 2× 加速", "未报告精度漂移、FP16/INT8、预后处理延迟"]])

    doc.add_heading("7. 最近中点跟踪与状态机", 1)
    doc.add_paragraph("每个检测框以中心点 X=(maxX−minX)/2+minX、Y=(maxY−minY)/2+minY 表示。第 n 帧中心与第 n−1 帧所有活动 profile 比较，在任意方向 50 px 容差内优先最近者；未匹配检测创建新 profile，当前帧未匹配的旧 profile 立即删除。")
    doc.add_paragraph("在 640×420 画面中，Y=140 和 Y=280 为触发线。中心由下向上越过 140 记为 Arriving，由上向下越过 280 记为 Leaving，反向越线回到 Deck。New 表示尚未越线。最长框边经像素/毫米比例换算为尺寸，只在越线时记录，以提高完整可见概率。")
    add_table(doc, ["跟踪假设", "失效情形", "后果"], [["相邻帧位移 <50 px", "飞行快、帧率低", "轨迹断裂、重复计数"], ["最近目标就是同一只蜂", "交叉、拥挤、相似距离", "ID 交换、方向错误"], ["漏检不超过 0 帧", "遮挡、模糊、置信度波动", "旧 profile 立即消失"], ["固定水平线适合所有画面", "相机旋转、入口几何变化", "方向语义失真"], ["框长边代表体长", "姿态旋转、部分出框", "工蜂/雄蜂尺寸混叠"]])
    add_callout(doc, "复现实测", "在 BEE22 三个测试序列用真值框隔离检测误差后，12205 次分配的加权轨迹纯度为 0.9738，但发生 199 次 ID 切换；越线绝对误差累计 Arriving=4、Leaving=26。高纯度与高碎片化可同时存在，证明只报告计数准确率不足以评价跟踪。")

    doc.add_heading("8. 花粉与瓦螨分析链", 1)
    doc.add_paragraph("论文在每个 profile 越过任一触发线时保存一张蜂体图，待蜜蜂模型处理完整段视频后再加载 Pollen/Mite TensorRT engine 批量分析。输出以 P+置信度等形式叠加。5 段 5 分钟视频的携粉人工/算法计数分别为 23/22、21/14、10/6、7/7、15/15，并给出 FP/FN。")
    add_table(doc, ["视频", "TP", "FP", "FN", "P", "R", "F1"], [["1", "19", "3", "4", "0.8636", "0.8261", "0.8444"], ["2", "13", "1", "8", "0.9286", "0.6190", "0.7428"], ["3", "6", "1", "4", "0.8571", "0.6000", "0.7059"], ["4", "7", "0", "0", "1.0000", "1.0000", "1.0000"], ["5", "13", "2", "2", "0.8667", "0.8667", "0.8667"], ["作者算术平均", "—", "—", "—", "0.9032", "0.7823", "0.8319"]])
    doc.add_paragraph("这里使用按视频算术平均，而不是将全部 TP/FP/FN 汇总后的微平均；视频 4 样本仅 7 个且完美结果会显著抬高宏平均。专业报告应同时给出 micro/macro、置信区间和每视频样本量。")

    doc.add_heading("9. 网站、数据库与 REST 架构", 1)
    doc.add_paragraph("网站使用 Linux VM、PHP Laravel、MySQL 和 REST API，区分 all/registered/admin 三类用户。主要操作为 getData、uploadData、uploadVideo、uploadNetwork。监测端通过 POST 上传环境、视频和网络信息，浏览器通过 GET 每 5 分钟刷新。系统展示温度、湿度、CPU/GPU 温度、Deck/Leaving/Arriving、平均尺寸、花粉和螨计数。")
    doc.add_paragraph("单蜂箱每个指标按 5 分钟采样一年约 105120 点，网站为减轻负载只取每小时数据，约 8760 点。论文把工程可扩展性问题量化，写作上很好；但没有说明小时数据是抽样、均值、最大值还是聚合计数。对流量计数，直接抽一个点和按小时求和的语义完全不同。")
    add_table(doc, ["系统设计问题", "专业改进"], [["每个蜂箱独立 Activity 表", "统一时序事实表，hive_id+timestamp 索引或时序数据库"], ["每小时降采样语义不明", "为连续变量取均值/范围，为事件计数求和，并保留原始层"], ["身份与认证描述较粗", "密码哈希、token 生命周期、密钥轮换、速率限制、审计日志"], ["视频上传成本", "事件片段/缩略图、对象存储、保留策略"], ["无离线缓冲说明", "Jetson 本地队列、幂等上传、断网补传"], ["无多租户隔离评估", "蜂场/用户访问控制与数据所有权模型"]])

    doc.add_heading("10. 实验设计与指标重建", 1)
    doc.add_paragraph("论文给出蜜蜂模型 F1≈0.95，Precision/Recall 曲线值 0.981；Pollen/Mite 模型 F1≈0.95，Pollen 0.821、Mite 0.996；跟踪计数准确率 96.28%；五视频携粉平均 F1=0.8319。检测曲线缺少置信度阈值、IoU、独立测试集、类别支持数和 mAP，因此不能判断这些值是否在同一操作点。")
    add_callout(doc, "公式审校", "论文把 Recall 的公式排成 TP/(TP+True Negatives)，正确式应为 TP/(TP+False Negatives)，但数值计算使用了 FN；F1 的排版公式分母也有异常，后续数值使用 P+R。跟踪部分把 1−|A−M|/M 得到的值称作 Error，又再次写 1−Error，符号与最终计算不一致。最终 96.28% 实际是各视频 Arriving/Leaving 相对计数准确率的平均。", "FCE4D6")
    doc.add_paragraph("若 P=R=0.981，则 F1 也应约为 0.981，而不是 0.95。最可能的解释是 0.981 与 F1=0.95 来自曲线上不同置信度点。论文应明确操作阈值，或报告最大 F1 对应的 P、R、阈值。")
    add_table(doc, ["指标", "能回答什么", "不能回答什么"], [["检测 F1", "选定阈值下误报/漏报平衡", "跨阈值性能、框定位严格度"], ["mAP@0.5", "宽松 IoU 下 PR 曲线面积", "精细定位和实际计数误差"], ["mAP@0.5:0.95", "多 IoU 阈值定位质量", "轨迹身份连续性"], ["计数准确率", "总进入/离开数接近程度", "同一只蜂是否跟对、误差是否相互抵消"], ["IDF1/HOTA", "身份和检测联合质量", "业务级健康关联"], ["敏感度/特异度", "真实螨诊断能力", "感染率估计的校准性"]])

    doc.add_heading("11. 实验结果和结论边界", 1)
    doc.add_paragraph("作者的系统级结论是：在所构建入口装置与有限视频上，蜜蜂活动可被近实时采集和处理；跟踪计数与人工总数较接近；携粉检测具有可用但不均匀的表现；真实瓦螨尚未得到验证；网站能持续展示环境和活动数据。")
    doc.add_paragraph("96.28% 来自 5 段各 1 分钟视频，且只比较 Arriving/Leaving 汇总数，排除 New，Deck 差异也未进入主准确率。样本窗口短、场景单一、无置信区间。该结果可以作为系统原型验证，不能推断跨季节、跨蜂箱的长期准确率。")
    doc.add_paragraph("作者讨论明确提出真实螨数据、夜视摄像机和全球多地部署，这是合适的限制—未来工作连接。但夜间蜜蜂活动较低，不代表夜视必然是最优投资；真实螨、跨域验证、持续运行可靠性和诊断校准的优先级更高。")

    doc.add_heading("12. 创新性分层评价", 1)
    add_table(doc, ["创新层", "评价", "依据"], [["算法创新", "较弱", "YOLOv7-tiny、最近邻跟踪、REST/MySQL 均为已有技术"], ["系统创新", "强", "把入口通道、边缘推理、环境感知、端云数据与养蜂界面组成闭环"], ["任务创新", "中强", "单装置统一流量、携粉、寄生代理与环境监测"], ["工程创新", "中强", "通道几何、TensorRT、录制/处理流水、PoE 与远程维护"], ["科学验证创新", "有限", "短视频与替代螨限制了生态和诊断结论"]])
    doc.add_paragraph("专业评价不应因为使用现成 YOLO 而否定工作。应用系统论文的贡献可以来自约束建模、物理通道设计、系统吞吐、部署可靠性和数据闭环。但论文需要用更严密的对照实验证明每个设计选择的增益。")

    doc.add_heading("13. 内部、外部与统计有效性", 1)
    add_table(doc, ["有效性", "主要威胁", "影响", "缓解"], [["内部", "连续帧可能跨划分", "测试指标偏高", "视频/日期/蜂箱分组"], ["内部", "检测与跟踪联合评估", "不能定位误差来源", "真值框跟踪、检测框跟踪分别测"], ["构念", "红珠替代真实螨", "测到颜色/形状代理", "真实螨专家标注"], ["构念", "总计数准确率代替跟踪质量", "ID 交换被隐藏", "HOTA/IDF1/轨迹碎片"], ["外部", "单装置/单地点/4 天", "跨场景泛化未知", "多蜂场、多季节、留一场地验证"], ["统计", "5 段短视频，无区间", "结果不确定性未知", "bootstrap CI、分层混合效应模型"], ["生态", "视觉计数未与蜂群健康终点关联", "健康解释过强", "与巢脾、蜂群强度、标准螨检验纵向关联"]])

    doc.add_heading("14. 复现结果与差异解释", 1)
    add_figure(doc, metric_chart, "图 1  本项目公开替代数据独立测试指标")
    add_table(doc, ["实验", "P", "R", "F1", "mAP@0.5", "mAP@0.5:0.95"], [["蜜蜂单类", "0.930", "0.862", "0.895", "0.905", "0.512"], ["两类总体", "0.848", "0.787", "0.816", "0.849", "0.452"], ["普通蜜蜂", "0.922", "0.871", "0.896", "0.920", "0.527"], ["携粉蜜蜂", "0.775", "0.704", "0.738", "0.778", "0.377"]])
    doc.add_paragraph("差异来自数据、任务定义与评估协议。本项目用 Caltech 入口全图将个体直接分为 ordinary/pollen-bearing；论文第二模型在已裁剪蜂体上检测 Pollen/Mite。全图任务的携粉目标相对更小，且训练集仅 463 个携粉框，因此携粉 F1 0.738 不应与论文五视频 F1 0.8319 视为同一基准。")
    doc.add_paragraph("本项目通过视频组划分保留 149 张独立测试图，报告 mAP 与逐类别指标。蜜蜂单类 F1 0.895 低于作者约 0.95，但公开数据包含不同入口、光照和标注政策；这一差距不能解释为实现失败或作者模型更优，只能说明不同实验分布下的结果。")

    doc.add_heading("15. 论文写作的优秀之处", 1)
    strengths = [
        ("动机具有业务闭环", "从人工、破坏性和营养损失切入，再落到非侵扰入口监测，使读者知道系统为何必要。"),
        ("系统叙事完整", "硬件、软件、跟踪、网站和结果都有独立章节，读者能从传感器追踪到网页指标。"),
        ("工程约束量化", "给出摄像距离、视场、帧率、分辨率、视频长度、单帧延迟和年度数据点数。"),
        ("设计决策有理由", "Jetson、钓鱼线、磨砂亚克力、下采样、TensorRT、批处理流水线均说明原因。"),
        ("图示密集且服务理解", "装置、触发线、跟踪点、数据库、REST 流程和网页结果以图支撑。"),
        ("限制披露", "明确承认螨使用替代物、尺寸估计受角度影响、最近邻在快速运动时失配。"),
        ("结果落到使用者", "指标不止是模型 AP，还连接到进入/离开、花粉、温湿度和网页历史趋势。"),
    ]
    for h, b in strengths: doc.add_heading(h, 2); doc.add_paragraph(b)
    doc.add_paragraph("学习其写法时，可采用“痛点 → 现有方法代价 → 系统需求 → 设计选择 → 可测指标 → 使用场景”的段落链。每一个硬件或算法选择都回答‘为什么是它、受什么约束、如何验证’。")

    doc.add_heading("16. 论文写作与报告规范的不足", 1)
    add_table(doc, ["问题", "表现", "建议写法"], [["贡献不够聚焦", "引言末没有编号贡献列表", "列出装置、算法流水、部署和数据服务四项可验证贡献"], ["相关工作偏叙述", "缺少对照表和明确研究空白", "按任务/硬件/数据/指标比较并给出本工作定位"], ["实验细节缺失", "无划分、阈值、优化器、学习率、种子", "单列 Reproducibility Setup 表"], ["检测指标含糊", "F1 与 P/R 可能来自不同阈值", "报告阈值、IoU、PR/AP 和逐类支持数"], ["公式和术语错误", "Recall、F1、Error/Accuracy 符号不一致", "公式编号后做量纲和数值单元检查"], ["系统结果缺基线", "没有 YOLO/跟踪/部署替代方案比较", "加入模型、跟踪器、分辨率和量化消融"], ["主张略超证据", "摘要称检测 Varroa", "写为 surrogate-mite feasibility，真实螨待验证"], ["数据可复现性不足", "无代码、权重和数据链接", "公开匿名数据、标注规范、提交号和模型卡"]])
    doc.add_paragraph("论文写作的专业性不只取决于英文表达。指标定义、实验单位、操作阈值、划分规则和结论边界决定读者能否验证论证链。该文的系统描述较强，实验报告规范是最需要加强的部分。")

    doc.add_heading("17. 可发表级改进方向", 1)
    improvements = [
        ("真实瓦螨两阶段检测与诊断校准", "建立真实活蜂螨数据，记录蜂体位置、螨框/掩膜、拍摄条件和专家一致性。先检测蜂体，再用高分辨率检测器/分割器定位螨；与酒精洗或糖滚的蜂群级感染率做 Bland–Altman、敏感度/特异度和校准曲线。"),
        ("统一多任务视觉模型", "共享骨干同时预测蜂体框、携粉属性、姿态/朝向和螨体关键区域，减少两模型重复计算。用任务不确定性加权或动态损失平衡，并与串联系统比较精度、延迟和能耗。"),
        ("面向小目标的多尺度与超分辨率", "对花粉和螨使用高分辨率 crop、切片推理、P2 检测头、注意力或局部放大；按像素尺寸分层报告 AP_small，并做 64/128/256 crop 消融。"),
        ("鲁棒多目标跟踪", "用 ByteTrack/BoT-SORT 或 Kalman+Hungarian，保留短时丢失轨迹，引入方向和速度门控。报告 HOTA、IDF1、ID switches、fragmentation 和越线 MAE。"),
        ("跨域泛化与持续学习", "按蜂场留一验证；研究光照、箱体、相机、季节和蜂种域移。使用风格增强、域适应、测试时适配，并加入漂移检测和人工复核队列。"),
        ("不确定性与风险控制", "输出校准置信度、拒识率和低质量帧标记。对螨诊断采用高召回筛查+人工确认，避免把模型输出直接当治疗决策。"),
        ("边缘端联合优化", "比较 FP32/FP16/INT8、稀疏化和蒸馏，测端到端延迟、功耗、温升与精度漂移。用事件驱动裁剪替代全帧持续推理。"),
        ("多模态蜂群数字孪生", "把流量、花粉、温湿度、重量、声学和天气合并，建立时序异常检测与预测模型。健康终点由独立蜂群检查提供，避免把视觉代理变量等同于健康。"),
    ]
    for h, b in improvements: doc.add_heading(h, 2); doc.add_paragraph(b)

    doc.add_heading("18. 推荐实验矩阵与统计方案", 1)
    add_table(doc, ["研究问题", "自变量", "因变量", "最低对照"], [["模型选择", "YOLOv7-tiny / YOLOv8n / RT-DETR 小型", "AP、F1、延迟、功耗", "相同数据、划分、输入和阈值选择规则"], ["分辨率", "416/640；crop 64/128/256", "AP_small、召回、吞吐", "固定模型和训练预算"], ["跟踪", "最近邻/ByteTrack/BoT-SORT", "HOTA、IDF1、越线 MAE", "真值框与检测框两种输入"], ["域泛化", "蜂场/季节/相机", "留一域 AP 与误差", "随机图像划分作为偏乐观参照"], ["量化", "FP32/FP16/INT8", "精度差、端到端 ms、W", "同一 Jetson 与热稳态"], ["健康效度", "视觉螨率/流量/花粉", "标准螨检验、蜂群强度", "纵向重复测量"]])
    doc.add_paragraph("统计上以视频或蜂箱作为独立实验单位，而不是把每一帧视为独立样本。检测指标用分组 bootstrap 95% CI；多蜂箱纵向数据用混合效应模型，将蜂箱设为随机效应，日期、天气和季节作为协变量。多模型比较应预先指定主指标并控制多重比较。")
    doc.add_paragraph("数据集应提供 annotation guideline、双标注者一致性、难例标签、类别像素尺度分布和泄漏审计。模型卡应记录代码提交、依赖、权重哈希、训练时长、能耗、适用域和禁止用途。")

    doc.add_heading("19. 专业读者的最终判断", 1)
    doc.add_paragraph("IntelliBeeHive 是一篇有价值的全栈应用系统论文。它的强项是把物理通道、边缘视觉、跟踪、传感器、网络和用户界面连接为一个可运行原型，并公开讨论若干工程限制。它证明了低成本入口视觉监测的可行性，但尚未建立真实瓦螨诊断效度，也没有以现代检测和多目标跟踪规范完成跨域、独立、统计充分的验证。")
    doc.add_paragraph("对后续研究者，最值得继承的是系统问题意识和设计决策的可解释叙事；最需要改进的是数据开放、分组评测、指标严谨性、真实生物学终点和长期部署证据。把这些部分补齐，可从“可运行原型”推进到“可比较算法、可复现系统和可用于蜂群管理决策的科学工具”。")
    doc.add_heading("参考与核验材料", 1)
    for ref in ["Narcia-Macias, C. I., et al. IntelliBeeHive: An Automated Honey Bee, Pollen, and Varroa Destructor Monitoring System. arXiv:2309.08955v1, 2023.", "Wang, C.-Y., Bochkovskiy, A., Liao, H.-Y. M. YOLOv7: Trainable bag-of-freebies sets new state-of-the-art for real-time object detectors.", "Caltech-Honeybee public dataset, repository commit 0a06fabcf23bbc75f03af4b028f8070bda8a2649.", "本项目 metrics_summary.json、tracking_evaluation.json 与训练/测试曲线，生成于 2026-10-31."]:
        doc.add_paragraph(ref, style="List Bullet")
    path = DOCS / "第四篇论文_IntelliBeeHive专业深度解析与论文写作评析.docx"; doc.save(path); return path


def build_pdf(metric_chart: Path) -> Path:
    pdfmetrics.registerFont(TTFont("WQY", FONT))
    path = REPORTS / "第四篇论文复现结果报告.pdf"
    styles = getSampleStyleSheet()
    title = ParagraphStyle("CNTitle", parent=styles["Title"], fontName="WQY", fontSize=22, leading=30, textColor=colors.HexColor("#17365D"), alignment=TA_CENTER)
    h1 = ParagraphStyle("CNH1", parent=styles["Heading1"], fontName="WQY", fontSize=15, leading=22, textColor=colors.HexColor("#2F5597"), spaceBefore=12, spaceAfter=8)
    body = ParagraphStyle("CNBody", parent=styles["BodyText"], fontName="WQY", fontSize=9.5, leading=15, alignment=TA_LEFT, spaceAfter=6)
    small = ParagraphStyle("CNSmall", parent=body, fontSize=8, leading=11)
    story = [Paragraph("第四篇论文复现结果报告", title), Spacer(1, 0.4*cm), Paragraph("IntelliBeeHive：公开替代数据、YOLOv7-tiny、入口跟踪与部署链", body), Paragraph("生成日期：2026-10-31", body), Spacer(1, 0.5*cm)]
    story += [Paragraph("1. 复现结论", h1), Paragraph("已完成两套 YOLOv7-tiny 100 epochs 训练、独立分组测试、论文最近中点跟踪规则、视频监测代码、本地网页、TorchScript/ONNX 导出和完整文档。作者原始数据与源码未公开，因此结果属于方法与工程流程复现，不宣称严格数值复现。", body)]
    data = [["任务/类别", "P", "R", "F1", "mAP50", "mAP50:95"], ["蜜蜂", "0.930", "0.862", "0.895", "0.905", "0.512"], ["普通蜜蜂", "0.922", "0.871", "0.896", "0.920", "0.527"], ["携粉蜜蜂", "0.775", "0.704", "0.738", "0.778", "0.377"], ["两类总体", "0.848", "0.787", "0.816", "0.849", "0.452"]]
    table = Table(data, colWidths=[4.2*cm, 1.8*cm, 1.8*cm, 1.8*cm, 2.2*cm, 2.3*cm]); table.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"WQY"),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2F5597")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.4,colors.grey),("ALIGN",(1,1),(-1,-1),"CENTER"),("FONTSIZE",(0,0),(-1,-1),8.5),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F4F7FB")])]))
    story += [table, Spacer(1, 0.35*cm), RLImage(str(metric_chart), width=16.5*cm, height=8.8*cm)]
    story += [PageBreak(), Paragraph("2. 数据与协议", h1), Paragraph("公开替代数据为 Caltech-Honeybee，固定提交 0a06fab…；以 frame id // 10000 作为视频组，seed=2309，将 87 个组划为 61/13/13，得到 624/178/149 张 train/val/test。测试集 1043 个框，其中 ordinary 945、pollen-bearing 98。", body), Paragraph("两模型均使用官方 YOLOv7-tiny、416×416、batch 8、100 epochs、官方预训练权重；best.pt 由验证适应度选择，测试集只在训练结束后评估。", body)]
    story += [Paragraph("3. 速度与部署", h1), Paragraph("RTX 4090、batch 8：蜜蜂模型推理+NMS 约 4.9 ms/图，两类模型约 5.3 ms/图。此速度与作者 Jetson Nano TensorRT 约 27 ms/帧不在同一硬件/运行时，不能直接比较。两套 best.onnx 已成功导出；TensorRT engine 应在目标 Jetson 上构建并校验精度。", body)]
    story += [Paragraph("4. 跟踪诊断", h1), Paragraph("使用 BEE22 三个测试序列的真值检测框隔离检测误差。论文式最近中点跟踪完成 12205 次分配，加权轨迹纯度 0.9738，但有 199 次 ID 切换；越线累计绝对误差 Arriving=4、Leaving=26。结果说明简单规则能在平稳运动中工作，却对轨迹断裂、快速移动和拥挤敏感。", body)]
    story += [Paragraph("5. 与论文结果的关系", h1), Paragraph("论文报告蜜蜂检测 F1 约 0.95、跟踪计数准确率 96.28%、五段视频携粉平均 F1 0.8319。论文没有公开数据、划分、检测阈值或代码，且本项目花粉任务是全场景 ordinary/pollen-bearing 检测，论文则在蜂体裁剪上检测 pollen/mite，因此不进行等价排名。", body), Paragraph("论文 mite 类使用粘在死蜂上的 1.5 mm 红珠。项目未将其扩展为真实瓦螨检测主张。真实诊断必须建立真实螨数据并与标准感染率测量校准。", body)]
    for task, title_text in [("bee", "蜜蜂模型"), ("pollen", "普通/携粉模型")]:
        story += [PageBreak(), Paragraph(f"6. {title_text}训练与测试图", h1)]
        for file, caption in [(f"results/figures/{task}_training_results.png","100 epochs 训练曲线"),(f"results/figures/{task}_test_pr_curve.png","独立测试 PR 曲线"),(f"results/figures/{task}_test_confusion_matrix.png","独立测试混淆矩阵"),(f"results/figures/{task}_test_predictions.jpg","独立测试预测示例")]:
            p=ROOT/file
            if p.exists(): story += [RLImage(str(p), width=16.2*cm, height=9.0*cm), Paragraph(caption, small), Spacer(1,0.2*cm)]
    story += [PageBreak(), Paragraph("7. 已交付内容", h1), Paragraph("代码：下载、转换、训练、续训、测试、推理、视频、跟踪、网页、ONNX、结果汇总。文档：README、REPORT、VS Code 操作手册 Word、专业论文解析 Word、当前 PDF 报告。大数据、第三方源码和运行权重由脚本获取或本地生成，避免 Git 仓库不可维护。", body)]
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=1.8*cm, leftMargin=1.8*cm, topMargin=1.7*cm, bottomMargin=1.7*cm, title="第四篇论文复现结果报告")
    doc.build(story); return path


def main() -> None:
    chart = make_metric_chart()
    paths = [build_manual(chart), build_analysis(chart), build_pdf(chart)]
    for path in paths: print(path, path.stat().st_size)


if __name__ == "__main__":
    main()

