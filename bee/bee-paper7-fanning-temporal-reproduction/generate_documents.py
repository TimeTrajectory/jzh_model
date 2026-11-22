#!/usr/bin/env python3
"""Generate Chinese VS Code manual, professional paper analysis, combined report and PDF."""
from pathlib import Path
from datetime import date
import json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Cm, Inches, Pt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parent; RESULTS=ROOT/'results'; DOCS=ROOT/'docs'; REPORTS=ROOT/'reports'; ASSETS=ROOT/'assets'; FONT=Path('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')

def load(name):
 p=RESULTS/name
 return json.loads(p.read_text()) if p.exists() else None

def new_doc(title,subtitle):
 d=Document(); section=d.sections[0]; section.top_margin=section.bottom_margin=Cm(2); section.left_margin=section.right_margin=Cm(2.1)
 for name,size in [('Normal',10.5),('Title',22),('Heading 1',16),('Heading 2',13)]:
  style=d.styles[name]; style.font.name='Microsoft YaHei'; style._element.rPr.rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia','微软雅黑'); style.font.size=Pt(size)
 p=d.add_paragraph(style='Title'); p.alignment=1; p.add_run(title); p=d.add_paragraph(); p.alignment=1; p.add_run(subtitle); d.add_paragraph(f'生成日期：{date.today()}').alignment=1; d.add_page_break(); return d

def table(d,heads,rows):
 t=d.add_table(rows=1,cols=len(heads)); t.style='Table Grid'
 for i,x in enumerate(heads): t.rows[0].cells[i].text=str(x)
 for row in rows:
  cells=t.add_row().cells
  for i,x in enumerate(row): cells[i].text=str(x)
 return t

def bullets(d,items):
 for item in items: d.add_paragraph(item,style='List Bullet')

def code(d,text):
 run=d.add_paragraph().add_run(text); run.font.name='Consolas'; run.font.size=Pt(9)

def metrics_rows():
 rows=[]
 for enc in ('rgb','tsg','tem'):
  x=load(f'metrics_yolo11n_{enc}.json')
  if x: rows.append([enc.upper(),f"{x['precision']:.4f}",f"{x['recall']:.4f}",f"{x['map50']:.4f}",f"{x['map50_95']:.4f}"])
 return rows

def chart():
 rows=metrics_rows()
 if not rows:return None
 ASSETS.mkdir(exist_ok=True); out=ASSETS/'encoding_comparison.png'; labels=[r[0] for r in rows]; m50=[float(r[3]) for r in rows]; m95=[float(r[4]) for r in rows]
 x=range(len(rows)); fig,ax=plt.subplots(figsize=(7,4)); ax.bar([i-.18 for i in x],m50,.36,label='mAP@0.50'); ax.bar([i+.18 for i in x],m95,.36,label='mAP@0.50:0.95'); ax.set_xticks(list(x),labels); ax.set_ylim(0,1); ax.grid(axis='y',alpha=.25); ax.legend(); fig.savefig(out,dpi=180,bbox_inches='tight'); plt.close(fig); return out

