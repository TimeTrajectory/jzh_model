"""Generate a Chinese PDF report from experiment artifacts."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parent
FONT_PATH = Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
CLASS_NAMES = ["WB no pollen", "WB pollen", "Drone bee"]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def fmt(value: object, digits: int = 4) -> str:
    if value is None:
        return "未生成"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return str(value)


def training_summary(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        return {}
    key = "metrics/mAP50-95(B)"
    best = max(rows, key=lambda row: float(row[key]))
    return {
        "completed_epochs": int(float(rows[-1]["epoch"])),
        "best_epoch": int(float(best["epoch"])),
        "best_val_precision": float(best["metrics/precision(B)"]),
        "best_val_recall": float(best["metrics/recall(B)"]),
        "best_val_map50": float(best["metrics/mAP50(B)"]),
        "best_val_map50_95": float(best[key]),
    }


def build_pdf(output: Path) -> None:
    if FONT_PATH.exists():
        pdfmetrics.registerFont(TTFont("Chinese", str(FONT_PATH)))
        font = "Chinese"
    else:
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        font = "STSong-Light"

    styles = getSampleStyleSheet()
    body = ParagraphStyle("ChineseBody", parent=styles["BodyText"], fontName=font, fontSize=9.5, leading=15, spaceAfter=6)
    title = ParagraphStyle("ChineseTitle", parent=body, fontSize=19, leading=26, alignment=TA_CENTER, spaceAfter=14)
    h1 = ParagraphStyle("ChineseH1", parent=body, fontSize=14, leading=20, spaceBefore=10, spaceAfter=7, textColor=colors.HexColor("#17365D"))
    small = ParagraphStyle("ChineseSmall", parent=body, fontSize=8, leading=11)
    metrics = read_json(ROOT / "results/detector_metrics.json")
    train = training_summary(ROOT / "runs/detector/yolov10x_seed50/results.csv")

    def table(data: list[list[object]], widths: list[float] | None = None) -> Table:
        formatted = [[Paragraph(str(cell), small) for cell in row] for row in data]
        value = Table(formatted, colWidths=widths, repeatRows=1, hAlign="LEFT")
        value.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#7F8C8D")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return value

    story: list[object] = [
        Paragraph("第三篇论文复现结果报告", title),
        Paragraph("蜂群强度与授粉效率：YOLOv10X 三类别蜜蜂检测", ParagraphStyle("Sub", parent=body, fontSize=12, alignment=TA_CENTER)),
        Paragraph(f"生成日期：{date.today().isoformat()}", ParagraphStyle("Date", parent=body, alignment=TA_CENTER)),
        Spacer(1, 8 * mm),
        Paragraph("1. 论文与复现范围", h1),
        Paragraph("对应论文为 Chaudhary 等发表于 Smart Agricultural Technology 14 (2026) 102005 的研究。本项目完成论文最佳实时模型 YOLOv10X 的数据审计、训练、断点续训、固定测试集评估与推理流程，识别无花粉工蜂、带花粉工蜂和雄蜂。", body),
        Paragraph("2. 官方数据审计", h1),
        Paragraph("官方附件大小为 4,236,622,867 字节，SHA-256 为 cae66fc3d855ef1d26f570afe574cbfe23763c5da845b100625d0d490fd6c891。排除 macOS 资源叉并修复两份错误 imagePath 后，所有 4,590 份有效标注均成功转换。", body),
        table([
            ["划分", "图片", "无花粉工蜂", "带花粉工蜂", "雄蜂", "框总数"],
            ["训练", "2,754", "44,450", "2,463", "339", "47,252"],
            ["验证", "918", "14,459", "887", "102", "15,448"],
            ["测试", "918", "15,072", "922", "118", "16,112"],
            ["合计", "4,590", "73,981", "4,272", "559", "79,212"],
        ], [24*mm, 20*mm, 29*mm, 29*mm, 20*mm, 24*mm]),
        Paragraph("论文只公开 60/20/20 比例，没有公开逐帧清单和随机种子。本轮固定 seed 50，因此可重复本项目划分，但不能保证与作者的逐帧划分完全一致。", body),
        Paragraph("3. 训练设置", h1),
        table([
            ["项目", "本次设置"],
            ["模型", "COCO 预训练 YOLOv10X，31,660,658 参数"],
            ["输入", "请求 1080，Ultralytics 按步长补齐至 1088"],
            ["优化", "batch 4，SGD，初始学习率 0.01"],
            ["停止", "最多 100 epoch，patience 10；论文实际训练 45 epoch"],
            ["硬件", "NVIDIA GeForce RTX 4090 24 GB"],
            ["随机性", "seed 50，deterministic=True"],
        ], [38*mm, 122*mm]),
        Paragraph("4. 训练与独立测试结果", h1),
    ]

    if train:
        story.append(table([
            ["完成轮数", "最佳轮次", "验证 Precision", "验证 Recall", "验证 mAP@0.5", "验证 mAP@0.5:0.95"],
            [train["completed_epochs"], train["best_epoch"], fmt(train["best_val_precision"]), fmt(train["best_val_recall"]), fmt(train["best_val_map50"]), fmt(train["best_val_map50_95"])],
        ], [24*mm, 24*mm, 28*mm, 26*mm, 29*mm, 34*mm]))
        story.append(Paragraph("本轮按 patience=10 自然早停于第 43 轮，最佳模型来自第 33 轮；论文在其未公开的原始划分上训练到第 45 轮。", body))
    else:
        story.append(Paragraph("尚未找到训练 CSV。", body))

    if metrics:
        story.extend([
            Spacer(1, 3 * mm),
            table([
                ["测试 Precision", "测试 Recall", "测试 F1", "mAP@0.5", "mAP@0.5:0.95", "推理 FPS"],
                [fmt(metrics.get("precision")), fmt(metrics.get("recall")), fmt(metrics.get("f1_from_mean_precision_recall")), fmt(metrics.get("map50")), fmt(metrics.get("map50_95")), fmt(metrics.get("inference_fps"), 2)],
            ], [28*mm, 27*mm, 25*mm, 27*mm, 33*mm, 25*mm]),
            Spacer(1, 3 * mm),
        ])
        class_rows: list[list[object]] = [["类别", "Precision", "Recall", "F1", "AP50", "mAP@0.5:0.95"]]
        for name in CLASS_NAMES:
            item = metrics.get("per_class", {}).get(name, {})
            class_rows.append([name, fmt(item.get("precision")), fmt(item.get("recall")), fmt(item.get("f1")), fmt(item.get("ap50")), fmt(item.get("map50_95"))])
        story.append(table(class_rows, [38*mm, 24*mm, 24*mm, 22*mm, 24*mm, 33*mm]))
        story.append(Paragraph("测试划分清单有 16,112 个原始框。Ultralytics 发现一个坐标完全相同的重复标签，实际计分实例数为 16,111；数据审计仍保留论文口径的 79,212 个原始标注。", body))
        story.append(Paragraph(f"最佳权重 SHA-256：{metrics.get('weights_sha256', '未生成')}。该哈希用于确认评估时使用的权重文件。", body))
    else:
        story.append(Paragraph("独立测试指标尚未生成，请先运行 evaluate.py。", body))

    plot = ROOT / "runs/detector/yolov10x_seed50/results.png"
    confusion = ROOT / "runs/evaluation/test/confusion_matrix_normalized.png"
    for heading, image_path in (("训练曲线", plot), ("测试集归一化混淆矩阵", confusion)):
        if image_path.exists():
            story.extend([Paragraph(heading, h1), Image(str(image_path), width=165*mm, height=100*mm)])

    story.extend([
        PageBreak(),
        Paragraph("5. 与论文结果的关系", h1),
        Paragraph("论文报告 YOLOv10X accuracy 93.9%、F1 0.92、Cohen's kappa 0.6105、速度 25.93 FPS。本项目报告标准目标检测 Precision、Recall、F1、AP50 和 mAP@0.5:0.95。论文没有公开背景 TN 的构造方法，故其 accuracy 与标准 mAP 不能直接互换；本报告不会用 mAP 冒充 accuracy。FPS 也受 GPU、CUDA、软件版本和计时范围影响。", body),
        Paragraph("6. 结论与限制", h1),
        Paragraph("官方数据的图片数、标注总数和三类分布已复核并与论文完全一致。训练与测试采用固定 seed 的可审计划分，代码支持完整断点恢复。主要限制是作者未公开逐帧划分、随机种子、完整 accuracy/kappa 实现和训练权重；少数类雄蜂样本仅 559 个，结果应结合逐类别指标和混淆矩阵解读。", body),
        Paragraph("7. 操作入口", h1),
        Paragraph("完整的环境安装、数据准备、训练、断点续训、评估、推理、报告生成命令，以及各文件作用，均记录在仓库 README.md。", body),
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm, title="第三篇论文复现结果报告", author="论文复现项目")
    document.build(story)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "reports/第三篇论文复现结果报告.pdf")
    args = parser.parse_args()
    build_pdf(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
