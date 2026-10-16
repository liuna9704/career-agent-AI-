from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build() -> Path:
    root = Path(__file__).resolve().parents[2]
    output = root / "demo_data" / "example_resume.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont("DemoCN", "C:/Windows/Fonts/simhei.ttf"))
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleCN", parent=styles["Title"], fontName="DemoCN", fontSize=23, leading=30, textColor=colors.HexColor("#17233D"), alignment=TA_CENTER)
    heading = ParagraphStyle("HeadingCN", parent=styles["Heading2"], fontName="DemoCN", fontSize=13, leading=18, textColor=colors.HexColor("#315FF6"), spaceBefore=8, spaceAfter=6)
    body = ParagraphStyle("BodyCN", parent=styles["BodyText"], fontName="DemoCN", fontSize=10.5, leading=18, textColor=colors.HexColor("#3F4B61"))
    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=22*mm, rightMargin=22*mm, topMargin=18*mm, bottomMargin=18*mm, title="智面未来演示简历")
    story = [Paragraph("张三", title), Paragraph("Java开发工程师 | 3年后端开发经验", ParagraphStyle("Sub", parent=body, alignment=TA_CENTER, textColor=colors.HexColor("#68758B"))), Spacer(1, 8*mm)]
    info = Table([["教育背景", "本科 - 计算机科学与技术"], ["核心技能", "Java / Spring Boot / MySQL / Redis / Docker"], ["求职方向", "Java开发工程师"]], colWidths=[30*mm, 115*mm])
    info.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"DemoCN"),("FONTSIZE",(0,0),(-1,-1),10),("TEXTCOLOR",(0,0),(0,-1),colors.HexColor("#315FF6")),("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F4F7FF")),("GRID",(0,0),(-1,-1),.5,colors.HexColor("#DDE5F6")),("PADDING",(0,0),(-1,-1),8)]))
    story += [info, Spacer(1, 6*mm), Paragraph("项目经历", heading), Paragraph("<b>智能招聘系统</b> | Spring Boot、MySQL、Redis、Docker", body), Paragraph("负责后端接口设计、数据库优化和缓存架构设计。通过覆盖索引、热点缓存与异步任务优化核心招聘流程，接口P95延迟降低35%，支持日均20万次请求。", body), Spacer(1, 4*mm), Paragraph("工作经历", heading), Paragraph("负责招聘业务服务开发、接口规范建设、线上问题排查和Docker部署；参与代码评审、单元测试与监控告警建设。", body), Spacer(1, 4*mm), Paragraph("个人优势", heading), Paragraph("具备完整后端项目交付经验；能够结合业务约束进行技术选型；重视性能指标、稳定性和工程质量。", body), Spacer(1, 4*mm), Paragraph("待验证信息", heading), Paragraph("Redis缓存一致性方案、分布式锁正确性、高并发故障降级和复杂分布式系统实践。", body)]
    doc.build(story)
    print(output)
    return output


if __name__ == "__main__":
    build()