def manual():
 d=new_doc('第七篇论文复现项目\nVS Code 结构与训练操作手册','YOLO11n · RGB/TSG/TEM · 官方扇风蜂数据')
 d.add_heading('1. 项目目标与证据边界',1); d.add_paragraph('本项目复现论文的核心因果比较：同一个检测模型在单帧 RGB、时序堆叠灰度 TSG、时序差分 TEM 下是否得到不同表现。官方数据和蜂箱隔离划分保持一致；首轮固定 YOLO11n，不覆盖论文全部 45 个模型组合。')
 d.add_heading('2. 目录与文件职责',1); table(d,['文件','作用'],[['prepare_remote_dataset.py','不保存 17.3 GB ZIP，Range 分块读取、缩放、校验'],['temporal_loader.py','训练时动态生成 TSG/TEM'],['encode_temporal.py','导出编码图用于检查'],['train.py','固定参数训练一个输入分支'],['evaluate.py','在 Hive 4 上评价并保存 JSON'],['run_experiments.sh','按 RGB、TSG、TEM 顺序执行'],['watch_and_train.sh','检查完整数据并按 RGB/TSG/TEM 自动训练、评估与生成报告'],['update_results.py','把指标写回 README/REPORT'],['generate_documents.py','生成 Word、PDF 和图表']])
 d.add_heading('3. VS Code 环境',1); code(d,'cd bee-paper7-fanning-temporal-reproduction\nbash setup.sh'); d.add_paragraph('在 VS Code 按 Ctrl+Shift+P，选择 Python: Select Interpreter，再选择 .venv/bin/python。用 nvidia-smi 检查显卡，用 .venv/bin/python -c "import torch; print(torch.cuda.is_available())" 检查 CUDA。')
 d.add_heading('4. 数据准备',1); code(d,'.venv/bin/python prepare_remote_dataset.py\ncat data/dataset_audit.json'); bullets(d,['完整 ZIP 17,336,965,310 字节，不写入本地。','保存 14,400 张训练帧和 3,600 张 Hive 4 验证帧；Hive 4 也用于早停和选权重。','原始 1920×1080 缩放为 1024×576。','空标签帧被保留，它们是重要负样本。','快速调试可加 --max-per-sequence 100，但这种结果不能当正式复现。'])
 d.add_heading('5. 时序编码检查',1); code(d,'.venv/bin/python encode_temporal.py tsg\n.venv/bin/python encode_temporal.py tem'); d.add_paragraph('正式训练无需运行这两条命令；动态加载器直接读取相邻文件。检查时应确认文件编号连续、B/G/R 通道顺序正确，视频段边界使用当前帧自身填充。')
 d.add_heading('6. 手动训练',1); code(d,'.venv/bin/python train.py rgb --epochs 50 --batch 32 --patience 15\n.venv/bin/python train.py tsg --epochs 50 --batch 32 --patience 15\n.venv/bin/python train.py tem --epochs 50 --batch 32 --patience 15'); bullets(d,['模型：YOLO11n；输入长边 1024，rect=True。','AdamW，lr0=0.001，momentum=0.9，seed=42。','平移 0.1、缩放 0.5、水平翻转 0.5、HSV V 0.2。','加速设置 patience=15；每 10 epoch 保存检查点。','显存不足时减小 batch，并在报告中记录改变。'])
 d.add_heading('7. 评价与结果位置',1); code(d,'.venv/bin/python evaluate.py rgb\n.venv/bin/python evaluate.py tsg\n.venv/bin/python evaluate.py tem'); bullets(d,['results/metrics_*.json：机器可读结果。','runs/train/*/weights/best.pt：最佳权重。','runs/eval/：混淆矩阵、PR 曲线和预测样例。','比较时先看 mAP50，再结合 Precision、Recall 和 mAP50:0.95。'])
 d.add_heading('8. 修改代码和扩展实验',1); table(d,['目标','建议'],[['复现论文中型模型','把 --model 改为 yolo11m.pt，保持其他参数'],['比较 YOLOv8','使用 yolov8n.pt 或 yolov8m.pt，新建独立 run 名'],['改变时间窗','修改 temporal_loader.py 的邻帧间隔，并写入运行元数据'],['留一蜂箱交叉验证','为每个蜂箱重建划分，报告均值和方差'],['边缘部署','导出 ONNX/TensorRT，并分开记录模型推理与前后处理耗时']])
 d.add_heading('9. 常见问题',1); bullets(d,['Zenodo 慢：脚本可重复运行，已存在图片会跳过。','找不到前后帧：确认文件名末尾是连续数字。','解释 Hive 4 分数：它未用于梯度更新，但被用于早停和权重选择；最终测试应使用训练期间不可见的新蜂箱。','TSG/TEM 无提升：检查通道次序、相邻帧间隔和视频段边界。','不能把扇风框直接解释为蜂群健康诊断，应结合温湿度和人工行为记录。'])
 return d

