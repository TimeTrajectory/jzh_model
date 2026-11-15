#!/usr/bin/env python3
"""Generate two detailed Word manuals, combined experiment report and PDF."""
from pathlib import Path
from datetime import date
import csv,json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm,Inches,Pt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parent; RESULTS=ROOT/'results'; DOCS=ROOT/'docs'; REPORTS=ROOT/'reports'; ASSETS=ROOT/'assets'; FONT=Path('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
def js(n):
 p=RESULTS/n; return json.loads(p.read_text()) if p.exists() else {}
def doc(title,sub):
 d=Document(); sec=d.sections[0]; sec.top_margin=sec.bottom_margin=Cm(2); sec.left_margin=sec.right_margin=Cm(2.1)
 for n,s in [('Normal',10.5),('Title',22),('Heading 1',16),('Heading 2',13)]:
  st=d.styles[n]; st.font.name='Microsoft YaHei'; st._element.rPr.rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia','微软雅黑'); st.font.size=Pt(s)
 p=d.add_paragraph(style='Title'); p.alignment=1; p.add_run(title); p=d.add_paragraph(); p.alignment=1; p.add_run(sub); d.add_paragraph(f'生成日期：{date.today()}').alignment=1; d.add_page_break(); return d
def table(d,heads,rows):
 t=d.add_table(rows=1,cols=len(heads)); t.style='Table Grid'
 for i,x in enumerate(heads): t.rows[0].cells[i].text=str(x)
 for row in rows:
  c=t.add_row().cells
  for i,x in enumerate(row): c[i].text=str(x)
 return t
def bullets(d,items):
 for x in items: d.add_paragraph(x,style='List Bullet')
def code(d,s):
 r=d.add_paragraph().add_run(s); r.font.name='Consolas'; r.font.size=Pt(9)
def charts():
 ASSETS.mkdir(exist_ok=True); fp=FontProperties(fname=str(FONT)) if FONT.exists() else FontProperties(); curve=None; condp=None
 h=RESULTS/'training_history.csv'
 if h.exists():
  rows=list(csv.DictReader(h.open())); fig,ax=plt.subplots(figsize=(8,3.8)); ax.plot([int(x['iteration']) for x in rows],[float(x['avg_loss']) for x in rows]); ax.set(xlabel='Iteration',ylabel='Average loss'); ax.grid(alpha=.25); curve=ASSETS/'training_curve.png'; fig.savefig(curve,dpi=180,bbox_inches='tight'); plt.close(fig)
 c=js('condition_metrics.json').get('records',[])
 if c:
  hs=['10cm','20cm','30cm']; cs=['white','brown','dark_brown']; z=[[next(x['map50'] for x in c if x['height_proxy']==h and x['background']==cc) for cc in cs] for h in hs]; fig,ax=plt.subplots(figsize=(7,4)); im=ax.imshow(z,cmap='YlGn',vmin=0,vmax=1); ax.set_xticks(range(3),cs); ax.set_yticks(range(3),hs); [ax.text(j,i,f'{z[i][j]:.3f}',ha='center',va='center') for i in range(3) for j in range(3)]; fig.colorbar(im,ax=ax,label='mAP@0.50'); condp=ASSETS/'condition_heatmap.png'; fig.savefig(condp,dpi=180,bbox_inches='tight'); plt.close(fig)
 return curve,condp
def manual():
 d=doc('第六篇论文复现项目\nVS Code 结构与训练操作手册','YOLOv3-tiny · BEE22 · 条件实验 · 视频活动监测')
 d.add_heading('1. 项目目标与边界',1); d.add_paragraph('复现论文的检测、摄像头/视频入口、活动阈值和采集条件比较。原始无刺蜂数据未公开，BEE22 是替代数据；10/20/30 cm 是视场代理。')
 d.add_heading('2. 目录和文件职责',1); table(d,['文件','作用'],[['setup.sh','建立环境、下载模型资产并编译 Darknet'],['download_bee22.py','断点下载 BEE22，并校验大小、ZIP CRC 和 SHA256'],['prepare_data.py','安全解压、标签转换、序列隔离与 Darknet 清单'],['configure_yolov3_tiny.py','生成两检测头配置'],['train_yolov3.py','训练与续训'],['evaluate_detector.py','验证/测试检测指标'],['condition_experiment.py','3×3 条件敏感性实验'],['monitor_video.py','越线、事件率和活动状态'],['app.py','本地视频上传网页'],['generate_documents.py','重建 Word/PDF']])
 d.add_heading('3. VS Code 环境',1); code(d,'cd /jzk-model/jzh_model/bee/bee-paper6-stingless-monitoring-reproduction\nbash setup.sh'); d.add_paragraph('Ctrl+Shift+P → Python: Select Interpreter → .venv/bin/python。模型初始化权重由 setup.sh 下载；约 354.8 MB 的 BEE22 数据集不会提交到 GitHub，也不会在 setup.sh 中静默下载。')
 d.add_heading('4. 数据下载与审计',1); code(d,'.venv/bin/python download_bee22.py\n.venv/bin/python prepare_data.py\ncat data/dataset_summary.json'); d.add_paragraph('下载脚本分段重试并验证固定 SHA256。若已有 YOLO 格式数据，可运行 prepare_data.py --source /path/to/yolo。划分以完整视频序列为单位，防止相邻帧泄漏。'); table(d,['集合','帧','框'],[['train','1,360','16,050'],['val','240','3,093'],['test','762','12,205']])
 d.add_heading('5. 正式训练和断点续训',1); code(d,'.venv/bin/python train_yolov3.py\n.venv/bin/python train_yolov3.py --resume runs/train/backup/yolov3-tiny-bee_last.weights'); bullets(d,['batch 64，subdivisions 16。','416×416，2700 iterations。','classes 1，两个头的 filters 都是 18。','续训不使用 -clear。'])
 d.add_heading('6. 评价和条件实验',1); code(d,'.venv/bin/python evaluate_detector.py --split val\n.venv/bin/python evaluate_detector.py --split test\n.venv/bin/python condition_experiment.py --samples 20'); d.add_paragraph('条件实验改变视场裁切和框外背景，只能解释模型敏感性。')
 d.add_heading('7. 视频和网页',1); code(d,'.venv/bin/python monitor_video.py input.mp4 --output runs/videos/demo\n.venv/bin/python app.py'); bullets(d,['monitored.mp4：检测框、ID 和中线。','tracks.csv：逐帧轨迹。','events.json：越线事件。','summary.json：事件率、阈值和 ACTIVE/INACTIVE。'])
 d.add_heading('8. 修改参数',1); table(d,['参数','影响'],[['confidence','低值提高召回并增加误报'],['line position','应放在入口通行必经位置'],['track distance/age','控制快速运动和短时漏检'],['activity threshold','必须用长期人工数据校准'],['camera crop/background','只用于代理实验，不代表真实厘米距离']])
 d.add_heading('9. 常见错误',1); bullets(d,['找不到标签：图片和同名 txt 必须在同一目录。','显存不足：增大 subdivisions。','方向相反：确认相机安装后映射左右。','网页无结果：先确认 final.weights 存在。','精度不能复现论文：物种、数据、模型主干和指标定义均不同。'])
 return d
def analysis(combined=False,curve=None,condp=None):
 title='第六篇论文详细分析与训练复现实验报告' if combined else '第六篇论文专业深度解析与写作评析'; d=doc(title,'Smart Stingless Beehive Internet Based Monitoring System · 2022')
 d.add_heading('1. 通俗概述',1); d.add_paragraph('论文想解决一个直观问题：养蜂人不在现场时，怎样知道无刺蜂是否持续进出蜂箱。摄像头拍入口，检测器统计飞入飞出；一分钟内达到 20 只显示活跃，否则发出提醒。作者还发现相机距离和底板颜色会显著改变检测效果。')
 d.add_heading('2. 系统流程',1); bullets(d,['640×480 摄像头采集实时或录制视频。','MATLAB 中的 YOLOv3 检测无刺蜂。','系统绘制历史曲线并按每分钟 20 次分类活动状态。','低活动时启动蜂鸣器并发送电子邮件。'])
 d.add_heading('3. 模型与训练',1); d.add_paragraph('论文称 YOLOv3 以 SqueezeNet 为特征提取器，增加两个不同尺度检测头。SqueezeNet 较轻，第二个更高分辨率检测头用于较小目标。论文图示学习率约 0.001、训练到约 2700 次、AP 0.69，但没有给出训练集规模、划分和完整超参数。')
 d.add_heading('4. 原论文条件实验',1); table(d,['高度','白色','棕色','深棕'],[['10 cm','29.99%','47.5%','71.4%（7张）'],['20 cm','62.81%','27.5%','60%（10张）'],['30 cm','65.34%','75%','6.25%（10张）']]); d.add_paragraph('作者选择 30 cm 与棕色。10 cm 画面覆盖不足，更高距离又被认为降低清晰度。条件样本数不一致，且 accuracy 没有公式，所以不能做严格显著性推断。')
 d.add_heading('5. 论文创新点',1); bullets(d,['把无刺蜂入口检测、历史曲线、活动规则和远程提醒连成原型。','把相机距离和底板颜色作为系统参数，而不是只讨论神经网络。','同时支持实时和离线视频，贴近养蜂人的使用流程。'])
 d.add_heading('6. 局限',1); bullets(d,['数据、代码、权重和标签协议未公开。','样本量小且不平衡，没有置信区间。','accuracy、AP 和检测计数的公式不完整。','没有轨迹身份与人工进出事件，无法证明 fly-in/fly-out 正确率。','每分钟 20 次缺乏多蜂箱、季节和天气验证。','相机高度与目标像素大小、焦距、曝光同时变化，因素没有完全控制。'])
 d.add_heading('7. 本地复现设计',1); d.add_paragraph('本项目用公开 BEE22 连续入口序列替代未公开无刺蜂数据，训练 Darknet YOLOv3-tiny 2700 次。它保留两尺度检测，但不是 SqueezeNet 主干。条件实验固定同一批 20 帧，通过中央裁切模拟视场变化，通过框外重着色模拟底板颜色。')
 val=js('detector_val_metrics.json'); test=js('detector_test_metrics.json'); cond=js('condition_metrics.json').get('records',[])
 d.add_heading('8. 本地实验结果',1)
 if test:
  table(d,['数据','Precision','Recall','F1','mAP50'],[['val',val.get('precision'),val.get('recall'),val.get('f1'),val.get('map50')],['test',test.get('precision'),test.get('recall'),test.get('f1'),test.get('map50')]])
  if cond:
   best=max(cond,key=lambda x:x.get('map50') or -1); d.add_paragraph(f"代理条件最佳组合：{best.get('height_proxy')} + {best.get('background')}，mAP50={best.get('map50'):.4f}。该结果不能与论文 75% 直接比较。")
  else: d.add_paragraph('条件代理实验尚未运行。')
 else: d.add_paragraph('正式结果生成后自动填入。')
 if combined and curve: d.add_picture(str(curve),width=Inches(6.2))
 if combined and condp: d.add_picture(str(condp),width=Inches(5.8))
 d.add_heading('9. 结果应该怎样理解',1); bullets(d,['检测 mAP 衡量框，不等于飞入飞出事件正确率。','背景效果取决于训练分布、对比度、曝光和物种颜色。','近距离可能让蜂更大，也可能裁掉入口全景。','低活动可能来自天气或时段，不能自动解释为蜂群不健康。'])
 d.add_heading('10. 更好的创新方案',1); table(d,['方向','改进'],[['真实条件因子实验','固定焦距和曝光，距离×颜色平衡采样并重复多天'],['事件真值','标注轨迹 ID、真实 fly-in/fly-out 与时间'],['自适应阈值','按蜂箱、时间、天气学习基线和异常区间'],['小目标架构','增加 P2 检测头或入口 ROI 局部放大'],['跟踪计数','比较 ByteTrack/OC-SORT 与区域状态机'],['长期部署','边缘推理、太阳能、断网缓存、镜头污染检测'],['科学解释','把流量与温湿度、降雨、蜂蜜产量联合建模']])
 d.add_heading('11. 推荐论文写法',1); bullets(d,['明确研究问题与预注册指标。','公开按蜂箱和日期分组的数据清单。','报告每个条件样本数、均值、区间和失败案例。','分开报告检测、跟踪、事件、系统延迟和告警。','讨论对蜂行为的干扰及部署维护成本。'])
 d.add_heading('12. 总结',1); d.add_paragraph('论文最有价值的地方是提醒研究者：采集条件是视觉系统的一部分。其原型展示了远程监测可行性，但证据不足以证明 75% 可泛化，也不足以把 20 次/分钟当作健康标准。本次复现将这些想法转为可运行、可审计的检测、条件敏感性和视频活动流程。')
 return d
def pdf(curve,condp):
 REPORTS.mkdir(exist_ok=True); out=REPORTS/'第六篇论文复现结果报告.pdf'; font='Helvetica'
 if FONT.exists(): pdfmetrics.registerFont(TTFont('CN',str(FONT))); font='CN'
 st=getSampleStyleSheet(); h=ParagraphStyle('h',parent=st['Heading2'],fontName=font,textColor=colors.HexColor('#234F32')); b=ParagraphStyle('b',parent=st['BodyText'],fontName=font,leading=15); story=[Paragraph('第六篇论文复现结果报告',ParagraphStyle('t',parent=st['Title'],fontName=font)),Spacer(1,12),Paragraph('1. 复现边界',h),Paragraph('原论文无刺蜂数据与 MATLAB 工程未公开。本项目使用 BEE22 和 Darknet YOLOv3-tiny复现检测、活动监测及采集条件敏感性实验。',b)]
 test=js('detector_test_metrics.json'); cond=js('condition_metrics.json').get('records',[])
 if test:
  t=Table([['P','R','F1','mAP50'],[test['precision'],test['recall'],test['f1'],test['map50']]]); t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),font),('GRID',(0,0),(-1,-1),.5,colors.grey)])); story += [Paragraph('2. 独立测试',h),t]
 if curve: story += [Spacer(1,8),Image(str(curve),480,220)]
 if cond:
  best=max(cond,key=lambda x:x['map50']); story += [PageBreak(),Paragraph('3. 条件代理实验',h),Paragraph(f"最佳组合为 {best['height_proxy']} + {best['background']}，mAP50={best['map50']:.4f}。高度为视场代理，不能解释为真实厘米距离。",b)]
  if condp: story += [Image(str(condp),430,250)]
 story += [Paragraph('4. 结论',h),Paragraph('论文强调相机位置和背景对检测的影响是合理的。严格验证需要平衡样本、多蜂箱重复、标准检测指标和真实进出事件。固定 20 次/分钟只能作为原型规则。',b)]
 SimpleDocTemplate(str(out),pagesize=A4).build(story); return out
def main():
 DOCS.mkdir(exist_ok=True); curve,condp=charts(); a=DOCS/'第六篇论文_VSCode项目结构与训练操作手册.docx'; manual().save(a); b=DOCS/'第六篇论文_专业深度解析与论文写作评析.docx'; analysis().save(b); c=DOCS/'第六篇论文_详细分析与训练复现实验报告.docx'; analysis(True,curve,condp).save(c); p=pdf(curve,condp); print(a,b,c,p,sep='\n')
if __name__=='__main__': main()

