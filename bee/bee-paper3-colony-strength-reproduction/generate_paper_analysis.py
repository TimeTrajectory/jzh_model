"""Generate a beginner-friendly, critical analysis of the third paper as DOCX."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from generate_word_manual import (
    add_bullets,
    add_code,
    add_note,
    add_steps,
    add_table,
    add_toc,
    setup_document,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "docs/第三篇论文深度分析与创新改进建议（入门版）.docx"
ASSETS = Path("/tmp/bee_paper3_analysis_assets")
FONT_FILE = Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")


def chart_font() -> FontProperties:
    return FontProperties(fname=str(FONT_FILE)) if FONT_FILE.exists() else FontProperties()


def make_charts() -> dict[str, Path]:
    ASSETS.mkdir(parents=True, exist_ok=True)
    font = chart_font()
    plt.rcParams["axes.unicode_minus"] = False

    classes = ["无花粉工蜂", "带花粉工蜂", "雄蜂"]
    counts = [73981, 4272, 559]
    shares = [94.0, 5.4, 0.7]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    colors = ["#4C78A8", "#F2CF5B", "#9C6ADE"]
    axes[0].bar(classes, counts, color=colors)
    axes[0].set_yscale("log")
    axes[0].set_title("类别标注数量（对数坐标）", fontproperties=font)
    axes[0].set_ylabel("边界框数量", fontproperties=font)
    for label in axes[0].get_xticklabels() + axes[0].get_yticklabels():
        label.set_fontproperties(font)
    for i, value in enumerate(counts):
        axes[0].text(i, value * 1.12, f"{value:,}", ha="center", fontsize=9)
    axes[1].pie(shares, labels=classes, autopct="%1.1f%%", colors=colors, startangle=90,
                textprops={"fontproperties": font, "fontsize": 9})
    axes[1].set_title("类别占比", fontproperties=font)
    fig.suptitle("论文公开数据集的类别极不平衡", fontproperties=font, fontsize=14)
    fig.tight_layout()
    class_chart = ASSETS / "class_distribution.png"
    fig.savefig(class_chart, dpi=180, bbox_inches="tight")
    plt.close(fig)

    models = ["YOLOv10", "Faster R-CNN", "RetinaNet", "FCOS", "SSD"]
    accuracy = [93.9, 93.4, 91.8, 92.3, 54.2]
    f1 = [92.0, 91.0, 90.0, 88.0, 69.0]
    fps = [25.93, 10.98, 22.20, 21.77, 23.72]
    x = range(len(models))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].bar([v - 0.18 for v in x], accuracy, width=0.36, label="Accuracy (%)", color="#4C78A8")
    axes[0].bar([v + 0.18 for v in x], f1, width=0.36, label="F1 × 100", color="#F58518")
    axes[0].set_ylim(45, 100)
    axes[0].set_title("论文报告的整体 Accuracy 与 F1", fontproperties=font)
    axes[0].legend()
    axes[0].set_xticks(list(x), models, rotation=18)
    axes[1].bar(models, fps, color="#54A24B")
    axes[1].set_title("论文报告的推理速度", fontproperties=font)
    axes[1].set_ylabel("FPS", fontproperties=font)
    axes[1].tick_params(axis="x", rotation=18)
    for ax in axes:
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font)
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("五种模型的结果与速度比较", fontproperties=font, fontsize=14)
    fig.tight_layout()
    model_chart = ASSETS / "model_comparison.png"
    fig.savefig(model_chart, dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 3.7))
    ax.axis("off")
    boxes = [
        (0.02, "摄像机视频", "采集蜂箱入口画面"),
        (0.21, "检测", "找出每一帧的蜜蜂"),
        (0.40, "跟踪", "跨帧识别同一只蜜蜂"),
        (0.59, "计数", "判断进入/离开并去重"),
        (0.78, "科学验证", "关联蜂群强度与授粉结果"),
    ]
    for i, (left, title, sub) in enumerate(boxes):
        ax.add_patch(plt.Rectangle((left, 0.32), 0.16, 0.38, facecolor="#D9EAF7", edgecolor="#1F4E78", linewidth=1.5))
        ax.text(left + 0.08, 0.57, title, ha="center", va="center", fontsize=12, fontproperties=font, weight="bold")
        ax.text(left + 0.08, 0.42, sub, ha="center", va="center", fontsize=8.5, fontproperties=font, wrap=True)
        if i < len(boxes) - 1:
            ax.annotate("", xy=(left + 0.19, 0.51), xytext=(left + 0.16, 0.51), arrowprops=dict(arrowstyle="->", color="#1F4E78", lw=1.5))
    ax.text(0.5, 0.88, "从论文的“检测模型”升级为真正的蜂群监测系统", ha="center", fontsize=15, fontproperties=font, weight="bold")
    ax.text(0.5, 0.13, "论文主要完成前两步中的“检测”；更强创新需要补齐跟踪、计数和生物学结果验证", ha="center", fontsize=10, fontproperties=font)
    innovation_chart = ASSETS / "innovation_pipeline.png"
    fig.savefig(innovation_chart, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {"class": class_chart, "model": model_chart, "innovation": innovation_chart}


def add_figure(doc, path: Path, caption: str, width: float = 6.4) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(path), width=Inches(width))
    p = doc.add_paragraph(caption)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True
    p.runs[0].font.size = Pt(9)


def build_document():
    charts = make_charts()
    doc = setup_document()
    doc.sections[0].header.paragraphs[0].text = "第三篇论文深度分析 · 实验结论、创新点、局限与改进路线"
    props = doc.core_properties
    props.title = "第三篇论文深度分析与创新改进建议（入门版）"
    props.subject = "蜂群强度与授粉效率视觉监测论文的通俗解读、批判性分析与后续创新设计"
    props.author = "TimeTrajectory 蜜蜂论文复现项目"
    props.keywords = "蜜蜂, YOLOv10, 目标检测, 蜂群强度, 授粉效率, 论文分析, 创新"

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("第三篇论文深度分析\n与创新改进建议")
    subtitle = doc.add_paragraph(style="Subtitle")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("面向初学者：从“这篇论文做了什么”到“下一篇更强论文怎么做”")
    doc.add_paragraph()
    add_table(doc, ["项目", "内容"], [
        ["论文题目", "Estimating colony strength and pollination efficiency in honey bees using a novel dataset and deep learning-based models"],
        ["作者", "Piyush Chaudhary、Connor Foley、Sathishkumar Samiappan、Leon Kohler、Volkan Senyurek、Dawson Boes、Priyadarshini Chakrabarti"],
        ["期刊", "Smart Agricultural Technology 14 (2026) 102005"],
        ["DOI", "10.1016/j.atech.2026.102005"],
        ["原始 PDF", "pdf-paper/1-s2.0-S2772375526002285-main.pdf（15 页）"],
        ["分析原则", "区分论文事实、合理解释、批判性判断和未来建议"],
        ["文档版本", f"1.0（{date.today().isoformat()}）"],
    ], [4.2, 12.3])
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("一句话结论：这是一篇很有实用价值的数据集与检测模型论文，但还不是完整的蜂群强度/授粉效率科学验证论文。 ").bold = True
    doc.add_page_break()

    doc.add_heading("目录", level=1)
    add_toc(doc)
    add_note(doc, "目录使用", "在 Word/WPS 中右键目录并选择“更新整个目录”，即可显示最新页码。")

    doc.add_heading("1. 给完全不懂的人：这篇论文到底在做什么", level=1)
    doc.add_paragraph("想象在蜂箱门口安装一台摄像机。传统方法需要人盯着视频，一只一只数蜜蜂，还要判断哪只工蜂腿上带着花粉、哪只是雄蜂。蜂很多、移动快、相互遮挡，而且光线和天气不断变化，人工作业非常慢。")
    doc.add_paragraph("论文训练计算机视觉模型，让计算机在每一帧画面中给蜜蜂画框，并把框分成三类：不带花粉的工蜂、带花粉的工蜂、雄蜂。带花粉工蜂数量可以作为授粉活动和育幼活动的间接信号；进出蜂箱的工蜂活动也可能反映蜂群状态。")
    add_table(doc, ["容易混淆的概念", "通俗解释"], [
        ["检测", "在图片里找到蜜蜂，并画出矩形框"],
        ["分类", "判断框里是无花粉工蜂、带花粉工蜂还是雄蜂"],
        ["跟踪", "在连续视频中知道第 1 帧和第 2 帧是不是同一只蜜蜂"],
        ["计数", "同一只蜜蜂不能跨帧重复计算，还要判断进入或离开"],
        ["蜂群强度估计", "把活动数据与蜂群人口、子脾、蜂脾覆盖等真实指标建立关系"],
        ["授粉效率估计", "把带花粉蜂、访花活动与花粉沉积、坐果率或产量建立关系"],
    ], [4.0, 12.5])
    add_note(doc, "最关键区别", "论文真正完成并严谨评估的是“检测 + 三分类”。它提出这些检测结果可用于估计蜂群状态和授粉活动，但没有完成唯一个体跟踪，也没有用真实蜂群强度或作物授粉结果验证最终估计。")

    doc.add_heading("2. 论文要解决的现实问题", level=1)
    doc.add_heading("2.1 为什么要监测蜂箱入口", level=2)
    add_bullets(doc, [
        "蜂蜜和农作物授粉具有重要经济价值，蜂群衰退会影响产量、食品安全和生态系统。",
        "返回蜂箱的带花粉工蜂说明蜂群正在采集花粉，常与育幼需求和授粉活动有关。",
        "论文引用经验：每分钟超过 100 只进入的采集蜂可被视为较好的授粉蜂群，但温度和风速会显著影响活动。",
        "频繁开箱检查会扰动蜂群，而且开箱时外出的采集蜂不在箱内，单次检查不能完整反映实时活动。",
    ])
    doc.add_heading("2.2 传统方法为什么不理想", level=2)
    add_table(doc, ["方法", "优点", "主要问题"], [
        ["人工站在蜂箱旁计数", "直观、无需设备", "耗时、主观、难以长时间连续执行"],
        ["录视频后逐帧人工计数", "可复查", "可能需要数周或数月，仍然非常费人"],
        ["花粉采集器/入口陷阱", "便于观察", "改变入口、可能造成压力，并限制蜂流"],
        ["红外、雷达、RFID", "可自动采集", "成本、专业知识、标签和安装维护门槛较高"],
        ["受控入口的视觉系统", "背景简单、准确率容易提高", "改变自然环境，换到真实蜂箱可能失效"],
    ], [4.0, 5.0, 7.5])
    doc.add_paragraph("论文的核心动机是：使用常见 GoPro 和深度学习，在不改造蜂箱入口的真实环境中完成自动识别。")

    doc.add_heading("3. 研究目标和论文逻辑", level=1)
    doc.add_heading("3.1 明确目标", level=2)
    add_steps(doc, [
        "建立真实蜂箱入口、多天气、多光照的公开数据集。",
        "把每只蜜蜂标注为三种具有生物学意义的类别。",
        "比较 YOLOv10、Faster R-CNN、RetinaNet、FCOS 和 SSD 五种检测器。",
        "找出适合实时蜂箱监测的模型，并讨论部署方式。",
    ])
    doc.add_heading("3.2 论文的因果链条", level=2)
    add_code(doc, "看到带花粉工蜂 → 推测存在活跃花粉采集 → 可能反映育幼需求和授粉活动\n看到大量进出工蜂 → 推测蜂群活动强 → 可能反映蜂群强度\n视觉模型自动识别 → 降低人工计数成本 → 支持长期监测")
    doc.add_paragraph("这里的“可能反映”非常重要。检测结果是代理变量，不是蜂群强度或授粉效率本身。要把代理变量升级为科学结论，还需要与真实生物学指标做相关性、预测性和跨地点验证。")

    doc.add_heading("4. 数据是怎样采集出来的", level=1)
    doc.add_heading("4.1 采集地点和时间", level=2)
    add_bullets(doc, [
        "地点：美国密西西比州立大学 Starkville 校园研究蜂场。",
        "时间跨度：两年，覆盖早晨、中午、傍晚及不同季节。",
        "设备：GoPro Hero 9 和 Hero 11，4K 录制。",
        "普通视频：30～60 分钟，1 或 2 FPS；三段交尾群相关视频以 30 FPS 录制。",
        "相机对准入口，蜂箱入口约占画面底部三分之一；后续用 Matlab 截取底部三分之一。",
        "记录温度、湿度、风速、风向、太阳辐射；7 段未现场记录的视频用附近气象站历史数据补齐。",
    ])
    doc.add_heading("4.2 数据并非简单随机抽样", level=2)
    doc.add_paragraph("研究者会优先选择带花粉工蜂较多或出现雄蜂的视频进行标注，因为这两类天然稀少。这样做能增加少数类样本，有利于训练，但也意味着公开数据中的类别比例不等同于自然蜂群真实频率。不能拿数据集 5.4% 的带花粉比例直接当作某个蜂群的实际花粉采集比例。")
    doc.add_heading("4.3 数据规模", level=2)
    add_table(doc, ["项目", "论文数值", "怎样理解"], [
        ["视频", "15 段", "数据来源单位较少，视频内部帧可能高度相似"],
        ["标注帧", "4,590", "图像规模中等，远少于通用视觉数据集"],
        ["边界框", "79,212", "单帧蜜蜂密度高，检测框很多"],
        ["无花粉工蜂", "73,981（约 94%）", "绝对主导类别"],
        ["带花粉工蜂", "4,272（5.4%）", "少数类"],
        ["雄蜂", "559（0.7%）", "极少数类且具有季节性"],
    ], [4.0, 5.0, 7.5])
    add_figure(doc, charts["class"], "图 1  论文数据类别分布：数量差距达到两个数量级")
    add_note(doc, "隐藏的难点", "论文指出花粉团平均只有约 15×15 像素。模型不仅要找到小而密集、快速移动的蜜蜂，还要观察腿上非常小的花粉特征。")

    doc.add_heading("5. 标注方法与数据质量", level=1)
    doc.add_heading("5.1 标注类别", level=2)
    add_table(doc, ["类别", "判断依据", "潜在歧义"], [
        ["WB no pollen", "工蜂，后腿没有清晰花粉团", "可能包括守卫蜂、花蜜采集蜂；遮挡导致看不见花粉时也可能被放入此类"],
        ["WB pollen", "后腿花粉篮有明显黄色/橙色花粉团", "花粉很小、运动模糊、腿被遮挡时困难"],
        ["Drone bee", "体型更大、眼部结构和形态不同", "季节性强，样本极少"],
    ], [3.5, 6.0, 7.0])
    doc.add_heading("5.2 标注流程", level=2)
    add_bullets(doc, [
        "使用开源 LabelMe 创建水平矩形框。",
        "由熟悉蜜蜂形态的专家识别类别。",
        "遮挡和运动模糊的蜜蜂仍尽量标注，以匹配真实蜂箱入口。",
        "同一数据在不同阶段经过多轮人工复查，修正类别拼写、边界框和错误分类。",
    ])
    doc.add_heading("5.3 值得肯定和需要警惕的地方", level=2)
    add_table(doc, ["方面", "评价"], [
        ["真实难例", "保留遮挡、模糊和密集场景，比只标清晰蜜蜂更接近实际部署。"],
        ["专家复查", "多轮复查能提升一致性，是资源受限条件下的合理做法。"],
        ["无正式一致性指标", "只有有限标注者，没有报告 Cohen's kappa 等标注者一致性，无法量化标签可靠性。"],
        ["遮挡规则偏置", "看不清后腿且不像雄蜂时归为无花粉工蜂，会系统性增加该类并低估花粉类。"],
        ["431 个零框帧", "Table 2 有一段视频 431 帧但三类标注均为 0，可能作为背景负样本；论文没有充分解释其选择标准。"],
    ], [4.2, 12.3])

    doc.add_heading("6. 五种模型：用最简单的话理解", level=1)
    add_table(doc, ["模型", "像什么", "主要优势", "主要风险"], [
        ["YOLOv10X", "扫一眼整张图就直接画框和分类", "速度快、整体结果最好、适合实时", "高置信阈值下可能漏检；论文观察到一些假阳性"],
        ["Faster R-CNN", "先找可疑区域，再逐个仔细检查", "小目标和密集目标强，高置信时稳定", "两阶段导致速度慢、计算量大"],
        ["RetinaNet", "单次检测，但特别关注难样本", "Focal Loss 适合类别不平衡，分类较好", "检测召回不一定最好"],
        ["FCOS", "不用预设锚框，直接从特征点预测", "结构简洁，对小目标友好，检测数量较好", "分类性能略低于 RetinaNet"],
        ["SSD", "在多个尺度用预设框快速猜目标", "结构经典、速度尚可", "默认锚框不适合本任务的小而密集目标，结果明显差"],
    ], [3.0, 4.3, 4.5, 4.7])
    doc.add_heading("6.1 为什么比较这些模型有意义", level=2)
    doc.add_paragraph("五种模型代表了不同设计思路：一阶段与两阶段、锚框与无锚框、普通分类损失与 Focal Loss。比较它们不只是找最高分，还能说明什么架构更适合小目标、密集场景和极不平衡类别。")

    doc.add_heading("7. 实验设置", level=1)
    doc.add_heading("7.1 共同设置", level=2)
    add_bullets(doc, [
        "GPU：Tesla P100 16 GB，系统内存 30 GB。",
        "batch size：所有模型均为 4。",
        "数据划分：训练 60%、验证 20%、测试 20%。",
        "early stopping：连续 10 轮没有改善就停止并保留最佳模型。",
        "学习率通过随机搜索选择，使用 one-cycle 学习率策略。",
        "每轮随机执行模糊、亮度/对比度、水平翻转、旋转和保留框的裁剪。",
    ])
    doc.add_heading("7.2 各模型配置", level=2)
    add_table(doc, ["模型", "参数量", "训练轮数", "骨干网络", "预训练", "优化器", "初始学习率", "FLOPS", "FPS"], [
        ["YOLOv10", "31.6M", 45, "Enhanced CSPNet", "COCO", "SGD", "1.0e-2", "169.8G", 25.93],
        ["Faster R-CNN", "43.3M", 47, "ResNet50", "ImageNet", "AdamW", "6.0e-5", "280.37G", 10.98],
        ["RetinaNet", "36.4M", 58, "ResNet50", "ImageNet", "AdamW", "9.0e-5", "152.24G", 22.20],
        ["FCOS", "32.1M", 43, "ResNet50", "ImageNet", "AdamW", "1.5e-4", "128.21G", 21.77],
        ["SSD", "24.0M", 79, "VGG16", "ImageNet", "AdamW", "3.0e-3", "98.20G", 23.72],
    ], [2.7, 1.8, 1.6, 2.7, 1.8, 1.8, 2.1, 1.8, 1.5])
    doc.add_heading("7.3 数据增强", level=2)
    add_table(doc, ["增强", "论文设置", "目的"], [
        ["Motion/Gaussian blur", "最大核 (3,7)，概率 0.25", "模拟快速飞行、失焦和运动模糊"],
        ["亮度/对比度", "limit 0.25，概率 1.0", "适应不同日照和阴影"],
        ["水平翻转", "概率 0.4", "扩展方向变化"],
        ["旋转", "概率 0.4，角度范围未明确", "适应姿态变化"],
        ["随机裁剪", "概率 0.3，不丢失框", "改变构图和局部尺度"],
    ], [4.0, 5.5, 7.0])
    add_note(doc, "复现难点", "论文没有给随机种子、逐帧划分列表、旋转角度范围、完整代码提交和每个模型的训练实现版本。因此可以复现方法方向，但很难逐位复现所有数字。")

    doc.add_heading("8. 评价指标：初学者也能看懂", level=1)
    add_table(doc, ["指标", "通俗问题", "例子"], [
        ["IoU", "预测框和真实框重叠得有多好？", "IoU≥0.5 时，论文把它作为匹配真值的基础"],
        ["Precision", "模型说“这是蜜蜂”的结果里，有多少是真的？", "误检越少，Precision 越高"],
        ["Recall", "真实存在的蜜蜂里，模型找到了多少？", "漏检越少，Recall 越高"],
        ["F1", "Precision 和 Recall 能否兼顾？", "适合同时关心误检和漏检"],
        ["mAP@50", "框重叠要求为 0.5 时，各类别综合得分如何？", "偏向实用检测能力"],
        ["mAP@50:95", "从宽松到严格的框要求下，综合定位能力如何？", "更严格，更适合模型基准比较"],
        ["FPS", "一秒能处理多少帧？", "实时部署的重要指标"],
        ["Cohen's kappa", "预测与真值的一致性是否超过偶然？", "1 最好，0 接近偶然，负数比偶然更差"],
    ], [3.2, 7.2, 6.0])
    add_note(doc, "Accuracy 警告", "目标检测中的背景“真负例”数量没有自然上限。论文给出包含 TN 的 Accuracy 公式，但没有充分说明如何定义背景 TN。因此 Accuracy 不能像普通三分类那样直接解释，也不能拿 mAP 代替它。")

    doc.add_heading("9. 主要实验结果", level=1)
    doc.add_heading("9.1 整体结果", level=2)
    add_table(doc, ["模型", "Accuracy", "F1", "Cohen's kappa", "FPS", "结论"], [
        ["YOLOv10", "93.9%", 0.92, 0.6105, 25.93, "综合最好，速度最快，最适合实时"],
        ["Faster R-CNN", "93.4%", 0.91, 0.5629, 10.98, "精度接近 YOLO，高置信更稳定，但慢"],
        ["RetinaNet", "91.8%", 0.90, 0.4921, 22.20, "类别不平衡下分类较强"],
        ["FCOS", "92.3%", 0.88, 0.5152, 21.77, "检测召回优于 RetinaNet"],
        ["SSD", "54.2%", 0.69, -0.1391, 23.72, "明显不适合当前小而密集的目标设置"],
    ], [3.0, 2.2, 1.7, 2.5, 1.7, 6.0])
    add_figure(doc, charts["model"], "图 2  五种模型整体指标和速度（数值来自论文摘要与 Table 1）")
    doc.add_heading("9.2 mAP 结果的细节", level=2)
    add_bullets(doc, [
        "Faster R-CNN 在 mAP@50 上最高，说明 IoU=0.5 的常用阈值下，它检测和分类非常稳。",
        "在更严格的 mAP@50:95 上，YOLOv10 和 RetinaNet 超过 Faster R-CNN，说明它们在多个定位严格度下更均衡。",
        "论文用曲线展示 mAP 随置信阈值变化，但没有在表格中公开每个模型固定阈值下的精确 mAP 数值，这降低了结果复用便利性。",
    ])
    doc.add_heading("9.3 每个模型为什么出现这种结果", level=2)
    add_bullets(doc, [
        "YOLOv10：一次前向完成检测，架构针对效率优化，取得最佳速度/精度平衡；但在部分阈值出现假阳性。",
        "Faster R-CNN：先提出高质量候选区再精细判断，所以高置信时仍稳定；代价是 280.37G FLOPS 和最低 FPS。",
        "RetinaNet：Focal Loss 让模型更关注困难和少数类，因此分类表现较好。",
        "FCOS：无锚框设计更容易捕捉目标，论文观察到其找出的蜜蜂比 RetinaNet 多，但类别判断略弱。",
        "SSD：预设锚框与小而密集的蜜蜂/15×15 像素花粉团不匹配，导致定位和分类均弱。",
    ])

    doc.add_heading("10. 天气条件实验怎么理解", level=1)
    add_table(doc, ["天气", "帧数", "Accuracy", "F1"], [
        ["Sunny", 595, "93.9%", 0.916],
        ["Mostly Cloudy", 42, "92.9%", 0.901],
        ["Partly Cloudy", 28, "92.1%", 0.896],
        ["Cloudy", 19, "98.8%", 0.988],
    ], [4.0, 3.0, 4.0, 4.0])
    doc.add_paragraph("论文据此认为视觉方法在天气变化下表现良好。这个方向有价值，因为模型输入只有图像，不需要实时气象传感器。")
    add_note(doc, "不要过度解读", "Cloudy 只有 19 帧，Partly Cloudy 只有 28 帧，样本量远小于 Sunny。98.8% 可能来自小样本波动；论文没有给置信区间，也没有清楚说明天气结果对应哪个模型或是否按视频独立划分。因此只能说“初步显示稳健”，不能证明对所有天气不变。")

    doc.add_heading("11. 统计检验说明了什么", level=1)
    doc.add_heading("11.1 Friedman 检验", level=2)
    doc.add_paragraph("论文报告 Friedman statistic=20.6667，p<0.001。直观含义是：五种模型的表现不可能都一样，至少一个模型与其他模型存在显著差异。SSD 的明显低性能很可能是差异的重要来源。")
    doc.add_heading("11.2 它没有说明什么", level=2)
    add_bullets(doc, [
        "p<0.001 不等于 YOLOv10 显著优于每一个模型。需要事后两两检验和多重比较校正。",
        "论文没有充分解释 Friedman 检验中的重复测量单元是什么，也没有报告效应量。",
        "没有多随机种子重复训练，模型之间的差异可能包含训练随机波动。",
    ])
    doc.add_heading("11.3 Cohen's kappa", level=2)
    doc.add_paragraph("YOLOv10 的 0.6105 被作者解释为 substantial agreement，Faster R-CNN、RetinaNet、FCOS 属于中等一致；SSD=-0.1391 表示比偶然一致还差。它进一步支持 SSD 不适合当前设置，但 kappa 的计算仍依赖混淆矩阵如何处理背景和未匹配框。")

    doc.add_heading("12. 论文最终得出了哪些结论", level=1)
    add_table(doc, ["结论", "证据强度", "分析"], [
        ["真实蜂箱入口可以用深度学习检测三类蜜蜂", "强", "有独立测试集、五模型对比和高 F1 支持"],
        ["YOLOv10 最适合实时应用", "较强", "综合 Accuracy/F1/FPS/kappa 最好"],
        ["Faster R-CNN 适合重视高置信可靠性的任务", "较强", "高 mAP@50，高置信下指标保持更好，但 FPS 低"],
        ["SSD 不适合当前配置", "强", "Accuracy、kappa 和混淆矩阵均明显差"],
        ["系统在不同天气下稳健", "中等偏弱", "有分组结果，但天气样本极不均衡且无外部站点"],
        ["系统可以估计蜂群强度", "概念上合理，未直接验证", "没有把视觉计数与真实蜂群人口/子脾建立模型"],
        ["系统可以估计授粉效率", "概念上合理，未直接验证", "没有测量花粉沉积、坐果率、产量或田间访花结果"],
    ], [5.0, 3.0, 8.5])

    doc.add_heading("13. 论文真正的创新点", level=1)
    doc.add_heading("13.1 真实、非侵入式场景", level=2)
    doc.add_paragraph("不改造蜂箱入口，不用专门通道把蜜蜂排成一列，而是在真实、嘈杂、密集、光线变化的入口检测。这让任务更难，但实用价值更高。")
    doc.add_heading("13.2 公开的三类别数据集", level=2)
    doc.add_paragraph("公开 4,590 帧、79,212 个框，并区分花粉工蜂、非花粉工蜂和雄蜂。过去研究常只做蜜蜂/非蜜蜂，或不考虑雄蜂。数据集本身是这篇论文最持久的贡献之一。")
    doc.add_heading("13.3 五种不同架构的系统比较", level=2)
    doc.add_paragraph("论文不是只训练一个 YOLO 后报告高分，而是比较一阶段、两阶段、锚框、无锚框和 Focal Loss 模型，并同时讨论速度、精度和部署取舍。")
    doc.add_heading("13.4 面向实际部署", level=2)
    doc.add_paragraph("作者讨论 GoPro、Jetson Orin Nano、网页/移动端上传视频等实施路线，体现了从算法到养蜂应用的意识。论文估算 GoPro 约 250–350 美元，Jetson Orin Nano 约 250–300 美元。")

    doc.add_heading("14. 这篇论文做得好的地方", level=1)
    add_bullets(doc, [
        "研究问题有现实价值，能减少人工计数和开箱干扰。",
        "数据采集跨两年，并主动覆盖时间、季节、天气和光照变化。",
        "保留遮挡、模糊和密集难例，没有只选择漂亮图片。",
        "公开数据并描述标注流程，便于复现和后续研究。",
        "五模型对比兼顾 Accuracy、F1、mAP、FPS、FLOPS、kappa 和混淆矩阵。",
        "明确讨论类别不平衡，并使用 Focal Loss 和数据增强应对。",
        "对模型优缺点的解释与架构特点基本一致，具有教学价值。",
    ])

    doc.add_heading("15. 论文的局限与批判性分析", level=1)
    doc.add_heading("15.1 最大概念缺口：检测不等于蜂群强度或授粉效率", level=2)
    doc.add_paragraph("论文标题强调估计蜂群强度和授粉效率，但实验终点是检测框和类别指标。没有报告自动计数与人工唯一个体计数的 MAE，也没有把计数与蜂脾覆盖、成年蜂数量、子脾面积、蜂箱重量、花粉沉积、坐果率或作物产量关联。")
    doc.add_paragraph("因此最严谨的表述应是：该研究提供了构建蜂群强度和授粉效率代理指标的视觉基础，而不是已经验证出可靠的最终估计系统。")
    doc.add_heading("15.2 缺少跨帧跟踪和方向判断", level=2)
    doc.add_paragraph("同一只蜜蜂会出现在连续多帧。如果逐帧把框相加，会重复计数；如果不判断飞行方向，也无法区分进入、离开、守卫和在入口徘徊。论文自己也指出，无花粉工蜂中的不同行为组需要跟踪器才能分开。")
    doc.add_heading("15.3 数据泄漏风险", level=2)
    doc.add_paragraph("论文只有 15 段视频，却把 4,590 帧按 60/20/20 划分，未公开逐帧清单，也未说明是否按视频、日期或蜂箱分组。若同一视频的相邻帧同时进入训练和测试，背景和蜜蜂位置高度相似，测试分数可能偏乐观。这是基于方法描述提出的风险，不代表已经证实存在泄漏。")
    doc.add_heading("15.4 单地点和单一生态域", level=2)
    doc.add_paragraph("所有数据来自一个研究蜂场、当地 Apis mellifera 亚种和标准蜂箱。不同地区、蜂种体色、入口结构、降雪、植被背景、镜头角度都可能导致性能下降。没有外部数据集测试。")
    doc.add_heading("15.5 极端类别不平衡", level=2)
    doc.add_paragraph("94% 的框属于无花粉工蜂。整体 Accuracy 容易被多数类主导。雄蜂只有 559 个框，且主要集中在特定日期；即使单次测试结果高，也可能对新季节和新蜂场不稳定。")
    doc.add_heading("15.6 标注偏差", level=2)
    doc.add_paragraph("遮挡时看不清花粉就归为无花粉工蜂，这一规则会把未知样本压入多数类。没有双人独立标注和一致性统计，模型的上限和错误可能部分来自标签噪声。")
    doc.add_heading("15.7 模型比较并非完全等条件", level=2)
    add_bullets(doc, [
        "模型使用不同骨干、预训练数据、优化器、学习率和训练轮数。",
        "随机搜索的范围、次数和每模型调参预算没有完整公开。",
        "只报告一次训练，没有多 seed 均值和标准差。",
        "FPS 是否包含预处理、后处理、batch 和框架差异不够明确。",
        "SSD 的失败可能既来自架构，也来自默认锚框/输入配置没有针对本数据优化。",
    ])
    doc.add_heading("15.8 评价和统计报告不够完整", level=2)
    add_bullets(doc, [
        "检测 Accuracy 中 TN 定义不清，背景真负例在目标检测中很难自然计数。",
        "固定阈值的逐模型 mAP 精确数字没有汇总表，主要依赖曲线。",
        "Friedman 显著后没有报告成对事后检验。",
        "天气小组样本极不均衡，没有置信区间或视频级独立分析。",
        "没有阈值校准、计数误差和长时间运行稳定性评估。",
    ])

    doc.add_heading("16. 论文主张与证据边界", level=1)
    add_table(doc, ["主张层级", "论文是否完成", "还需要什么"], [
        ["图片中找到蜜蜂", "已完成", "跨站点复核"],
        ["区分三类蜜蜂", "已完成", "更多少数类、双人标注"],
        ["实时运行", "初步完成", "端到端延迟、功耗、长期稳定性"],
        ["统计进入/离开数量", "未完成", "多目标跟踪、过线计数、方向识别"],
        ["估计蜂群强度", "未直接完成", "与蜂脾覆盖、成年蜂、子脾、重量做实证关联"],
        ["估计授粉效率", "未直接完成", "与访花、花粉沉积、坐果率、产量做实证关联"],
        ["跨地区商业应用", "未验证", "多蜂场、多蜂种、多蜂箱外部测试"],
    ], [4.4, 4.0, 8.2])

    doc.add_heading("17. 本地复现结果如何补充理解论文", level=1)
    doc.add_paragraph("当前项目对官方附件进行了独立审计，确认 4,590 帧、79,212 个原始框和三类计数与论文完全一致。使用 seed 50 生成可审计的 60/20/20 划分，复现 YOLOv10X 路线。")
    add_table(doc, ["项目", "论文", "本地复现"], [
        ["训练停止", "45 epoch", "patience=10，自然停止于 43 epoch"],
        ["最佳轮次", "未单独明确", "33"],
        ["F1", "0.92", "0.9353（标准检测 P/R 推导）"],
        ["mAP@0.5", "曲线展示，未给单一表格数值", "0.9629"],
        ["mAP@0.5:0.95", "曲线展示，未给单一表格数值", "0.6374"],
        ["纯模型推理", "25.93 FPS（P100）", "约 160 FPS（RTX 4090，计时范围不同）"],
    ], [4.2, 6.2, 6.2])
    add_note(doc, "不要把复现差异当成胜负", "论文没有公开逐帧划分和代码版本，硬件与计时方法也不同。复现结果证明流程可运行、数据一致，并不能证明本地模型绝对优于作者模型。")

    doc.add_heading("18. 怎样做出比原论文更强的创新", level=1)
    add_figure(doc, charts["innovation"], "图 3  更强研究应从单帧检测扩展到跟踪、计数和生物学结果验证")
    doc.add_heading("18.1 创新一：检测 + 跟踪 + 过线计数", level=2)
    doc.add_paragraph("在 YOLOv10 后加入 ByteTrack、BoT-SORT 或 OC-SORT，为每只蜜蜂分配跨帧 ID；设置蜂箱入口计数线，判断进入和离开；用轨迹长度、方向和时间去除守卫蜂徘徊与重复计数。")
    add_table(doc, ["新增评价", "含义"], [
        ["IDF1 / HOTA", "跟踪身份是否稳定"],
        ["Count MAE / MAPE", "自动进出计数与人工计数差多少"],
        ["方向准确率", "进入/离开判断是否正确"],
        ["每分钟净流量", "进入数减去离开数，可形成时间序列"],
    ], [5.0, 11.5])
    doc.add_heading("18.2 创新二：真正验证蜂群强度", level=2)
    doc.add_paragraph("每周同时采集视觉流量和标准蜂群检查数据：成年蜂覆盖框数、子脾面积、蜂王状态、蜂箱重量、病虫害。建立混合效应模型或时间序列模型，预测真实蜂群强度，并按蜂箱/日期留出测试。")
    doc.add_heading("18.3 创新三：真正验证授粉效率", level=2)
    doc.add_paragraph("把返回带花粉工蜂率与作物田间指标关联：单位时间访花次数、柱头花粉沉积、坐果率、果实重量和产量。这样才能回答“检测到花粉蜂是否真的预测了授粉结果”。")
    doc.add_heading("18.4 创新四：严格跨域数据划分", level=2)
    add_bullets(doc, [
        "按整段视频分组，避免相邻帧跨集合。",
        "按蜂箱留一验证，检查模型能否适应新蜂箱。",
        "按日期/季节留一验证，检查时间变化。",
        "跨蜂场、地区、蜂种和入口结构做外部测试。",
        "最终报告 frame-level、video-level、hive-level 三套结果。",
    ])
    doc.add_heading("18.5 创新五：专门解决少数类和小花粉团", level=2)
    add_bullets(doc, [
        "类别均衡采样、Class-Balanced Loss、Varifocal/Focal Loss。",
        "针对花粉团的 Copy-Paste、合成数据和困难样本挖掘。",
        "两级但联合优化的模型：先检测蜜蜂，再对腿部 ROI 做花粉分类/分割。",
        "加入“不可判断/遮挡”类别或软标签，避免强制归入无花粉工蜂。",
        "主动学习：让模型挑选最不确定帧给专家标注，提高每小时标注价值。",
    ])
    doc.add_heading("18.6 创新六：多模态时间序列", level=2)
    doc.add_paragraph("把图像计数与温度、湿度、风速、太阳辐射、蜂箱重量和声音结合。视觉回答“发生了什么”，环境和时间序列模型回答“为什么变化、接下来会怎样”，可用于异常预警。")
    doc.add_heading("18.7 创新七：真实边缘部署", level=2)
    add_bullets(doc, [
        "比较 YOLOv10X 与 N/S、蒸馏模型和轻量 Transformer。",
        "导出 ONNX/TensorRT，测试 FP16/INT8 量化。",
        "报告端到端 FPS、P95 延迟、功耗、温度、丢帧和每日电量。",
        "进行连续数天运行测试、镜头污损和相机偏移鲁棒性测试。",
    ])
    doc.add_heading("18.8 创新八：可信度与解释", level=2)
    doc.add_paragraph("做置信度校准、错误类型标注和不确定性估计。当模型遇到新蜂种、严重遮挡或暴雨时，应该能够说“我不确定”，并把片段提交人工复核，而不是给出看似精确的错误数字。")

    doc.add_heading("19. 推荐的新论文方案", level=1)
    doc.add_heading("19.1 建议题目", level=2)
    doc.add_paragraph("Cross-apiary honey bee traffic monitoring using detection-tracking and biologically validated colony-strength and pollination indicators（基于检测跟踪和生物学验证的跨蜂场蜜蜂流量监测）")
    doc.add_heading("19.2 核心科学问题", level=2)
    add_steps(doc, [
        "视频级严格划分下，三类检测性能是否仍然稳定？",
        "检测 + 跟踪能否准确统计进出、带花粉返回率和雄蜂活动？",
        "这些时间序列能否预测独立测量的蜂群强度？",
        "带花粉返回率能否预测田间授粉结果？",
        "系统能否跨蜂场、蜂种、季节和设备泛化？",
        "轻量模型能否在边缘设备持续运行并保持可接受误差？",
    ])
    doc.add_heading("19.3 建议实验设计", level=2)
    add_table(doc, ["模块", "建议设计", "关键指标"], [
        ["数据", "≥3 地区、≥5 蜂场、多个蜂箱/季节/蜂种；按视频和蜂箱分组", "覆盖度、类别数、域差异"],
        ["检测", "YOLOv10 基线 + 轻量/Transformer + 类别不平衡策略", "mAP、macro F1、每类 Recall"],
        ["跟踪", "ByteTrack/BoT-SORT，对进入/离开设置计数线", "HOTA、IDF1、Count MAE"],
        ["蜂群强度", "同步人工检查、蜂箱重量和子脾面积", "R²、MAE、混合效应模型"],
        ["授粉", "带花粉率对花粉沉积、坐果率和产量", "相关性、预测误差、置信区间"],
        ["部署", "Jetson 多精度、多模型、长时间运行", "端到端 FPS、P95 延迟、W、温度"],
        ["统计", "多 seed、预注册主要指标、外部测试、置信区间", "均值±标准差、效应量"],
    ], [3.0, 8.0, 5.5])
    doc.add_heading("19.4 必做消融实验", level=2)
    add_bullets(doc, [
        "随机帧划分 vs 视频分组划分：量化潜在相邻帧泄漏影响。",
        "普通损失 vs Focal/Class-Balanced Loss：检验少数类收益。",
        "无跟踪逐帧累计 vs 跟踪去重计数：比较实际计数误差。",
        "仅视觉 vs 视觉+天气+蜂箱重量：比较蜂群强度预测。",
        "原始模型 vs FP16/INT8：比较精度、速度和功耗。",
    ])

    doc.add_heading("20. 基于当前 VS Code 项目的落地路线", level=1)
    add_table(doc, ["阶段", "在当前项目上做什么", "预计产物"], [
        ["第 1 阶段", "保留现有 YOLOv10X 基线，新增按视频分组的数据准备脚本", "严格 split manifest 与新基线"],
        ["第 2 阶段", "扩展 predict.py 为 track_video.py，加入 ByteTrack 和过线计数", "轨迹 CSV、进出统计和计数视频"],
        ["第 3 阶段", "人工标注一部分轨迹和方向，建立计数真值", "IDF1/HOTA/Count MAE"],
        ["第 4 阶段", "采集蜂群检查、天气、重量与授粉结果", "多模态时序数据集"],
        ["第 5 阶段", "训练蜂群强度/授粉预测模型并做跨蜂场验证", "真正回答论文标题的问题"],
        ["第 6 阶段", "TensorRT/Jetson 部署和网页展示", "可用原型与成本报告"],
    ], [2.8, 9.0, 4.7])
    add_note(doc, "优先级建议", "最先做“视频分组划分 + 跟踪过线计数”。它们直接修复论文最关键的评估风险和功能缺口，并且可以在现有代码与数据基础上实施。")

    doc.add_heading("21. 对初学者最重要的十个结论", level=1)
    add_steps(doc, [
        "论文最强贡献是公开真实蜂箱数据和证明三类检测可行。",
        "YOLOv10 是速度和整体性能最均衡的模型；Faster R-CNN 更慢但高置信时稳。",
        "94% 数据属于一个类别，所以不能只看总体 Accuracy。",
        "15×15 像素花粉团、小目标、密集遮挡是任务的真正难点。",
        "检测一帧中的蜜蜂，不等于统计了唯一进出个体。",
        "带花粉工蜂是授粉活动的代理变量，不等于直接测得授粉效率。",
        "论文没有公开逐帧划分，按视频分组评估会更可信。",
        "单蜂场高分不保证换地区、蜂种、蜂箱仍然高分。",
        "统计显著只说明模型有差异，不自动证明每一对模型都有差异。",
        "下一步最有价值的创新是：严格划分、跟踪计数、跨蜂场验证和生物学结果验证。",
    ])

    doc.add_heading("附录 A：论文事实、分析判断和未来建议如何区分", level=1)
    add_table(doc, ["类型", "本文件中的例子", "可信边界"], [
        ["论文事实", "4,590 帧、79,212 框、YOLO Accuracy 93.9%", "直接来自论文正文/表格"],
        ["复现事实", "本地 seed 50 测试 mAP@0.5:0.95=0.6374", "来自当前项目的固定实验"],
        ["批判性判断", "相邻帧随机划分可能导致性能偏乐观", "基于方法描述的风险，需要新实验确认"],
        ["未来建议", "加入 ByteTrack、过线计数和蜂群强度真值", "尚未完成，是下一步研究方案"],
    ], [3.5, 8.0, 5.0])

    doc.add_heading("附录 B：文献与数据入口", level=1)
    doc.add_paragraph("论文：Chaudhary, P. et al. Estimating colony strength and pollination efficiency in honey bees using a novel dataset and deep learning-based models. Smart Agricultural Technology 14 (2026) 102005. DOI: 10.1016/j.atech.2026.102005.")
    doc.add_paragraph("官方数据 DOI：10.54718/JCHW9401\n官方数据页面：https://scholarsjunction.msstate.edu/gri-publications/4/\n本地原文：/jzk-model/pdf-paper/1-s2.0-S2772375526002285-main.pdf")
    doc.add_paragraph("本分析以论文 15 页全文、论文表格和当前复现项目结果为基础。原论文为开放获取 CC BY 许可；本文件使用概述、解释和批判性分析，没有替代原文。")
    return doc


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = build_document()
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