def analysis(combined=False):
 d=new_doc('第七篇论文详细分析与复现实验报告' if combined else '第七篇论文专业深度解析与写作评析','Evaluation of Single-Shot Object Detection Models for Identifying Fanning Behavior in Honeybees at the Hive Entrance')
 d.add_heading('1. 研究问题',1); d.add_paragraph('扇风蜂停在蜂箱入口并高速振翅，用空气流动调节温湿度或传播信息。单张图像只能看到姿态、翅膀模糊和腹部抬起，容易与守卫、行走、短暂振翅混淆。论文的问题是：把极短时间窗编码到普通三通道图像后，标准 YOLO 是否能更可靠地定位正在扇风的蜂。')
 d.add_heading('2. 数据与场景',1); table(d,['项目','论文报告'],[['蜂箱','4 个'],['视频','10 分钟，30 FPS'],['帧','18,000'],['含扇风行为帧','15,111（84%）'],['扇风蜂实例','57,597'],['分辨率','1920×1080'],['模型输入','1024×576'],['训练/验证','Hive 1–3 / Hive 4']]); d.add_paragraph('蜂箱级隔离比随机拆帧更严格，因为连续视频背景几乎不变。Hive 4 蜂密度更高，因而测试同时包含背景域偏移和拥挤程度变化。论文把同一个 Hive 4 描述为 validation/testing，没有再给独立测试集，这是结果解释时必须保留的限制。')
 d.add_heading('3. RGB、TSG 与 TEM',1); table(d,['输入','B 通道','G 通道','R 通道','含义'],[['RGB','蓝色','绿色','红色','当前帧外观'],['TSG','I(n−1)','I(n)','I(n+1)','相邻灰度帧顺序'],['TEM','|I(n)−I(n−1)|','I(n)','|I(n)−I(n+1)|','显式突出运动']]); d.add_paragraph('TSG 让卷积核从通道差异中学习运动方向和变化；TEM 先做绝对差分，压低静态背景。两者都不改变 YOLO 结构，工程代价小，但只覆盖三个相邻帧，不能表达长时间行为持续性。绝对差分也会把相机抖动、阴影变化和行走放大。')
 d.add_heading('4. 模型与训练',1); bullets(d,['论文比较 YOLOv8、YOLO11、YOLO12 的 n/s/m/l/x。','AdamW，初始学习率 0.001，momentum 0.9。','最多 1000 epoch，patience 100，通常 100–200 epoch 收敛。','平移 ±10%、scale gain 0.5、水平翻转 0.5、亮度 hsv_v=0.2。','检测损失权重 box=7.5、cls=0.5、DFL=1.5。','RTX 4080 Super 16 GB；软件为 Ultralytics 8.3.80、Python 3.12.9、Torch 2.5.1、CUDA 12.6。'])
 d.add_heading('5. 论文实验结论',1); d.add_paragraph('图中结果显示，时序编码通常带来约 5–10 个 mAP50 百分点提升。文中举例：YOLOv8m 从 RGB 约 76% 提升到 TSG 约 81%；YOLO11m 从约 76% 提升到约 84%；YOLO12l 从 RGB 约 74% 提升到 TSG 约 84%。最佳组合接近 85% mAP50。由于论文用曲线而非完整数值表呈现大多数模型，这些是图文报告值，不应伪装成逐位可比表格。')
 d.add_heading('6. 边缘部署结论',1); d.add_paragraph('RTX 4080 上全部模型达到或超过 30 FPS。Jetson AGX Orin 上，FP16 的 YOLOv8n、YOLO11n 和 INT8 的若干 nano/small 模型接近或超过 30 FPS，但 INT8 小模型可能损失 1–5 个百分点，nano 甚至超过 10 个百分点。论文还把预处理和后处理延迟分开记录，这是系统论文写作中值得学习的做法。')
 d.add_heading('7. 创新点',1); bullets(d,['公开了专门面向扇风行为的大规模框标注数据。','用三通道兼容编码把时间信息引入现成检测器，无需改动网络。','同时比较三代 YOLO、五种规模、三种输入，形成精度速度曲线。','把桌面 GPU、Jetson 精度模式、端到端延迟和功耗放在同一部署讨论中。','采用蜂箱隔离划分，主动测试新场景泛化。'])
 d.add_heading('8. 方法学局限',1); bullets(d,['Hive 4 同时承担验证和测试；本项目用其早停并选择 best.pt，因此它不是独立测试集。','只有四个蜂箱，无法估计蜂箱间方差和季节变化。','框标签把行为压缩成单帧空间目标，没有事件起止和持续时长。','n−1/n/n+1 的实际时间跨度固定为约 67 ms，未系统比较步长。','文章没有发布全部 45 个组合的精确数值、随机种子重复或置信区间。','INT8 校准集和量化流程细节不足，部署数值不易逐位复制。','扇风与温湿度、蜂群状态的生物学关系没有在本数据中直接验证。'])
 d.add_heading('9. 本地复现设计与差异',1); d.add_paragraph('本项目使用官方 Zenodo 数据、Hive 1–3/Hive 4 划分和 1024×576 图像，固定 YOLO11n 做三组受控实验。由于工作盘不足以保存 17.3 GB ZIP，使用 Range 流式读取并立即缩放；TSG/TEM 在训练加载时动态生成。当前运行环境为 RTX 4090、Torch 2.1.2、CUDA 12.1、Ultralytics 8.4.163，与论文软件栈不同。首轮目标是验证输入编码效应，不是重建全部 45 组曲线。')
 d.add_heading('10. 本地实验结果',1); rows=metrics_rows()
 if rows: table(d,['输入','Precision','Recall','mAP50','mAP50:0.95'],rows); table(d,['输入','早停轮数','训练耗时','训练期最佳 mAP50 轮次'],[['RGB','24','19.5 分钟','9'],['TSG','22','19.8 分钟','7'],['TEM','28','27.2 分钟','5']]); d.add_paragraph('训练采用最多 50 epoch、batch 32、patience 15。Hive 4 同时用于逐轮验证、早停和最佳检查点选择，因此这些最终数字是 Hive 4 验证结果，不是完全独立测试。TSG 比 RGB 高 13.38 个百分点，但单模型、单随机种子与缩短训练预算不足以支持普遍结论。')
 else: d.add_paragraph('正式训练正在运行。完成后本节由 results/metrics_yolo11n_*.json 自动填充。')
 if combined:
  p=chart()
  if p: d.add_picture(str(p),width=Inches(6.2))
 d.add_heading('11. 更强的创新方案',1); table(d,['研究方向','具体设计','可验证收益'],[['多时间尺度','使用 ±1、±3、±5 帧差分并做轻量注意力融合','区分短暂振翅和持续扇风'],['事件检测','标注行为起止，输出 tube 或 track-level 状态','报告事件 F1、持续时长误差'],['留一蜂箱验证','四折 leave-one-hive-out，并跨季节复测','给出泛化均值和置信区间'],['多模态','同步温湿度、声音、风速与视觉','验证扇风是否对应真实热应激'],['相机稳像','用全局运动补偿后再差分','减少阴影和抖动伪运动'],['主动学习','优先复核低置信度和行为边界帧','降低标注不一致'],['蒸馏与量化','从 YOLO11m-TSG 蒸馏到 n/s，再做量化感知训练','改善 Jetson 精度速度权衡']])
 d.add_heading('12. 论文写作可借鉴之处',1); bullets(d,['贡献列表明确对应数据、方法比较和部署。','方法部分给出通道定义公式和图示，读者容易实现。','精度速度曲线比只给最好模型更适合工程决策。','讨论部分把误差来源落到遮挡、行为变异和标注一致性。','改进时应补充完整结果表、统计重复、校准协议和数据清单哈希。'])
 d.add_heading('13. 结论',1); d.add_paragraph('论文最有价值的结论是：对扇风这种由运动定义的行为，短时间信息比单纯增加单帧模型复杂度更关键。TSG/TEM 是低成本、可实时的入口，但检测到扇风蜂仍不等于诊断蜂群健康；真正的精准养蜂系统还需要事件级评价、跨蜂箱验证和环境传感器证据。')
 return d

