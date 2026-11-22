# -*- coding: utf-8 -*-
"""生成公司内部制度文件：差旅与费用报销管理办法"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_DIR = r"E:\Desktop\oncall-agent\output"
OUT = os.path.join(OUT_DIR, "星澜科技-差旅与费用报销管理办法-V2.1.docx")
os.makedirs(OUT_DIR, exist_ok=True)

CN_BODY = "宋体"
CN_HEAD = "黑体"
EN_FONT = "Times New Roman"


def set_font(run, cn=CN_BODY, en=EN_FONT, size=10.5, bold=False, color=None):
    run.font.name = en
    run.font.size = Pt(size)
    run.bold = bold
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), en)
    rfonts.set(qn("w:hAnsi"), en)
    rfonts.set(qn("w:eastAsia"), cn)
    if color:
        run.font.color.rgb = RGBColor(*color)


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def doc_heading(doc, text, level=1):
    # 关键：使用 Word 真正的「标题」样式，MaxKB 靠 style.name 识别层级
    style = "Heading 1" if level == 1 else "Heading 2"
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    p.paragraph_format.space_after = Pt(8 if level == 1 else 6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    if level == 1:
        set_font(run, cn=CN_HEAD, size=16, bold=True, color=(0x1F, 0x3B, 0x63))
    else:
        set_font(run, cn=CN_HEAD, size=13, bold=True, color=(0x1F, 0x3B, 0x63))
    return p


def body(doc, text, indent=True, bold_prefix=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(4)
    if indent:
        pf.first_line_indent = Pt(21)
    if bold_prefix:
        r1 = p.add_run(bold_prefix)
        set_font(r1, bold=True)
    run = p.add_run(text)
    set_font(run)
    return p


def bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 1.4
    pf.left_indent = Pt(21)
    pf.space_after = Pt(2)
    if bold_prefix:
        r1 = p.add_run(bold_prefix)
        set_font(r1, bold=True)
    run = p.add_run(text)
    set_font(run)
    return p


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def no_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))


def make_table(doc, header, rows, widths=None, font_size=9.5):
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    repeat_header(table.rows[0])
    no_split(table.rows[0])
    hdr = table.rows[0].cells
    for i, h in enumerate(header):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        set_font(run, cn=CN_HEAD, size=font_size, bold=True)
        shade(hdr[i], "DCE6F1")
    for row in rows:
        cells = table.add_row().cells
        no_split(table.rows[-1])
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == len(row) - 1 and len(str(val)) > 10 else WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(str(val))
            set_font(run, size=font_size)
    if widths:
        for r in table.rows:
            for i, w in enumerate(widths):
                r.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


doc = Document()

# 页面设置 A4
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.left_margin = Cm(2.8)
sec.right_margin = Cm(2.6)
sec.top_margin = Cm(2.4)
sec.bottom_margin = Cm(2.2)

# 正文样式
normal = doc.styles["Normal"]
normal.font.name = EN_FONT
normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), CN_BODY)

# 页脚
footer_p = sec.footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
fr = footer_p.add_run("星澜信息技术有限公司  |  文件编号 XLKJ-XZ-2026-007  |  内部公开")
set_font(fr, size=8, color=(0x80, 0x80, 0x80))

# ---------- 封面区 ----------
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_before = Pt(30)
tr = title.add_run("差旅与费用报销管理办法")
set_font(tr, cn=CN_HEAD, size=24, bold=True, color=(0x1F, 0x3B, 0x63))

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sub.add_run("Travel and Expense Reimbursement Policy")
set_font(sr, size=11, color=(0x60, 0x60, 0x60))

doc.add_paragraph()

make_table(
    doc,
    ["项目", "内容", "项目", "内容"],
    [
        ["文件编号", "XLKJ-XZ-2026-007", "版本号", "V2.1"],
        ["归口部门", "行政人事部", "会签部门", "财务部、法务合规部"],
        ["密级", "内部公开", "生效日期", "2026年12月1日"],
        ["适用范围", "全体在职员工", "废止文件", "XLKJ-XZ-2025-004（V1.8）"],
    ],
    widths=[2.6, 5.4, 2.6, 5.4],
    font_size=9,
)

doc_heading(doc, "修订记录", 2)
make_table(
    doc,
    ["版本", "修订日期", "修订部门", "主要修订内容"],
    [
        ["V1.5", "2024-03-01", "行政人事部", "首次发布，明确境内差旅基本标准。"],
        ["V1.8", "2025-06-15", "行政人事部", "新增境外差旅章节，调整住宿标准上限。"],
        ["V2.0", "2026-03-10", "财务部", "报销流程迁移至 OA 系统，取消纸质审批单。"],
        ["V2.1", "2026-11-20", "行政人事部", "细化城市分级，新增长期驻场与 AI 工具使用条款。"],
    ],
    widths=[2.0, 3.0, 3.2, 7.8],
    font_size=9,
)

doc.add_page_break()

# ---------- 第一章 ----------
doc_heading(doc, "第一章  总则", 1)

doc_heading(doc, "第一条  目的", 2)
body(doc, "为规范公司差旅活动管理，控制差旅成本，明确费用报销标准与审批权限，保障员工出差期间的正常工作条件，依据《中华人民共和国会计法》《企业会计准则第9号——职工薪酬》及公司财务管理相关规定，制定本办法。")

doc_heading(doc, "第二条  适用范围", 2)
body(doc, "本办法适用于星澜信息技术有限公司及各分支机构全体在职人员，包括：")
bullet(doc, "与公司签订劳动合同的正式员工、试用期员工；", "（一）")
bullet(doc, "经人力资源部备案的实习生、劳务派遣人员；", "（二）")
bullet(doc, "经总经理批准、由公司承担差旅费用的外部顾问及合作方人员。", "（三）")

doc_heading(doc, "第三条  管理原则", 2)
bullet(doc, "预算控制原则。差旅支出纳入部门年度费用预算，超预算部分须追加审批。", "（一）")
bullet(doc, "真实必要原则。出差须与业务直接相关，不得安排无实质业务内容的差旅。", "（二）")
bullet(doc, "事前审批原则。除本办法第八条规定的紧急情形外，未经审批的差旅费用不予报销。", "（三）")
bullet(doc, "逐级审核原则。费用报销实行经办人、部门负责人、财务部三级审核。", "（四）")

doc_heading(doc, "第四条  术语定义", 2)
body(doc, "本办法所称“出差”，指员工因公务离开常驻工作城市且连续时间超过 4 小时、需要在外住宿或使用交通工具的行为。常驻工作城市以劳动合同约定的工作地点为准。")
body(doc, "“差旅费用”包括城市间交通费、住宿费、市内交通费、伙食补贴及其他经批准的合理支出；“招待费”“会议费”不属于差旅费用，按公司相关专项制度执行。")

# ---------- 第二章 ----------
doc_heading(doc, "第二章  职责分工", 1)
body(doc, "差旅管理实行归口管理与分级负责相结合的方式，各方职责如下：")
make_table(
    doc,
    ["责任主体", "主要职责"],
    [
        ["出差员工", "如实填写申请、按标准执行、妥善保管票据、按时提交报销、对费用真实性负责。"],
        ["直属上级", "审核出差必要性、行程合理性，对下属差旅行为负管理责任。"],
        ["部门负责人", "在授权额度内审批，控制本部门差旅预算，审核超标准申请。"],
        ["行政人事部", "制定与解释差旅标准，管理协议酒店与商旅平台，统计差旅数据。"],
        ["财务部", "审核票据合规性与标准符合性，办理付款，组织抽查与专项审计。"],
        ["分管副总", "审批超授权额度及跨部门、境外差旅事项。"],
        ["总经理", "审批境外差旅、超预算 30% 以上的差旅及重大特殊事项。"],
    ],
    widths=[3.2, 12.8],
    font_size=9.5,
)

# ---------- 第三章 ----------
doc_heading(doc, "第三章  出差审批", 1)

doc_heading(doc, "第五条  申请流程", 2)
body(doc, "员工应在 OA 系统「差旅管理—出差申请」模块填写《出差申请单》，注明出差事由、目的地、起止日期、同行人员、预估费用及费用承担主体，提交后按下列顺序流转：")
bullet(doc, "直属上级审核（必要时补充行程说明）；", "第一步：")
bullet(doc, "部门负责人审批；", "第二步：")
bullet(doc, "超出部门授权额度的，转分管副总或总经理审批；", "第三步：")
bullet(doc, "审批通过后系统自动抄送行政人事部备案。", "第四步：")

doc_heading(doc, "第六条  审批时限与授权额度", 2)
body(doc, "各级审批人应在收到申请后 24 小时内完成审批；逾期未处理且员工已出差的，视为默认同意，但事后仍需补办审批手续。审批授权额度如下：")
make_table(
    doc,
    ["出差类型", "预估费用", "审批权限"],
    [
        ["境内，≤ 3 天", "≤ 5,000 元", "部门负责人"],
        ["境内，> 3 天", "≤ 20,000 元", "分管副总"],
        ["境内任意", "> 20,000 元", "总经理"],
        ["境外任意", "任意金额", "总经理"],
        ["长期驻场（> 30 天）", "任意金额", "总经理 + 财务负责人会签"],
    ],
    widths=[5.0, 4.0, 7.0],
    font_size=9.5,
)

doc_heading(doc, "第七条  变更与取消", 2)
body(doc, "出差行程发生变更（延期、改道、提前返回）的，员工应在变更发生后 1 个工作日内于 OA 提交变更申请。因航班取消、疫情管控等不可抗力导致的变更，可先执行后补录，但须保留航空公司或相关机构出具的证明。")

doc_heading(doc, "第八条  紧急出差", 2)
body(doc, "因客户故障、生产事故等紧急情况需即时出差的，员工可先电话或即时通讯工具取得直属上级口头同意后出行，并在返程后 2 个工作日内补办审批手续。口头同意的记录（聊天截图）应作为附件上传。")

# ---------- 第四章 ----------
doc_heading(doc, "第四章  差旅费用标准", 1)

doc_heading(doc, "第九条  城市分级", 2)
body(doc, "差旅标准按目的地城市分级执行，分级结果每年 1 月由行政人事部更新发布：")
make_table(
    doc,
    ["城市等级", "城市范围"],
    [
        ["一类城市", "北京、上海、广州、深圳"],
        ["二类城市", "杭州、成都、南京、武汉、西安、苏州、天津、重庆、长沙、郑州、青岛、宁波、厦门、合肥、济南、福州、东莞、佛山"],
        ["三类城市", "除上述城市以外的其他国内城市"],
    ],
    widths=[3.0, 13.0],
    font_size=9.5,
)

doc_heading(doc, "第十条  住宿标准", 2)
body(doc, "住宿费按实际住宿天数凭票报销，标准上限（元/晚，含税）如下。超标部分由个人承担，特殊情况须在报销时附书面说明并经分管副总批准。")
make_table(
    doc,
    ["职级", "一类城市", "二类城市", "三类城市"],
    [
        ["P1—P3（初级）", "600", "450", "350"],
        ["P4—P5（中级/高级）", "700", "550", "450"],
        ["M1—M2（经理/高级经理）", "900", "700", "600"],
        ["M3 及以上（总监及以上）", "1200", "1000", "800"],
    ],
    widths=[5.5, 3.5, 3.5, 3.5],
    font_size=9.5,
)
body(doc, "两名及以上同性别同职级员工同行出差至同一地点的，原则上应合住标准间；因公司安排合住而节省的住宿费用，不另行发放补贴。")

doc_heading(doc, "第十一条  城市间交通标准", 2)
body(doc, "城市间交通工具的选择应以经济、安全、高效为原则，原则上优先选择高铁。具体标准如下：")
make_table(
    doc,
    ["职级", "飞机", "高铁/动车", "其他"],
    [
        ["P1—P3", "经济舱", "二等座", "长途汽车、普通列车硬卧"],
        ["P4—P5", "经济舱", "二等座（单程 ≥ 4 小时可一等座）", "同上"],
        ["M1—M2", "经济舱", "一等座", "同上"],
        ["M3 及以上", "经济舱（单程 ≥ 4 小时可公务舱）", "一等座/商务座", "同上"],
    ],
    widths=[3.5, 4.5, 4.5, 3.5],
    font_size=9.5,
)
body(doc, "机票应通过公司商旅平台预订，原则上选择折扣票价；因紧急公务需购买全价票的，须在申请中说明原因。退票、改签产生的费用，因公原因造成的予以报销，因个人原因造成的由个人承担。")

doc_heading(doc, "第十二条  市内交通标准", 2)
body(doc, "出差期间市内交通费据实报销，包括机场/车站往返、客户拜访、会议地点往返等，每日限额为：一类城市 200 元、二类城市 150 元、三类城市 120 元。")
body(doc, "鼓励使用公共交通。单次超过 100 元的打车费用，应在报销单中注明起讫地点与事由。租车自驾须事前经部门负责人批准，燃油费、过路费按实际报销，违章罚款不予报销。")

doc_heading(doc, "第十三条  伙食补贴", 2)
body(doc, "伙食补贴按出差自然日计算，实行包干制，无需提供发票，标准如下：")
make_table(
    doc,
    ["城市等级", "补贴标准（元/天）", "说明"],
    [
        ["一类城市", "100", "出发当日与返程当日按全天计"],
        ["二类城市", "80", "当日往返（不留宿）按 50% 计发"],
        ["三类城市", "60", "会议/培训统一安排用餐的，不予计发"],
    ],
    widths=[3.5, 5.0, 7.5],
    font_size=9.5,
)

doc_heading(doc, "第十四条  境外差旅标准", 2)
body(doc, "境外差旅须经总经理事前批准，并按国家（地区）分类执行补贴标准，住宿费凭票报销，上限按财务部每年发布的《境外差旅费用标准表》执行：")
make_table(
    doc,
    ["国家/地区分类", "伙食及杂费补贴（美元/天）", "示例"],
    [
        ["一类（高消费）", "80", "美国、英国、日本、新加坡、瑞士"],
        ["二类（中等）", "60", "德国、法国、澳大利亚、韩国、阿联酋"],
        ["三类（其他）", "40", "东南亚其他国家、南美、非洲"],
    ],
    widths=[4.0, 6.0, 6.0],
    font_size=9.5,
)
body(doc, "境外差旅期间的汇率按报销当月 1 日中国银行中间价折算。公司为境外出差人员统一购买境外旅行意外险，个人自行增加的保险费用自理。")

# ---------- 第五章 ----------
doc_heading(doc, "第五章  费用报销", 1)

doc_heading(doc, "第十五条  报销时限", 2)
body(doc, "员工应在出差结束后 15 个工作日内完成报销单提交；跨年度费用须于当年 12 月 25 日前提交，逾期不再受理并计入次年预算。")
body(doc, "因特殊原因（如票据未到、项目结算延迟）无法按期提交的，须在期满前提交延期说明，经财务负责人批准后可延长 15 个工作日，且仅限一次。")

doc_heading(doc, "第十六条  单据要求", 2)
body(doc, "报销须提供以下原始凭证，缺一不予受理：")
bullet(doc, "增值税发票（抬头须为“星澜信息技术有限公司”，税号信息由财务部统一提供）；", "（一）")
bullet(doc, "交通票据：机票行程单、火车票（或电子客票报销凭证）、出租车发票；", "（二）")
bullet(doc, "住宿票据：酒店发票及水单（须体现入住人姓名与天数）；", "（三）")
bullet(doc, "经批准的《出差申请单》编号及审批记录；", "（四）")
bullet(doc, "超标、变更、紧急出差等特殊情形的书面说明与批准记录。", "（五）")
body(doc, "电子发票须上传 PDF 原件，同一张发票不得重复报销，财务系统将自动查重。")

doc_heading(doc, "第十七条  审批与付款", 2)
body(doc, "报销单流转顺序为：员工提交 → 直属上级审核 → 部门负责人审核 → 财务部复核 → 出纳付款。财务部应在收到完整单据后 5 个工作日内完成审核，审批通过后 5 个工作日内将款项支付至员工工资卡账户。")
body(doc, "对审核不通过的报销单，财务部应一次性告知需补正的全部事项；员工补正后重新提交，审批时限重新计算。")

doc_heading(doc, "第十八条  借款与冲抵", 2)
body(doc, "员工出差可申请差旅借款，单笔不超过预估费用的 80%。借款须在出差结束后 10 个工作日内冲抵；未冲抵的，财务部可从当月工资中暂扣，待报销完成后返还。")

# ---------- 第六章 ----------
doc_heading(doc, "第六章  特殊情形", 1)

doc_heading(doc, "第十九条  长期驻场", 2)
body(doc, "连续在同一城市驻场超过 30 天的，自第 31 天起不再执行住宿标准，改为发放住房补贴：一类城市 3,000 元/月、二类城市 2,500 元/月、三类城市 2,000 元/月，不再发放伙食补贴。")
body(doc, "长期驻场人员每满 30 天可享受 1 次探亲往返，交通标准按第十一条执行，探亲期间不计入出差天数。")

doc_heading(doc, "第二十条  会议与培训", 2)
body(doc, "由公司统一组织并承担食宿的会议、培训，不发放伙食补贴与住宿费；由主办方承担部分费用的，仅报销公司未承担部分。参加外部付费培训的，须提前取得培训预算批准。")

doc_heading(doc, "第二十一条  不可抗力", 2)
body(doc, "因自然灾害、公共卫生事件、交通管制等不可抗力导致行程滞留的，滞留期间住宿费按标准上限的 120% 报销，伙食补贴照常计发，员工应在返程后 3 个工作日内提交情况说明。")

doc_heading(doc, "第二十二条  AI 辅助工具的差旅场景应用", 2)
body(doc, "员工在差旅申请、行程规划、票据整理环节可使用公司批准的 AI 工具辅助，但不得将客户名称、合同金额、个人信息等敏感数据输入未经安全评估的第三方模型。使用 AI 生成的行程方案作为报销附件的，须经人工核对。")

# ---------- 第七章 ----------
doc_heading(doc, "第七章  违规处理", 1)
body(doc, "对违反本办法的行为，视情节轻重按下列标准处理；涉嫌违法的，移交司法机关：")
make_table(
    doc,
    ["违规情形", "处理措施"],
    [
        ["虚开、买卖、伪造发票", "全额追回款项，给予书面警告，扣减当年绩效 20%，一年内不得晋升"],
        ["重复报销、拆分报销规避审批", "追回款项，全公司通报批评，取消当年评优资格"],
        ["未经审批出差且事后未补办", "费用不予报销，超标部分由个人承担"],
        ["超期 30 天以上未提交报销", "原则上不予受理，特殊情况须总经理批准"],
        ["将个人消费混入差旅报销", "追回款项，视金额给予警告至解除劳动合同"],
        ["审批人未尽审核义务", "纳入管理者年度考核，累计 3 次以上取消当年评优资格"],
    ],
    widths=[6.5, 9.5],
    font_size=9.5,
)

# ---------- 第八章 ----------
doc_heading(doc, "第八章  附则", 1)
body(doc, "第二十三条  本办法由行政人事部会同财务部负责解释；与国家法律法规冲突的，以法律法规为准。")
body(doc, "第二十四条  本办法自 2026 年 12 月 1 日起施行，原《差旅与费用报销管理办法（V1.8）》同时废止。")
body(doc, "第二十五条  各部门可在本办法框架内制定实施细则，报行政人事部备案后执行，不得突破本办法规定的标准上限。")

doc.add_page_break()

# ---------- 附录 ----------
doc_heading(doc, "附录 A  常见问题解答", 1)
faqs = [
    ("出差当天往返，能拿到多少补贴？", "当日往返不留宿的，伙食补贴按标准的 50% 计发；住宿费不予报销。市内交通费仍按目的地城市分级限额据实报销。"),
    ("机票买贵了还能报销吗？", "可以报销，但须证明是紧急公务并附部门负责人说明。若因个人原因选择高价航班，超出同航线经济舱折扣票价的部分由个人承担。"),
    ("住宿超标了怎么办？", "超标部分由个人承担。如因会议指定酒店、当地房源紧张等客观原因超标，须在报销时附书面说明，经分管副总批准后方可全额报销。"),
    ("出差期间顺路回家，费用怎么算？", "因私绕行的交通费与住宿费由个人承担，绕行期间不计发出差补贴；因私绕行不得影响正常公务行程。"),
    ("发票抬头开错了怎么办？", "须联系商家作废重开。电子发票可通过原开票平台申请红冲后重新开具，不得使用涂改票据报销。"),
    ("长期驻场满 30 天后标准怎么变？", "自第 31 天起停发住宿费与伙食补贴，改为按月发放住房补贴：一类城市 3,000 元、二类 2,500 元、三类 2,000 元，并每满 30 天享受 1 次探亲往返。"),
    ("报销多久能到账？", "财务部在收到完整单据后 5 个工作日内完成审核，审批通过后 5 个工作日内付款，整体一般不超过 10 个工作日。"),
    ("境外出差的汇率按什么算？", "按报销当月 1 日中国银行外汇中间价折算，由财务部在系统中统一配置，员工无需自行换算。"),
    ("出差期间生病了，医疗费能报吗？", "普通门诊费用由医保承担；境外出差由公司统一购买的旅行意外险覆盖紧急医疗，个人额外增加的保险与治疗费用自理。"),
    ("忘记提交报销单超过 30 天了怎么办？", "原则上不再受理。确有特殊原因的，可提交书面申请说明原因，经部门负责人与财务负责人会签、总经理批准后，可例外受理一次。"),
]
for i, (q, a) in enumerate(faqs, 1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(f"Q{i}. {q}")
    set_font(r, cn=CN_HEAD, size=10.5, bold=True)
    p2 = doc.add_paragraph()
    p2.paragraph_format.line_spacing = 1.4
    p2.paragraph_format.left_indent = Pt(14)
    p2.paragraph_format.space_after = Pt(4)
    r2 = p2.add_run(f"A：{a}")
    set_font(r2, size=10.5)

doc_heading(doc, "附录 B  报销单据清单", 1)
make_table(
    doc,
    ["序号", "单据名称", "是否必需", "备注"],
    [
        ["1", "出差申请单（OA 编号）", "必需", "紧急出差可后补"],
        ["2", "交通票据/行程单", "必需", "机票须附行程单"],
        ["3", "住宿发票及水单", "必需", "须体现入住人"],
        ["4", "增值税发票", "必需", "抬头税号须准确"],
        ["5", "超标说明及批准记录", "视情况", "超标或变更时提供"],
        ["6", "境外差旅批准文件", "境外必需", "须总经理签批"],
        ["7", "延期报销申请", "视情况", "超过 15 个工作日时提供"],
    ],
    widths=[1.8, 6.2, 3.0, 5.0],
    font_size=9.5,
)

# 文末发布信息
doc.add_paragraph()
end = doc.add_paragraph()
end.alignment = WD_ALIGN_PARAGRAPH.RIGHT
er = end.add_run("星澜信息技术有限公司  行政人事部\n2026 年 11 月 20 日")
set_font(er, size=10)

doc.save(OUT)
print("saved:", OUT)
