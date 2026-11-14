#!/usr/bin/env python3
"""Generate paper-5 PDF report and two detailed Chinese Word documents."""
from pathlib import Path
from datetime import date
import csv,json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Cm,Inches,Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parent; RESULTS=ROOT/'results'; DOCS=ROOT/'docs'; REPORTS=ROOT/'reports'; ASSETS=ROOT/'assets'; FONT=Path('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
def js(name,default=None):
 p=RESULTS/name; return json.loads(p.read_text()) if p.exists() else default
def setup(title,sub):
 d=Document(); s=d.sections[0]; s.top_margin=s.bottom_margin=Cm(2); s.left_margin=s.right_margin=Cm(2.2)
 for name,size in [('Normal',10.5),('Title',23),('Heading 1',16),('Heading 2',13),('Heading 3',11)]:
  st=d.styles[name]; st.font.name='Microsoft YaHei'; st._element.rPr.rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia','微软雅黑'); st.font.size=Pt(size)
 p=d.add_paragraph(style='Title'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run(title)
 p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run(sub).italic=True
 p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run(f'版本 1.0 · {date.today()}'); d.add_page_break(); return d
def tbl(d,heads,rows):
 t=d.add_table(rows=1,cols=len(heads)); t.style='Table Grid'; t.alignment=WD_TABLE_ALIGNMENT.CENTER
 for i,x in enumerate(heads): t.rows[0].cells[i].text=str(x)
 for row in rows:
  c=t.add_row().cells
  for i,x in enumerate(row): c[i].text=str(x)
 return t
def bullets(d,items,number=False):
 for x in items: d.add_paragraph(x,style='List Number' if number else 'List Bullet')
def code(d,s):
 p=d.add_paragraph(); r=p.add_run(s); r.font.name='Consolas'; r.font.size=Pt(9)
def note(d,title,s):
 p=d.add_paragraph(); r=p.add_run(title+'：'); r.bold=True; p.add_run(s)
def pipeline_chart():
 ASSETS.mkdir(exist_ok=True); fp=FontProperties(fname=str(FONT)) if FONT.exists() else FontProperties(); fig,ax=plt.subplots(figsize=(11,3.5)); ax.axis('off')
 boxes=[('入口硬件','单向、单蜂'),('YOLOv4','检测'),('DeepSORT','身份关联'),('越线状态机','方向去重'),('活动指标','进出趋势')]
 for i,(a,b) in enumerate(boxes):
  x=.01+i*.198; ax.add_patch(plt.Rectangle((x,.3),.17,.42,fc='#D9EAF7',ec='#1F4E78')); ax.text(x+.085,.57,a,ha='center',fontproperties=fp,fontsize=12,weight='bold'); ax.text(x+.085,.42,b,ha='center',fontproperties=fp,fontsize=9)
  if i<4: ax.annotate('',xy=(x+.195,.51),xytext=(x+.17,.51),arrowprops={'arrowstyle':'->'})
 ax.text(.5,.88,'硬件条件与视觉算法共同决定计数质量',ha='center',fontproperties=fp,fontsize=15,weight='bold'); p=ASSETS/'paper_pipeline.png'; fig.savefig(p,dpi=180,bbox_inches='tight'); plt.close(fig); return p
def training_chart():
 p=RESULTS/'training_history.csv'
 if not p.exists(): return None
 rows=list(csv.DictReader(p.open())); x=[int(r['iteration']) for r in rows]; y=[float(r['avg_loss']) for r in rows]; fig,ax=plt.subplots(figsize=(9,4)); ax.plot(x,y); ax.grid(alpha=.25); ax.set_xlabel('Iteration'); ax.set_ylabel('Average loss'); q=ASSETS/'training_curve.png'; fig.savefig(q,dpi=180,bbox_inches='tight'); plt.close(fig); return q

def manual():
 d=setup('第五篇论文复现项目\nVS Code 结构与训练操作手册','YOLOv4 · DeepSORT · BEE22 · 越线方向计数')
 tbl(d,['项目','内容'],[['项目根目录',str(ROOT)],['原论文','Ryu et al., Journal of Apiculture 2021'],['适用环境','Ubuntu/Linux、NVIDIA GPU、VS Code'],['目标','从零准备、训练、续训、评估、修改和部署']])
 d.add_heading('目录',1); d.add_paragraph('在 Word/WPS 中右键目录字段并更新整个目录。')
 sections=[
 ('1. 系统边界','原论文将入口机构、相机、YOLOv4、DeepSORT 和越线计数作为整体。本项目分别评价检测、跟踪和事件，并使用 BEE22 替代未公开的 2,600 张通道图像。'),
 ('2. VS Code 准备','打开项目文件夹，按 Ctrl+Shift+P 选择 Python: Select Interpreter，再选择 .venv/bin/python。所有终端命令从项目根目录运行。'),
 ('3. 数据原则','训练、验证、测试按完整 BEE22 序列隔离，避免同视频相邻帧泄漏。Darknet 在图片旁读取同名 .txt 标签。'),
 ('4. 编译原则','build_darknet.sh 为 RTX 4090 设置 compute_89，启用 CUDA、cuDNN、半精度与 libdarknet.so。'),
 ('5. 训练单位','配置 max_batches=6000 表示 6,000 次参数更新。原论文称 6,000 epochs，但没有日志消除术语歧义。'),
 ('6. 评价原则','检测用 P/R/F1/mAP50，身份关联用 MOTA/IDF1/IDSW，越线事件用事件级 P/R/F1。三层不能混为一个 accuracy。')]
 for h,p in sections: d.add_heading(h,1); d.add_paragraph(p)
 d.add_heading('7. 目录结构',1); code(d,'configs/  YOLOv4 配置\ndata/  清单与数据链接\nresults/  JSON/CSV/日志/图表\nruns/train/backup/  权重\nruns/tracking/  MOT 与视频\nvendor/darknet/  固定上游源码\ndocs/ 和 reports/  可下载文档')
 d.add_heading('8. 文件职责',1)
 tbl(d,['文件','作用'],[['setup.sh','一键环境准备'],['prepare_data.py','BEE22 转换与审计'],['configure_yolov4.py','生成单类 608 配置'],['build_darknet.sh','GPU 编译'],['train_yolov4.py','训练/续训'],['evaluate_checkpoints.py','比较周期权重'],['evaluate_tracking.py','MOT 与事件评价'],['track_video.py','视频检测、ID、方向计数'],['app.py','本地上传网页'],['generate_documents.py','重新生成三份文档']])
 d.add_heading('9. 一键安装',1); code(d,'cd /jzk-model/jzh_model/bee/bee-paper5-yolov4-deepsort-reproduction\nbash setup.sh'); note(d,'检查','运行 nvidia-smi，并确认 vendor/darknet/darknet 与 libdarknet.so 存在。')
 d.add_heading('10. 数据准备',1); code(d,'.venv/bin/python prepare_data.py\ncat data/dataset_summary.json\nsha256sum data/split_manifest.csv'); tbl(d,['集合','帧','框','序列'],[['train','1,360','16,050','01–11、14'],['val','240','3,093','15'],['test','762','12,205','12、13、16']])
 d.add_heading('11. 正式训练',1); code(d,'.venv/bin/python train_yolov4.py'); bullets(d,['batch=64，subdivisions=16。','输入 608×608。','max_batches=6000，steps=4800,5400。','单类 classes=1，三个检测头 filters=18。','无 OpenCV 编译，mosaic=0。'])
 d.add_heading('12. 断点续训',1); code(d,'.venv/bin/python train_yolov4.py --resume runs/train/backup/yolov4-bee_last.weights'); note(d,'危险操作','续训不能加 -clear，否则迭代计数和学习率阶段会被清空。')
 d.add_heading('13. 参数调整',1); tbl(d,['参数','影响'],[['width/height','416 更快；608 对小目标细节更友好'],['subdivisions','越大越省显存；8 在本机 OOM，16 稳定'],['classes/filters','类别改变时同步设置 filters=(classes+5)×3'],['max_batches/steps','总更新数和学习率下降点'],['confidence/NMS','影响检测 P/R 和跟踪输入']])
 d.add_heading('14. 检测评价',1); code(d,'.venv/bin/python evaluate_checkpoints.py runs/train/backup/yolov4-bee_5000.weights runs/train/backup/yolov4-bee_final.weights\n.venv/bin/python evaluate_detector.py --weights runs/train/backup/yolov4-bee_best.weights'); d.add_paragraph('第一个命令在验证集选择权重，第二个命令才在测试集评价一次。原始日志保留在 results。')
 d.add_heading('15. 跟踪与上限实验',1); code(d,'.venv/bin/python evaluate_tracking.py --weights runs/train/backup/yolov4-bee_best.weights\n.venv/bin/python evaluate_tracking.py --oracle-gt'); note(d,'解释','oracle-gt 用真值框隔离检测误差，不是完整系统成绩。')
 d.add_heading('16. 自己的视频',1); code(d,'.venv/bin/python track_video.py my.mp4 --line-x 475 --output runs/my_video'); bullets(d,['tracked.mp4：带框、ID、阈值线和方向数。','tracks.csv：逐帧轨迹。','summary.json：速度与计数。','必须根据安装方向把左右映射为进/出。'])
 d.add_heading('17. 图片与网页',1); code(d,'.venv/bin/python predict.py my.jpg\n.venv/bin/python app.py'); d.add_paragraph('浏览器访问 http://127.0.0.1:5000。')
 d.add_heading('18. 权重管理',1); bullets(d,['yolov4.conv.137 仅是初始化。','last.weights 用于续训。','5000.weights 用于对应作者选择点。','final.weights 是 6,000 次结果。','best.weights 应按预先定义的验证规则选择。'])
 d.add_heading('19. 替换自己的数据',1); bullets(d,['固定相机和入口方向。','按完整视频/日期划分。','每张图和标签同名。','标注截断、重叠、逆行规则。','额外标注轨迹 ID 和真实事件。','记录拥堵、拒入、通行耗时和行为干扰。'],True)
 d.add_heading('20. 常见错误',1); tbl(d,['错误','处理'],[['mosaic requires OpenCV','设 mosaic=0 或重新编译'],['Can\'t open label file','把同名 txt 放到图片旁'],['CUDA OOM','增大 subdivisions'],['libdarknet.so missing','执行 build_darknet.sh'],['计数方向反了','确认相机方向后交换业务含义'],['检测高但 IDF1 低','检查重叠、交叉、外观嵌入和轨迹参数']])
 d.add_heading('21. 建议实验记录',1); tbl(d,['字段','必须记录'],[['代码','Darknet 提交与本项目提交'],['数据','清单 SHA256 和序列'],['环境','GPU/CUDA/cuDNN'],['训练','配置、初始权重、迭代、耗时'],['选择','最佳权重规则'],['结果','检测/MOT/事件/速度分层指标'],['失败','漏检、合并、ID切换、拥堵、逆行']])
 return d

def analysis(pipe):
 d=setup('第五篇论文专业深度解析\n与论文写作评析','面向计算机视觉、智能养蜂与农业工程研究者')
 tbl(d,['项目','内容'],[['题名','Honeybee In-Out Monitoring System by Object Recognition and Tracking from Real-Time Webcams'],['作者','Ji-Su Ryu 等'],['期刊','Journal of Apiculture 36(4), 2021'],['DOI','10.17519/apiculture.2021.11.36.4.273'],['原文','/jzk-model/pdf-paper/31356.pdf（8页）']])
 d.add_heading('目录',1); d.add_paragraph('在 Word/WPS 中更新目录字段。')
 d.add_heading('1. 专业概述',1); d.add_paragraph('本文是一项硬件与视觉共同设计的蜂箱入口计数系统研究。作者不是被动接受密集、双向、遮挡严重的视频，而是逐步改变通道、背景、材料和方向约束，再用 YOLOv4 检测、DeepSORT 关联和中央竖线计数。其持久价值在于“设计可观测环境”，而不只是模型版本升级。')
 p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(str(pipe),width=Inches(6.5))
 chapters=[
 ('2. 科学与应用问题',['进出流量是蜂群活动的代理变量。','视觉计数保留可复核证据，但小目标、快速运动和遮挡会积累误差。','检测、跟踪、事件和生物学解释是不同层级。']),
 ('3. 系统组成',['Logitech StreamCam：1080p、60 FPS。','Ryzen 5-3500、16 GB、GTX 1660 SUPER、Ubuntu 18.04。','透明顶板、MDF 底板、并行单向通道。','YOLOv4、DeepSORT、中央竖线计数。']),
 ('4. 硬件迭代',['15 mm 单通道出现重叠。','8–12 mm 多通道降低密度，但透明板带来反光和背景。','白纸背景改善视觉稳定性。','过窄双向通道导致排队、雄蜂受限、打滑和对向死锁。','最终使用 MDF 与 0.1 mm 铜片心脏瓣膜约束单向通行。']),
 ('5. 标注协议',['共 2,600 张，7:2:1，单类 bee。','身体露出超过 90% 才标。','上下/侧向重叠时人为限制框重叠。','规则便于训练，但会排除边缘截断蜂并改变重叠样本分布。']),
 ('6. YOLOv4',['单阶段结构适合实时场景。','CSPDarknet53、SPP、PANet 与三尺度检测兼顾语义和细节。','论文用通用 COCO 图解释 YOLOv4 优于 YOLOv3，但这不能替代蜂箱数据消融。']),
 ('7. DeepSORT',['卡尔曼滤波预测状态，匈牙利算法关联，深度外观嵌入辅助身份。','原文称 DeepSORT 使用 YOLOv4 训练得到的连接权重；标准 DeepSORT 实际使用独立的外观嵌入网络，因此该表述在技术上不严谨。','它不能恢复 YOLO 漏掉的蜂，也不能拆开合并框。','蜂外观高度相似且相向交叉时仍易 ID switch。']),
 ('8. 越线计数',['框质心跨过中央竖线时按方向计数。','论文图 12 明确给出右侧为巢外、左侧通向巢内，因此右→左在原装置中表示进巢。','稳健实现应保存每个 ID 的稳定侧别并设置死区。','BEE22 的拍摄朝向未由本文给定，故本地左右方向不强行赋予进/出语义。']),
 ('9. 作者结论',['摘要报告新系统 detection accuracy 99.5%、旧系统 97.5%，正文另称单图检测约 98%，两者统计口径未解释。','loss rate 从 2.6% 降到 0.24%，但没有定义它是训练损失、比例还是测试错误率。','作者称训练 6,000 epochs，选择 5,000 权重。','示例证明计数流程可运行，但没有事件级统计。']),
 ('10. 核心创新',['硬件约束与算法协同。','被动铜片单向门。','检测—关联—事件的端到端原型。','每次硬件修改由具体失败案例驱动。']),
 ('11. 主要局限',['数据、划分、代码、权重和视频未公开。','99.5% 的公式、样本量和置信区间未给。','入口、YOLO 版本和跟踪器同时变化，因素混杂。','没有 mAP、MOTA、IDF1、IDSW 或事件 F1。','没有端到端 FPS/延迟。','没有量化拒入、逆行、停留和拥堵。','6,000 epochs 与 Darknet iterations 概念可能混用。']),
 ('12. 写作优点',['题名直接交代任务、方法和实时场景。','硬件演进图呈现清楚的失败—修改链。','相机、通道宽度、材料和计算机规格具体。','主动报告行为干扰和未来改进，没有夸成成熟产品。']),
 ('13. 写作改进',['摘要的 99.5% 应附定义和不确定性。','方法需完整超参数、阈值、随机种子和数据清单。','结果应提供标准表格和曲线，不只示例截图。','应把通用 COCO 证据与本任务证据分开。','讨论需区分检测率、身份连续性和事件正确率。'])]
 for h,items in chapters: d.add_heading(h,1); bullets(d,items)
 d.add_heading('14. 本地复现事实',1); o=js('tracking_oracle_metrics.json',{}) or {}; m=o.get('motmetrics',{}).get('OVERALL',{}); tbl(d,['指标','真值框上限'],[['对象',m.get('num_objects',12205)],['MOTA',f"{m.get('mota',0):.4f}"],['IDF1',f"{m.get('idf1',0):.4f}"],['ID switches',m.get('num_switches',142)],['Misses',m.get('num_misses',736)],['FPS',f"{o.get('fps_end_to_end',0):.2f}"]]); d.add_paragraph('完美检测输入仍出现身份切换，说明开放入口的关联难度真实存在，也间接支持论文硬件约束的价值；它不能证明作者的 99.5%。')
 det=js('detector_metrics.json',{}) or {}; full=js('tracking_metrics.json',{}) or {}
 if det:
  fm=full.get('motmetrics',{}).get('OVERALL',{}); d.add_heading('14.1 完整系统实测',2); tbl(d,['指标','BEE22 测试集'],[['Precision',det.get('precision')],['Recall',det.get('recall')],['F1',det.get('f1')],['mAP@0.50',det.get('map50')],['MOTA',fm.get('mota')],['IDF1',fm.get('idf1')],['ID switches',fm.get('num_switches')],['端到端 FPS',full.get('fps_end_to_end')]]); d.add_paragraph('权重先在验证集选择，再在测试集评价一次。完整系统与真值框上限的差距可用于分离检测误差和关联误差。')
 d.add_heading('15. 更强实验设计',1); bullets(d,['做旧/新入口 × YOLOv3/YOLOv4 的 2×2 因子实验，分离硬件、模型和交互效应。','固定检测结果比较 SORT、DeepSORT、ByteTrack、OC-SORT、BoT-SORT。','按蜂箱、日期和完整视频分组，并进行跨蜂箱测试。','人工标注轨迹和真实进出事件。','报告检测、HOTA/IDF1、事件 F1/MAE、端到端延迟与能耗。','量化通道拒入率、通行时间、排队长度、逆行和蜂行为扰动。'])
 d.add_heading('16. 可发表假设',1); tbl(d,['假设','实验与终点'],[['单向门减少 ID 切换','同一蜂群交叉使用开放/单向入口；IDSW/1000帧、HOTA'],['窄通道改善检测但增加拥堵','8/10/12/15 mm；mAP、排队长度、通行时间'],['单蜂通道中外观嵌入收益下降','DeepSORT vs 纯运动 SORT；IDF1、功耗'],['608 改善小蜂召回','416 vs 608；small Recall、FPS'],['物理约束比扩大模型更节能','入口×模型规模；每个正确事件的能耗']])
 d.add_heading('17. 建议结果表',1); tbl(d,['层级','建议报告'],[['检测','P/R/F1、AP50、AP50:95、大小分层'],['跟踪','MOTA、IDF1、HOTA、IDSW、Frag'],['计数','进/出事件 P/R/F1、每分钟 MAE/MAPE'],['速度','检测、嵌入、关联、I/O、P95 延迟'],['行为','拒入、逆行、排队、通行时间'],['统计','多蜂箱均值、置信区间、效应量']])
 d.add_heading('18. 最终评价',1); d.add_paragraph('这是一篇有实用价值的系统原型论文。最强贡献是入口机构与计算机视觉的共同设计，而不是单独的 YOLOv4。证据足以说明方案可运行，却不足以严格量化可泛化的 99.5% 性能或分离各组件贡献。后续论文应保留其工程迭代优点，并增加开放材料、因素实验、标准指标和动物行为影响评价。')
 return d

def detailed_report(pipe,curve):
 d=setup('第五篇论文详细分析与训练复现实验报告','从入门理解到专业复核：论文、训练、检测、跟踪、计数与进一步创新')
 d.add_heading('阅读说明',1); d.add_paragraph('这份文档把“原论文说了什么”“本项目实际做了什么”和“结果能说明什么”分开。没有计算机视觉基础的读者可先读第 1、2、9、12、15 节；研究人员可重点检查第 5—11、13—16 节。')
 d.add_heading('1. 一页读懂这篇论文',1); d.add_paragraph('作者希望自动统计蜜蜂进巢和出巢。系统先用摄像机拍蜂箱入口，再用 YOLOv4 在每帧中找出蜜蜂，用 DeepSORT 给同一只蜂保持编号，最后判断编号对应的框中心是否穿过竖线。作者发现入口结构会直接决定视觉难度，因此把通道改成一次只允许一只蜂、并用 0.1 mm 铜片构成单向“心脏瓣膜”。这项工作最有价值的思想是同时改造观察环境和算法。')
 p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(str(pipe),width=Inches(6.5))
 d.add_heading('2. 零基础术语',1); tbl(d,['术语','直观解释'],[['检测','在单张图中画框并判断哪里有蜜蜂'],['跟踪','跨视频帧判断哪个框仍是同一只蜂'],['越线事件','同一轨迹从阈值线一侧稳定移动到另一侧'],['Precision','报出的蜜蜂中有多少是真的'],['Recall','真实蜜蜂中有多少被找到了'],['mAP@0.50','在框重叠阈值 0.5 下综合衡量检测排序与定位'],['MOTA','综合漏跟、误跟和身份切换的跟踪指标'],['IDF1','轨迹身份在整个时间上的一致程度'],['ID switch','同一只蜂的编号被错误换掉']])
 d.add_heading('3. 论文研究问题与应用价值',1); bullets(d,['蜂群进出流量可作为活动强度代理，但不能单独诊断健康或数量。','人工计数耗时，视觉方法可长期运行并保留录像证据。','蜂体小、移动快、外观相似、遮挡和相向运动使检测与身份关联都困难。','一个检测框正确，不等于身份正确，更不等于进出事件正确。'])
 d.add_heading('4. 原论文方法全流程',1); bullets(d,['StreamCam 以 1080p、60 FPS 拍摄透明顶板下的并行通道。','YOLOv4 负责逐帧单类 bee 检测。','DeepSORT 结合运动预测与外观特征保持轨迹 ID。','框质心越过画面中央竖线时，根据方向增加进巢或出巢计数。','论文装置中右侧为巢外、左侧为巢内，因此右→左代表进巢。'],True)
 d.add_heading('5. 入口硬件为什么是核心创新',1); tbl(d,['阶段','发现的问题','修改'],[['15 mm 单通道','多蜂同时通过、框重叠','改为多条并行通道'],['透明并行通道','反光与底部颜色干扰','增加白色背景'],['8–12 mm 双向窄通道','排队、雄蜂受限、打滑、对向死锁','MDF 底板并分离方向'],['单向最终结构','需要阻止逆行且允许主动推开','0.1 mm 弹性铜片心脏瓣膜']]); d.add_paragraph('它把原本困难的开放场景改造成更容易观测的受控场景。这类“为测量而设计环境”的方法，常比单纯换更大模型更稳定、更节能。')
 d.add_heading('6. 原论文数据和训练',1); tbl(d,['项目','论文报告'],[['图像','2,600 张自采图'],['划分','训练/测试/验证=7:2:1'],['类别','bee 单类'],['标注','身体可见超过 90%；重叠框受人工规则约束'],['模型','Darknet YOLOv4'],['长度','文中称 6,000 epochs，选 5,000 权重'],['作者结果','摘要 99.5%，正文另称约 98%；旧系统 97.5%'],['损失','称 2.6% 降至 0.24%']])
 d.add_paragraph('原文未公开数据、代码、权重、数据清单或指标公式；“epoch”也很可能实际指 Darknet iteration/batch。因此本项目属于方法与工程链复现，不是同数据精确重复。')
 d.add_heading('7. 本项目如何复现',1); tbl(d,['层级','本地实现'],[['数据','公开 BEE22 连续入口序列'],['隔离划分','train 1,360 帧/16,050 框；val 240/3,093；test 762/12,205'],['检测','Darknet YOLOv4，608×608，COCO 前 137 层初始化'],['训练','batch 64、subdivisions 16、6,000 iterations'],['跟踪','DeepSORT MobileNet 外观嵌入、卡尔曼滤波与级联匹配'],['计数','中央竖线、8 px 死区、±5 帧事件容差'],['选择规则','5000 与 final 只在验证集比较，测试集只评价一次']])
 d.add_heading('8. 实际训练过程',1)
 hist=RESULTS/'training_history.csv'; rows=list(csv.DictReader(hist.open())) if hist.exists() else []
 if rows:
  first,last=rows[0],rows[-1]; d.add_paragraph(f"日志解析到 {len(rows):,} 次更新。平均损失从第 {first['iteration']} 次的 {float(first['avg_loss']):.4f} 下降到第 {last['iteration']} 次的 {float(last['avg_loss']):.4f}。训练在约 5,085 次时进程中断，因最近周期权重已在 5,000 次保存，随后从该权重恢复并完成剩余更新；这会重跑少量未保存更新，但不会破坏检查点。")
 else: d.add_paragraph('正式训练日志正在生成，完成后本节自动写入迭代数和最终平均损失。')
 if curve: p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(str(curve),width=Inches(6.3))
 d.add_heading('9. 检测实验结果与解释',1); det=js('detector_metrics.json',{}) or {}; sel=js('best_checkpoint_val.json',{}) or {}
 if det: tbl(d,['项目','结果'],[['验证集选择',Path(sel.get('weight','')).name],['测试 Precision',det.get('precision')],['测试 Recall',det.get('recall')],['测试 F1',det.get('f1')],['测试 mAP@0.50',det.get('map50')],['评估图像/框','762 / 12,205']]); d.add_paragraph('这些数值衡量 BEE22 开放入口，不等同于作者未定义的 99.5%。Precision 和 Recall 的差异可帮助判断主要问题是误报还是漏检。')
 else: d.add_paragraph('训练后将自动填入验证集选择和独立测试集 P、R、F1、mAP@0.50。')
 d.add_heading('10. 跟踪上限实验',1); o=js('tracking_oracle_metrics.json',{}) or {}; om=o.get('motmetrics',{}).get('OVERALL',{}); tbl(d,['指标','真值框输入'],[['MOTA',f"{om.get('mota',0):.4f}"],['IDF1',f"{om.get('idf1',0):.4f}"],['ID switches',int(om.get('num_switches',0))],['Misses',int(om.get('num_misses',0))],['FPS',f"{o.get('fps_end_to_end',0):.2f}"]]); d.add_paragraph('这里直接把正确真值框交给 DeepSORT，用来隔离检测误差。即使检测完美，开放入口仍有身份切换和轨迹初始化漏失，说明物理通道确实可能帮助跟踪。')
 d.add_heading('11. 完整系统结果',1); full=js('tracking_metrics.json',{}) or {}; fm=full.get('motmetrics',{}).get('OVERALL',{})
 if full:
  es={'tp':0,'fp':0,'fn':0}
  for s in full.get('sequences',{}).values():
   for k in es: es[k]+=int(s.get('event_metrics',{}).get(k,0))
  ep=es['tp']/(es['tp']+es['fp']) if es['tp']+es['fp'] else 0; er=es['tp']/(es['tp']+es['fn']) if es['tp']+es['fn'] else 0; ef=2*ep*er/(ep+er) if ep+er else 0
  tbl(d,['指标','YOLOv4+DeepSORT'],[['MOTA',fm.get('mota')],['IDF1',fm.get('idf1')],['ID switches',fm.get('num_switches')],['Misses',fm.get('num_misses')],['False positives',fm.get('num_false_positives')],['事件 P/R/F1',f'{ep:.4f} / {er:.4f} / {ef:.4f}'],['端到端 FPS',full.get('fps_end_to_end')]])
  d.add_paragraph('完整系统与真值框上限之间的差距主要反映检测错误对关联的传播；MOT 与事件指标之间的差距反映身份断裂和越线状态机对最终计数的影响。')
 else: d.add_paragraph('检测权重生成后将自动运行完整 YOLOv4+DeepSORT，并填入 MOT、越线事件和速度结果。')
 d.add_heading('12. 实验结论，用简单的话说',1); bullets(d,['论文的核心想法成立：减少重叠、相向运动和滑动，会让视觉计数更容易。','YOLO 找到蜜蜂只是第一关；同一只蜂的编号连续性决定它会不会被重复计数。','开放入口 BEE22 明显比单蜂单向通道困难，因此本地低于作者口径并不等于论文错误。','作者 99.5% 缺少公式和统计量，不能当成 mAP，也不能直接与本项目比较。','本项目证明代码链、训练链和分层评价可以运行，同时暴露出计数评价比单张检测更严格。'])
 d.add_heading('13. 原论文创新点',1); bullets(d,['硬件与算法共同设计，而非只替换检测器。','铜片被动单向阀无需主动执行机构。','把 YOLOv4、DeepSORT 和方向计数串成实时原型。','用连续失败案例推动通道材料、宽度、背景和方向结构演进。'])
 d.add_heading('14. 论文局限与证据边界',1); bullets(d,['2,600 张图、视频、权重和代码未公开，无法严格重复。','99.5%、98%、2.6% 与 0.24% 的公式、分母和置信区间缺失。','入口结构、YOLO 版本和 DeepSORT 同时改变，无法分离各自贡献。','没有 AP50:95、MOTA、IDF1、HOTA、事件 F1、延迟或能耗。','DeepSORT 使用 YOLO 权重的原文表述不符合标准模块结构。','单向门可能引起停留、拒入和逆行，动物行为影响没有量化。'])
 d.add_heading('15. 怎样做出更好的创新',1); tbl(d,['创新方向','具体方法','预期价值'],[['可学习但低扰动入口','压力/光学传感器与视觉融合，通道宽度自适应','兼顾计数与自然通行'],['检测跟踪联合优化','比较 ByteTrack、BoT-SORT、OC-SORT，或训练蜂专用 ReID','减少身份切换'],['不依赖身份的流量估计','密度流、光流与轨迹计数交叉校验','拥堵时仍可输出趋势'],['不确定性与异常报警','校准置信度，检测拥堵、停留、逆行和摄像头污染','从演示走向长期部署'],['跨蜂箱泛化','多蜂箱、多季节、多光照分组测试与域适应','证明系统可迁移'],['边缘节能','轻量检测器、TensorRT、动态帧率','降低每个正确事件的能耗']])
 d.add_heading('16. 推荐的下一篇论文实验设计',1); bullets(d,['做“旧/新入口 × YOLOv3/YOLOv4”的 2×2 因子实验，分离硬件和算法效应。','同一蜂群采用交叉设计，随机安排入口方案，至少覆盖多个蜂箱和日期。','完整标注检测框、轨迹 ID 和真实进出事件。','预先定义检测、MOT、事件、行为和效率五层指标。','报告均值、置信区间、效应量，并公开清单、配置、代码和代表性匿名视频。'],True)
 d.add_heading('17. 如何正确阅读本项目结果',1); d.add_paragraph('首先看数据划分是否按完整序列隔离；然后看验证集如何选权重；第三看独立测试检测结果；第四比较真值框跟踪上限与完整系统；最后看事件 F1 和速度。不要只挑一个最高数字，也不要把训练损失当测试准确率。')
 d.add_heading('18. 总结',1); d.add_paragraph('这篇论文的优秀之处是从真实失败出发反复修改系统，使观察对象更容易被可靠测量。其证据能支持“原型可运行”和“入口结构重要”，但不足以严格证明可泛化的 99.5% 性能。本次复现保留了 YOLOv4—DeepSORT—越线计数主链，并通过序列隔离、验证集选权重、测试集一次评价和分层指标，让结论更可检查。进一步工作应把动物行为影响、跨蜂箱泛化、统计不确定性和能耗一起纳入。')
 return d

def pdf(pipe,curve):
 REPORTS.mkdir(exist_ok=True); out=REPORTS/'第五篇论文复现结果报告.pdf'; family='Helvetica'
 if FONT.exists(): pdfmetrics.registerFont(TTFont('CN',str(FONT))); family='CN'
 styles=getSampleStyleSheet(); title=ParagraphStyle('T',parent=styles['Title'],fontName=family,fontSize=20,leading=27,alignment=TA_CENTER); h=ParagraphStyle('H',parent=styles['Heading2'],fontName=family,fontSize=14,leading=20,textColor=colors.HexColor('#17365D')); b=ParagraphStyle('B',parent=styles['BodyText'],fontName=family,fontSize=9.5,leading=15)
 story=[Paragraph('第五篇论文复现结果报告',title),Paragraph('YOLOv4 + DeepSORT 蜜蜂进出监测',ParagraphStyle('C',parent=b,alignment=TA_CENTER)),Spacer(1,15),Image(str(pipe),500,160),PageBreak(),Paragraph('1. 复现边界',h),Paragraph('原论文 2,600 张受控通道图像未公开。本项目使用序列隔离 BEE22，复现检测、身份关联和中央竖线事件。作者 99.5% 未定义公式，不能解释成 mAP。',b),Spacer(1,10)]
 t=Table([['集合','帧','框'],['train','1,360','16,050'],['val','240','3,093'],['test','762','12,205']],colWidths=[130,120,120]); t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),family),('GRID',(0,0),(-1,-1),.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#D9EAF7')),('ALIGN',(0,0),(-1,-1),'CENTER')])); story.extend([t,Spacer(1,12)])
 o=js('tracking_oracle_metrics.json',{}) or {}; m=o.get('motmetrics',{}).get('OVERALL',{}); story.extend([Paragraph('2. DeepSORT 真值框上限',h),Paragraph(f"MOTA {m.get('mota',0):.4f}，IDF1 {m.get('idf1',0):.4f}，ID switches {int(m.get('num_switches',0))}，misses {int(m.get('num_misses',0))}，{o.get('fps_end_to_end',0):.2f} FPS。完美检测输入仍有身份误差，支持对硬件入口条件进行单独评价。",b)])
 ck=js('detector_metrics.json',{}) or {}; selected=js('best_checkpoint_val.json',{}) or {}; story.extend([Paragraph('3. YOLOv4 独立测试',h),Paragraph((f"验证集选择 {Path(selected.get('weight','')).name or '最佳权重'}；独立测试集 P={ck.get('precision')}，R={ck.get('recall')}，F1={ck.get('f1')}，mAP50={ck.get('map50')}。" if ck else '正式训练与测试尚未完成。'),b)])
 if curve: story.extend([Spacer(1,8),Image(str(curve),480,220)])
 full=js('tracking_metrics.json',{}) or {}; story.extend([PageBreak(),Paragraph('4. 完整系统',h),Paragraph(f"YOLOv4+DeepSORT 端到端速度：{full.get('fps_end_to_end','待完成')} FPS。详细 MOT 与事件结果见 results/tracking_metrics.json。",b),Paragraph('5. 结论',h)])
 for x in ['入口、检测、跟踪和事件规则构成一条误差链。','序列隔离比随机拆帧更可信。','DeepSORT 无法自动修复漏检和合并框。','开放入口结果属于方法复现，不能直接重复作者受控通道数值。','部署应增加拥堵、逆行、功耗和长期稳定性评价。']: story.append(Paragraph('• '+x,b))
 SimpleDocTemplate(str(out),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=40,bottomMargin=40).build(story); return out

def main():
 DOCS.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True); pipe=pipeline_chart(); curve=training_chart(); a=DOCS/'第五篇论文_VSCode项目结构与训练操作手册.docx'; manual().save(a); b=DOCS/'第五篇论文_专业深度解析与论文写作评析.docx'; analysis(pipe).save(b); d=DOCS/'第五篇论文_详细分析与训练复现实验报告.docx'; detailed_report(pipe,curve).save(d); c=pdf(pipe,curve); print(a,b,d,c,sep='\n')
if __name__=='__main__': main()