def make_pdf():
 REPORTS.mkdir(exist_ok=True); out=REPORTS/'第七篇论文复现结果报告.pdf'; font='Helvetica'
 if FONT.exists(): pdfmetrics.registerFont(TTFont('CN',str(FONT))); font='CN'
 styles=getSampleStyleSheet(); h=ParagraphStyle('h',parent=styles['Heading2'],fontName=font,textColor=colors.HexColor('#315C3B')); b=ParagraphStyle('b',parent=styles['BodyText'],fontName=font,leading=15); story=[Paragraph('第七篇论文复现结果报告',ParagraphStyle('t',parent=styles['Title'],fontName=font)),Spacer(1,10),Paragraph('复现范围',h),Paragraph('官方扇风蜂数据，固定 YOLO11n，比对 RGB、TSG、TEM。TSG/TEM 在加载时动态生成，Hive 4 不参与梯度更新，但会用于每轮验证、早停和 best.pt 选择，因此结果属于验证表现，不是独立测试。',b)]
 rows=metrics_rows()
 if rows:
  data=[['输入','P','R','mAP50','mAP50-95']]+rows; t=Table(data); t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),font),('GRID',(0,0),(-1,-1),.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DCEAD8'))])); story += [Paragraph('本地结果',h),t,Paragraph('加速训练轮数：RGB 24、TSG 22、TEM 28（均早停）；Hive 4 同时用于验证和选权重，结果不是独立测试。',b)]
 else: story += [Paragraph('本地结果',h),Paragraph('正式训练正在运行，完成后重新生成本文档。',b)]
 story += [Paragraph('解释边界',h),Paragraph('首轮只固定 YOLO11n 验证时间编码效应，不等于论文完整 45 组实验。论文 Hive 4 同时作为验证和测试，本地结果也应按该口径解释。',b)]
 SimpleDocTemplate(str(out),pagesize=A4).build(story); return out

def main():
 DOCS.mkdir(exist_ok=True); a=DOCS/'第七篇论文_VSCode项目结构与训练操作手册.docx'; manual().save(a); b=DOCS/'第七篇论文_专业深度解析与论文写作评析.docx'; analysis().save(b); c=DOCS/'第七篇论文_详细分析与训练复现实验报告.docx'; analysis(True).save(c); p=make_pdf(); print(a,b,c,p,sep='\n')

if __name__=='__main__':main()
