# -*- coding: utf-8 -*-
"""Build the AI.zip cracking-attempts summary docx."""
import os
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = r"D:\crack-log\AI.zip破解尝试汇总.docx"


def _gpu_rows():
    """Read measured GPU results (written by night_5090.py)."""
    import json as _json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gpu_results.json")
    try:
        with open(path, encoding="utf-8") as f:
            rows = _json.load(f).get("rows", [])
    except Exception:
        return []
    rows = [r for r in rows if r.get("speed_ps", 0) > 0 and r.get("price", 0) > 0]
    return sorted(rows, key=lambda r: -r["speed_ps"])


def _wan(v):
    return "{:,.0f}".format(v / 1e4)


def _h62(r):
    return 62 ** 7 / r["speed_ps"] / 3600.0


def _cost62(r):
    return "{:,.0f}".format(_h62(r) * r["price"])

P_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl",
           "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens",
           "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN",
           "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing",
           "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment",
           "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"]
TC_ORDER = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap",
            "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark"]


def insert_ordered(parent, el, order):
    tag = el.tag.split("}")[-1]
    idx = order.index(tag)
    for child in list(parent):
        ctag = child.tag.split("}")[-1]
        if ctag in order and order.index(ctag) > idx:
            child.addprevious(el)
            return el
    parent.append(el)
    return el
NAVY = RGBColor(0x1F, 0x3A, 0x5F)
GREY = RGBColor(0x59, 0x59, 0x59)
MONO = "Consolas"
EA = "微软雅黑"
SONG = "宋体"


def set_run(run, size=10.5, bold=False, ea=SONG, ascii_f="Times New Roman", color=None, italic=False):
    run.font.name = ascii_f
    run._element.rPr.rFonts.set(qn("w:eastAsia"), ea)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    return run


def P(doc, text="", size=10.5, bold=False, color=None, align=None, space_after=6, indent=None, ea=SONG):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.45
    if indent is not None:
        pf.first_line_indent = Cm(indent)
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "right":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    elif align == "justify":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if text:
        add_rich(p, text, size, bold, color, ea)
    return p


def add_rich(p, text, size=10.5, bold=False, color=None, ea=SONG):
    import re
    for part in re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", text):
        if not part:
            continue
        if part.startswith("`") and part.endswith("`") and len(part) > 2:
            r = p.add_run(part[1:-1])
            set_run(r, size - 0.5, False, MONO, MONO, RGBColor(0x8B, 0x1A, 0x1A))
        elif part.startswith("**") and part.endswith("**") and len(part) > 4:
            r = p.add_run(part[2:-2])
            set_run(r, size, True, ea, "Times New Roman", color)
        else:
            r = p.add_run(part)
            set_run(r, size, bold, ea, "Times New Roman", color)


def H1(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(16)
    pf.space_after = Pt(8)
    if text == "AI.zip 破解尝试汇总":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    set_run(r, 15, True, EA, EA, NAVY)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "1F3A5F")
    pBdr.append(bottom)
    insert_ordered(pPr, pBdr, P_ORDER)
    return p


def H2(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(10)
    pf.space_after = Pt(4)
    r = p.add_run(text)
    set_run(r, 12, True, EA, EA, NAVY)
    return p


def BUL(doc, text, size=10.5):
    p = doc.add_paragraph(style="List Bullet")
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.35
    add_rich(p, text, size)
    return p


def CODE(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(6)
    pf.left_indent = Cm(0.4)
    pf.line_spacing = 1.05
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "F4F6F8")
    insert_ordered(pPr, shd, P_ORDER)
    pBdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "18")
    left.set(qn("w:space"), "6")
    left.set(qn("w:color"), "1F3A5F")
    pBdr.append(left)
    insert_ordered(pPr, pBdr, P_ORDER)
    for i, line in enumerate(text.split("\n")):
        r = p.add_run(line)
        set_run(r, 8.8, False, MONO, MONO, RGBColor(0x22, 0x22, 0x22))
        if i < len(text.split("\n")) - 1:
            r.add_break()
    return p


def CAP(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(6)
    pf.space_after = Pt(3)
    add_rich(p, text, 9, True, GREY, EA)
    return p


def T(doc, headers, rows, widths, size=8.6, center_cols=(), header_fill="1F3A5F"):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.autofit = False
    hdr = table.rows[0]
    hdr.cells[0].paragraphs[0].paragraph_format.space_after = Pt(1)
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.width = Cm(widths[i])
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        set_run(r, size, True, EA, EA, RGBColor(0xFF, 0xFF, 0xFF))
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), header_fill)
        insert_ordered(tcPr, shd, TC_ORDER)
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].width = Cm(widths[i])
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.1
            if i in center_cols:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_rich(p, str(val), size)
    for i, w in enumerate(widths):
        table.columns[i].width = Cm(w)
    return table


def footer_page(doc):
    sec = doc.sections[0]
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("第 ")
    set_run(r, 8.5, False, SONG, SONG, GREY)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    rr = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "1"
    rr.append(t)
    fld.append(rr)
    p._p.append(fld)
    r2 = p.add_run(" 页 / 共 ")
    set_run(r2, 8.5, False, SONG, SONG, GREY)
    fld2 = OxmlElement("w:fldSimple")
    fld2.set(qn("w:instr"), "NUMPAGES")
    rr2 = OxmlElement("w:r")
    t2 = OxmlElement("w:t")
    t2.text = "1"
    rr2.append(t2)
    fld2.append(rr2)
    p._p.append(fld2)
    r3 = p.add_run(" 页")
    set_run(r3, 8.5, False, SONG, SONG, GREY)


def setup():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.4)
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.2)
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)
    footer_page(doc)
    return doc


def cover(doc):
    for _ in range(4):
        P(doc, "", space_after=0)
    P(doc, "AI.zip 密码破解尝试汇总", 24, True, NAVY, "center", 6, ea=EA)
    P(doc, "覆盖空间、耗时、费用与后续方案", 12, False, GREY, "center", 18, ea=EA)
    P(doc, "2026-11-17 ～ 2026-11-18", 10.5, False, GREY, "center", 4)
    P(doc, "AutoDL RTX 4090D / RTX 4090 + 本地 Ryzen 7 5700U", 9.5, False, GREY, "center", 30)
    P(doc, "结论：已穷举 3–6 位全字符集与 7 位两套子空间，共约 2,531 亿候选，未命中。", 10, True, NAVY, "center", 4)
    P(doc, "累计 GPU 约 11 小时，花费约 ¥21.5。", 10, True, NAVY, "center", 4)
    doc.add_page_break()


def ch1(doc):
    H1(doc, "1　概述")
    P(doc, "本文件汇总 2026-11-17 至 2026-11-18 对 AI.zip 所做的一切密码尝试：用过的工具、跑过的掩码与字典、"
           "每个空间的候选数量、耗时与费用，以及最终结论和后续可选方案。目的是留档，避免重复劳动，"
           "并在下次想继续时能直接照着命令复现。", indent=0.74)
    P(doc, "压缩包本身没有被动过：所有尝试都是离线计算，不向任何服务上传文件；hash 由本机 zip2john 提取。", indent=0.74)
    H2(doc, "1.1　一句话结论")
    BUL(doc, "3、4、5、6 位（62 字符集：大小写字母 + 数字）已 **100% 穷举**，未命中。")
    BUL(doc, "7 位只覆盖了“纯大写 + 数字”和“纯小写 + 数字”两套（各 36⁷），覆盖 4.45%，未命中。")
    BUL(doc, "8 位只覆盖了 4 大写 + 4 数字的 4 种排列、8 位纯数字、手机号等零散切片，覆盖不到 0.01%，未命中。")
    BUL(doc, "综合判断：这不太像“人随手设的弱密码”，更可能是随机生成或带特殊符号，继续穷举的性价比很低。")


def ch2(doc):
    H1(doc, "2　对象与哈希参数")
    P(doc, "AI.zip 是 WinZip AES-256 加密的单文件压缩包，里面只有一个 PDF。zip2john 提取出的哈希是一条 "
           "143.6 MB 的 `$zip2$` 记录（data 字段是整段密文的十六进制）。", indent=0.74)
    CAP(doc, "表 2-1　AI.zip 与哈希参数")
    T(doc, ["项目", "值"], [
        ["压缩包大小", "143,624,640 字节（约 137 MB）"],
        ["加密方式", "WinZip AES-256（AE-1，压缩方法 99，deflate）"],
        ["条目数 / 原文件", "1 个；PDF 解压后 158,193,187 字节"],
        ["哈希模式", "`$zip2$`（hashcat 13600 / john ZIP、ZIP-opencl）"],
        ["mode / salt", "3（AES-256）/ `d5104ed18ea266a70c36285b7e76ea09`"],
        ["verify / auth", "`7b75` / `5e643f339fa77b9b62e3`"],
        ["压缩后长度", "143,624,398 字节（`88f88ce`，7 位十六进制）"],
        ["hash.txt", "287,248,884 字节（`$zip2$…$/zip2$` 一条）"],
    ], [4.2, 12.0], 8.8)
    P(doc, "注意：这条哈希的 `compress_length` 是 7 位十六进制、data 约 2.87 亿字符，"
           "两项都超过 hashcat 13600 模块的解析上限（1–6 位 / 16,777,216 字符），所以 hashcat 根本吃不下，"
           "只能走 john。", 9.5, indent=0.74)


def ch3(doc):
    H1(doc, "3　工具链与实测速度")
    P(doc, "john 对 ZIP 有两套后端，名字差一个后缀，速度差 50 倍：", indent=0.74)
    CAP(doc, "表 3-1　两套 john ZIP 后端对比")
    T(doc, ["后端", "设备", "本机/租用实测", "说明"], [
        ["`ZIP`", "CPU（AVX2 8x）", "11–13 万/秒", "默认选中；笔记本/无卡模式可用"],
        ["`ZIP-opencl`", "NVIDIA GPU", "627–897 万/秒", "必须显式 --format=ZIP-opencl"],
    ], [3.4, 3.4, 4.4, 5.0], 8.8)
    P(doc, "速度差异来自计算方式：CPU 版一次算 8 个候选（AVX2 8x 向量化），GPU 版靠几千个流处理器并行；"
           "两者都要对每个候选做 1000 轮 PBKDF2-HMAC-SHA1，再用 2 字节 verify 快筛，"
           "只有 1/65536 通过的候选才去算整段 143.6 MB 的 HMAC-SHA1。", indent=0.74)
    P(doc, "因此这个任务吃的是 SHA-1 的 ALU 吞吐，不是显存带宽；4090 与 4090D 差约 35%，"
           "H800 单卡理论也只有 4090 的 1.3–1.6 倍。", indent=0.74)


def ch4(doc):
    H1(doc, "4　已尝试清单")
    P(doc, "按设备分三张表。所有场次的结果都是 0g（未命中），pot 文件始终为空。", indent=0.74)

    H2(doc, "4.1　笔记本（Ryzen 7 5700U，john CPU）")
    CAP(doc, "表 4-1　笔记本上的尝试")
    T(doc, ["掩码 / 字典", "候选数", "耗时", "结果"], [
        ["rockyou.txt 原表", "14,344,391", "6 分", "0g"],
        ["`?d`×6", "1,000,000", "34 秒", "0g"],
        ["`?d`×7", "10,000,000", "6 分 21 秒", "0g"],
        ["19 + 6 位数字（生日）", "1,000,000", "31 秒", "0g"],
        ["2000/2010/2020 + 4 位", "30,000", "<1 秒", "0g"],
        ["`?d?u` 3–5 位", "62,192,448", "约 10 分", "0g"],
        ["`?d?u` 6 位", "2,176,782,336", "5 小时 49 分", "0g"],
        ["`?d?l` 3–6 位", "2,238,974,784", "约 5 小时 10 分", "0g"],
        ["4 大写 + 4 数字（4 种排列）", "4,569,760,000", "10 小时 12 分", "0g"],
    ], [6.6, 4.0, 3.2, 2.0], 8.6, (1, 2, 3))

    H2(doc, "4.2　RTX 4090D（john ZIP-opencl，6.3–6.7 M/s，累计 8 小时 47 分）")
    CAP(doc, "表 4-2　4090D 上的尝试")
    T(doc, ["掩码 / 字典", "候选数", "耗时", "结果"], [
        ["`?u?u?u?u?d?d?d`", "456,976,000", "1 分 10 秒", "0g"],
        ["`?u?u?u?d?d?d?d`", "175,760,000", "27 秒", "0g"],
        ["`?u?u?u?u?u?d?d`", "1,188,137,600", "3 分 02 秒", "0g"],
        ["`?d?d?d?d?u?u?u`", "175,760,000", "26 秒", "0g"],
        ["rockyou.txt", "14,344,391", "4 秒", "0g"],
        ["rockyou + best64 规则", "约 9.2 亿", "3 分 10 秒", "0g"],
        ["Top204k + best64", "13,056,000", "3 秒", "0g"],
        ["Top204k + OneRuleToRuleThemAll", "约 87 亿", "37 分", "0g"],
        ["Top204k + dive 规则", "约 108 亿", "1 小时 08 分", "0g"],
        ["手机号 1[3-9]XXXXXXXXX", "7,000,000,000", "19 分", "0g"],
        ["8 位纯数字", "100,000,000", "16 秒", "0g"],
        ["7 位 `?u?d`（纯大写 + 数字）", "78,364,164,097", "3 小时 17 分", "0g"],
        ["7 位 `?l?d`（纯小写 + 数字）", "78,364,164,097", "3 小时 13 分", "0g"],
    ], [6.6, 4.0, 3.2, 2.0], 8.6, (1, 2, 3))

    H2(doc, "4.3　RTX 4090（john ZIP-opencl，8.9 M/s，2026-11-18）")
    CAP(doc, "表 4-3　4090 上对 3–6 位全字符集的穷举")
    T(doc, ["掩码", "候选数", "耗时", "结果"], [
        ["62³（`?1?1?1`，`-1='?l?u?d'`）", "238,328", "<1 秒", "0g"],
        ["62⁴", "14,776,336", "3 秒", "0g"],
        ["62⁵", "916,132,832", "2 分 26 秒", "0g"],
        ["62⁶", "56,800,235,584", "1 小时 45 分", "0g"],
    ], [6.6, 4.4, 3.0, 1.8], 8.6, (1, 2, 3))
    P(doc, "这一步把 3–6 位的整片空间（含大小写混排）彻底封死：6 位结束后，"
           "`--show` 仍是 `0 password hashes cracked, 1 left`。", 9.5, indent=0.74)


def ch5(doc):
    H1(doc, "5　覆盖率与累计成本")
    P(doc, "按“长度 × 字符集”统计覆盖比例。6 位及以下已全部打满，7 位接近全空，8 位基本没动。", indent=0.74)
    CAP(doc, "表 5-1　各长度空间的覆盖情况")
    T(doc, ["长度", "全空间 62ⁿ", "已覆盖", "覆盖率"], [
        ["1–2 位", "3,906", "字典/规则已含", "≈100%"],
        ["3 位", "238,328", "238,328", "100%"],
        ["4 位", "14,776,336", "14,776,336", "100%"],
        ["5 位", "916,132,832", "916,132,832", "100%"],
        ["6 位", "56,800,235,584", "56,800,235,584", "100%"],
        ["7 位", "3,521,614,606,208", "156,728,328,192", "4.45%"],
        ["8 位", "218,340,105,584,896", "18,379,040,000", "0.0084%"],
        ["9–12 位", "—", "手机号 70 亿 + 字典", "抽样"],
    ], [2.6, 4.8, 5.6, 3.0], 8.6, (0, 1, 2, 3))
    CAP(doc, "表 5-2　三台设备的累计投入")
    T(doc, ["阶段", "设备 / 速度", "候选数", "时长", "费用"], [
        ["11-17 白天", "笔记本 CPU，约 11 万/秒", "约 90.6 亿", "约 21.5 小时", "电费"],
        ["11-17 晚", "RTX 4090D，6.3–6.7 M/s", "约 1,863 亿", "8 小时 47 分", "约 ¥16.5"],
        ["11-18 上午", "RTX 4090，8.9 M/s", "约 577 亿", "2 小时 24 分", "约 ¥5.0"],
        ["合计", "—", "约 2,531 亿", "约 32.7 小时", "约 ¥21.5"],
    ], [3.0, 4.6, 3.4, 3.2, 2.0], 8.6, (2, 3, 4))
    P(doc, "候选数按“掩码空间”直接相加，字典/规则按行数 × 规则数估算；"
           "同一候选可能被多次覆盖（例如 8 位数字既是数字掩码也被 rockyou 命中过），"
           "所以 2,531 亿是“计算量”而非“去重后的独立密码数”。", 9, indent=0.74)


def ch6(doc):
    H1(doc, "6　剩余空间与可行性")
    P(doc, "如果还要继续，只剩 7 位和 8 位这两大块。按当前实测速度折算：", indent=0.74)
    CAP(doc, "表 6-1　剩余空间的时间与成本")
    T(doc, ["长度", "剩余候选", "4090 @6.5M/s", "8×H800 @96M/s", "4090 费用"], [
        ["7 位", "3,364,886,278,016", "143 小时（6 天）", "9.7 小时", "约 ¥299"],
        ["8 位", "218,321,726,544,896", "9,330 小时（389 天）", "631 小时（26 天）", "约 ¥19,400"],
    ], [1.8, 4.8, 3.8, 3.6, 2.2], 8.4, (0, 1, 2, 3, 4))
    P(doc, "结论很直接：7 位还能算“一周内可完成”，8 位全空间已经不属于个人算力范围。"
           "8 位若一定要跑，只能加结构假设把空间砍到 10¹² 量级，例如：", indent=0.74)
    BUL(doc, "首字母大写 + 其余小写/数字：26×36⁷ ≈ 2.04 万亿，4090 约 87 小时、¥181。")
    BUL(doc, "前 6 位大小写混合 + 后 2 位数字：52⁶×10² ≈ 1.98 万亿，约 84 小时。")
    BUL(doc, "已知前后缀（如开头 `Abc`）时按前缀裁掩码，通常能再砍 2–3 个数量级。")


def ch7(doc):
    H1(doc, "7　复现命令（含断点续跑）")
    P(doc, "以下命令在 AutoDL 的 GPU 实例（Ubuntu + NVIDIA 驱动）上验证过，可直接抄。", indent=0.74)
    H2(doc, "7.1　环境搭建（一次性，约 10 分钟）")
    CODE(doc, "apt-get update -qq\n"
              "apt-get install -y build-essential ocl-icd-opencl-dev opencl-headers clinfo curl xz-utils\n"
              "mkdir -p /etc/OpenCL/vendors && echo libnvidia-opencl.so.1 > /etc/OpenCL/vendors/nvidia.icd\n"
              "clinfo -l        # 必须能看到 NVIDIA CUDA / RTX 4090\n"
              "cd /root && curl -L https://codeload.github.com/openwall/john/tar.gz/refs/heads/bleeding-jumbo -o john.tgz\n"
              "tar xzf john.tgz && cd john-bleeding-jumbo/src && ./configure && make -sj16\n"
              "cd ../run && ./john --list=formats | tr ',' '\\n' | grep -i zip   # 要有 ZIP-opencl")
    H2(doc, "7.2　上传哈希并校验")
    CODE(doc, "# 本机（Windows）上传；端口和域名以控制台为准\n"
              "scp -P 45904 D:\\hashb\\zip\\hash.txt root@connect.xxx.seetacloud.com:/root/hash.txt\n"
              "# 服务器上\n"
              "stat -c %s /root/hash.txt     # 必须是 287248884")
    H2(doc, "7.3　跑 7 位混合 + 断点续跑")
    CODE(doc, "cd /root/john-bleeding-jumbo/run\n"
              "nohup ./john --format=ZIP-opencl -1='?l?u?d' --mask='?1?1?1?1?1?1?1' \\\n"
              "  --session=mix7 --pot=/root/autodl-tmp/pat7.pot --progress-every=600 \\\n"
              "  /root/hash.txt > /root/mix7.log 2>&1 &\n\n"
              "# 中断后（关机/掉线/被杀）恢复：\n"
              "cd /root/john-bleeding-jumbo/run && ./john --restore=mix7\n\n"
              "# 进度与结果\n"
              "./john --status=mix7\n"
              "./john --show --format=ZIP-opencl --pot=/root/autodl-tmp/pat7.pot /root/hash.txt")
    P(doc, "`--restore` 会从 `run/mix7.rec` 里读回全部参数（掩码、哈希、pot 路径），不要额外再带 "
           "`--mask`/`--format`。john 大约每 10 秒写一次 `.rec`，正常关机不会丢太多进度；"
           "关机前把 `mix7.rec` 拷到 `/root/autodl-tmp/` 更保险。", 9.5, indent=0.74)
    H2(doc, "7.4　8 位的结构化模板")
    CODE(doc, "# A) 首字母大写 + 其余小写/数字（2.04 万亿）\n"
              "./john --format=ZIP-opencl -1='?l?d' --mask='?u?1?1?1?1?1?1?1' \\\n"
              "  --session=cap8 --pot=/root/autodl-tmp/pat8.pot /root/hash.txt\n"
              "# B) 前 6 位大小写混合 + 后 2 位数字（1.98 万亿）\n"
              "./john --format=ZIP-opencl -1='?l?u' --mask='?1?1?1?1?1?1?d?d' \\\n"
              "  --session=tail2 --pot=/root/autodl-tmp/pat8.pot /root/hash.txt")
    H2(doc, "7.5　验真")
    CODE(doc, "./john --show --format=ZIP-opencl --pot=/root/autodl-tmp/pat7.pot /root/hash.txt\n"
              "# 输出 /root/hash.txt:密码  →  本地验证：\n"
              "7z t -p'密码' AI.zip")


def ch8(doc):
    H1(doc, "8　本机 Windows 的 John 尝试（含坑与命令格式）")
    P(doc, "这一章记录“能不能用家里的笔记本跑 GPU”的完整尝试。结论先行：对这个 143.6 MB 的哈希，"
           "本机只能用 CPU；核显实测比 CPU 慢约 30 倍。", indent=0.74)

    H2(doc, "8.1　三种算力的真实速度")
    CAP(doc, "表 8-1　同一哈希在不同后端的速度")
    T(doc, ["后端", "速度", "相对 CPU", "说明"], [
        ["本机 CPU（`--format=zip`）", "10–12 万/秒", "1×", "AVX2 8x，16 线程吃满"],
        ["本机核显（`ZIP-opencl`）", "2.5–3.1 千/秒", "0.03×", "8 CU，真实哈希下崩塌"],
        ["租用 4090（`ZIP-opencl`）", "627 万/秒", "约 55×", "24 GB 显存，约 1 TB/s 带宽"],
        ["核显 `--test` 读数", "25.4 万/秒", "—", "假象：测试样例 data 只有几十字节"],
    ], [4.6, 3.4, 2.4, 5.8], 8.4, (1, 2))
    P(doc, "`--test` 用的是内置测试向量，跑的是纯 PBKDF2；真实 data 是 143,624,398 字节，"
           "核显的 8 个 CU 与共享 DDR4 带宽喂不动这个尺寸（实测 GPU 3D 引擎利用率只有 9.5%，"
           "john 进程反而在吃 CPU）。", 9.5, indent=0.74)

    H2(doc, "8.2　三个坑（按遇到顺序）")
    BUL(doc, "坑 1：john 的 win64 版是 Cygwin 构建，自带的 OpenCL 加载器是 ocl-icd，**不读 Windows 注册表**。"
             "把 amdocl64.dll 放进 System32、加 `HKLM\\SOFTWARE\\Khronos\\OpenCL` 键都没用，"
             "必须设 `OCL_ICD_VENDORS` 指向 AMD 的 ICD DLL。")
    BUL(doc, "坑 2：设好之后内核仍编译失败，报 `fatal error: 'opencl_device_info.h' file not found`。"
             "原因是 john 传给编译器的是 POSIX include 路径 `-I /run/kernels`，Windows 把它解析成当前盘的 "
             "`\\run\\kernels`。修复：把 `run\\kernels` 下 145 个文件（.cl 与 .h）复制到 `D:\\run\\kernels`。")
    BUL(doc, "坑 3：修好后 `--test=3 --format=ZIP-opencl` 显示 25.4 万/秒，真跑真实哈希只有 2.5–3.1 千/秒。"
             "**benchmark 不能套到真实 data 上**，这是本章最重要的一条。")
    P(doc, "顺带排除一条路：把驱动从 3570.0 升到 26.5.2（amdocl64 10.0.3584.0）后内核照样编不过，"
           "说明问题不在驱动版本，而在上面那条路径。所以**不需要升级驱动**。", 9.5, indent=0.74)
    CODE(doc, "# 坑 1：找到 ICD 并设环境变量（路径每台机器可能不同）\n"
              "Get-ChildItem C:\\Windows\\System32\\DriverStore -Recurse -Filter amdocl64.dll | Select-Object -First 1 FullName\n"
              "$env:OCL_ICD_VENDORS = 'C:/Windows/System32/DriverStore/FileRepository/amdocl.inf_amd64_xxxx/amdocl64.dll'\n\n"
              "# 坑 2：补内核头文件\n"
              "New-Item -ItemType Directory -Force 'D:\\run\\kernels'\n"
              "Copy-Item 'D:\\john\\john-1.9.0-jumbo-1-win64\\run\\kernels\\*' 'D:\\run\\kernels' -Force")

    H2(doc, "8.3　本机 CPU 的正确跑法（7 位）")
    CODE(doc, "cd 'D:\\john\\john-1.9.0-jumbo-1-win64\\run'\n"
              ".\\john.exe --format=zip -1='?l?u?d' --mask='?1?1?1?1?1?1?1' `\n"
              "  --session=mix7 --pot='D:\\hashb\\zip\\pat7.pot' --progress-every=600 `\n"
              "  'D:\\hashb\\zip\\hash.txt'\n\n"
              "# 中断后续跑（不要带 --mask / --format）\n"
              ".\\john.exe --restore=mix7\n"
              "# 看进度 / 看结果\n"
              ".\\john.exe --status=mix7\n"
              ".\\john.exe --show --format=zip --pot='D:\\hashb\\zip\\pat7.pot' 'D:\\hashb\\zip\\hash.txt'")
    P(doc, "也可以直接用脚本：`D:\\hashb\\zip\\run_gpu.ps1 -Len 7`（自动设 ICD、补 kernels、选格式），"
           "`-Resume` 续跑、`-Status` 看进度、`-Show` 看结果。", 9.5, indent=0.74)

    H2(doc, "8.4　8 位的结构化模板（Windows）")
    CAP(doc, "表 8-2　8 位的三种结构假设")
    T(doc, ["结构假设", "掩码参数（run 目录下）", "空间"], [
        ["首字母大写 + 其余小写/数字", "`-1='?l?d' --mask='?u?1?1?1?1?1?1?1'`", "2.04 万亿"],
        ["前 6 位混合 + 后 2 位数字", "`-1='?l?u' --mask='?1?1?1?1?1?1?d?d'`", "1.98 万亿"],
        ["8 位全字符集（不推荐）", "`-1='?l?u?d' --mask='?1?1?1?1?1?1?1?1'`", "218 万亿"],
    ], [4.6, 9.0, 2.6], 8.4, (2,))
    P(doc, "换 `--session` 名即可并行或分开续跑；建议固定一个 pot（如 `pat8.pot`），`--show` 时一起查。", 9.5, indent=0.74)

    H2(doc, "8.5　续跑的硬限制")
    BUL(doc, "`.rec` 文件里写死了整条命令行（含 `--format=zip`）。`--restore=mix7` 不接受额外参数，"
             "加 `--format=ZIP-opencl` 会报 `Invalid options combination or duplicate option`。")
    BUL(doc, "所以 **CPU 的进度不能搬到 GPU**；换后端只能从 0 开始（7 位重跑到 1% 约 10 分钟，影响可接受）。")
    BUL(doc, "john 约每 10 秒写一次 `.rec`；运行中不要删它；pot 与 `.rec` 分开存放便于备份。")

    H2(doc, "8.6　Windows 与 Linux 命令对照")
    CAP(doc, "表 8-3　同一动作的两种写法")
    T(doc, ["动作", "Windows（本机）", "Linux（租用机）"], [
        ["跑 7 位", "`.\\john.exe --format=zip -1='?l?u?d' --mask='?1?1?1?1?1?1?1' --session=mix7`", "`./john --format=ZIP-opencl ...`"],
        ["续跑", "`.\\john.exe --restore=mix7`", "`./john --restore=mix7`"],
        ["看进度", "`.\\john.exe --status=mix7`", "`./john --status=mix7`"],
        ["看结果", "`.\\john.exe --show --pot=... hash.txt`", "`./john --show --pot=... hash.txt`"],
    ], [2.0, 9.0, 5.2], 8.2, (0,))

    H2(doc, "8.7　租用 GPU 的实测对比（同一 143.6 MB 哈希）")
    rows = _gpu_rows()
    if not rows:
        rows = [{"name": "RTX 4090D", "mem": "24 GB", "speed_ps": 6270000, "price": 1.98}]
    top_speed = max(rows, key=lambda r: r["speed_ps"])
    top_yuan = max(rows, key=lambda r: r["speed_ps"] / r["price"])
    P(doc, "2026-11-19 起用同一份合成哈希、同一个 john（bleeding-jumbo）真实跑过 %d 张卡。"
           "结论：**%s 单卡最快（%s 万/秒）**，但按每元吞吐算 **%s 最划算（%s 万/元）**；"
           "消费卡（4090/5090 系）都明显强于同价位数据中心卡，H800 完全不适合这个内核。"
           % (len(rows), top_speed["name"], _wan(top_speed["speed_ps"]), top_yuan["name"],
              _wan(top_yuan["speed_ps"] / top_yuan["price"])), indent=0.74)
    CAP(doc, "表 8-4　%d 张卡的真实速度与性价比" % len(rows))
    T(doc, ["GPU（显存）", "ZIP-opencl 实测", "价格", "每元吞吐", "62^7 的时间 / 费用"], [
        ["%s（%s）" % (r["name"], r["mem"]), "%s 万/秒" % _wan(r["speed_ps"]),
         "¥%.2f/h" % r["price"], "%s 万/元" % _wan(r["speed_ps"] / r["price"]),
         "%d 小时 / ¥%s" % (round(_h62(r)), _cost62(r))]
        for r in rows
    ], [4.0, 3.2, 2.2, 2.6, 4.2], 8.4, (1, 2, 3, 4))
    BUL(doc, "4090 比 4090D 快约 43%（894 vs 627 万/秒），价格只贵 5%，所以 **4090 的每元吞吐高约 36%**；"
             "官方规格上 4090D 只比 4090 少约 20% 的单元与频率，实测差距更大，可能是租到的那台 4090D 有功耗/负载差异。")
    BUL(doc, "5090D 实测 1003 万/秒，是 4090D 的 1.60 倍；但 ¥3.14/h 是 1.58 倍价，所以每元吞吐 319 万几乎与 4090D 持平（317 万），"
             "仍只有 4090 的 74%。")
    BUL(doc, "PRO 6000 是 4090D 的 1.77 倍速，但单价是 4.7 倍，所以每元吞吐只有 4090D 的 40%、只有 4090 的 29%。")
    BUL(doc, "6000D（84 GB）实测 850 万/秒，是 4090D 的 1.36 倍、PRO 6000 的 77%；价格 ¥6.46/h 时每元吞吐 132 万，"
             "只有 4090D 的 42%、4090 的 31%——比 PRO 6000 略好，但仍远不如 40 系。")
    BUL(doc, "H800 反而是 4090D 的 0.46 倍——这个内核吃单卡整数吞吐与时钟，Hopper 的高带宽与 FP64 用不上；"
             "john 对 Hopper 的优化也差（raw-MD5 只有 1010 万/秒，4090D 是 6.5 亿/秒量级）。")
    BUL(doc, "`--test=3 --format=ZIP-opencl` 在这几张卡上都不可信（测试向量的 HMAC size 记为 0 KiB，"
             "PRO 6000 只报 2221 万/秒的纯 PBKDF2 读数）；只有用真实 143.6 MB 哈希跑出来的数字才算数。")
    for _r in rows:
        if _r.get("note"):
            BUL(doc, _r["note"])
    P(doc, "所以如果还要继续穷举：7 位混合用单张 4090 约 4.5 天 / ¥227（拆 2–4 台可把墙钟时间压到 1–2 天，总价不变；"
           "4090D 约 6.5 天 / ¥309）；8 位全空间 218 万亿，单张 4090 约 282 天 / ¥1.4 万，不建议。", 9.5, indent=0.74)


def ch9(doc):
    H1(doc, "9　原理：压缩包怎么加密，john / hashcat 怎么破")
    P(doc, "这一章讲清三件事：ZIP 的两种加密、WinZip AES 的密钥派生与校验、以及破解工具到底在算什么。"
           "看懂这三件事，就能明白为什么同一张显卡换个哈希类型速度能差几十倍，也能判断哪些“减小搜索范围”的办法是真的。",
      indent=0.74)

    H2(doc, "9.1　ZIP 的两种加密：ZipCrypto 与 WinZip AES")
    P(doc, "ZIP 里同时存在两套互不兼容的加密方案，很多人把它们混为一谈：", indent=0.74)
    BUL(doc, "**ZipCrypto（传统）**：1989 年的流密码，用 CRC32 参与密钥流，12 字节加密头里带 1–2 字节校验。"
             "**没有盐、没有迭代**，所以有已知明文攻击：只要知道包里任意 12 字节明文，bkcrack 几分钟就能恢复内部密钥，"
             "与密码长度、复杂度无关。")
    BUL(doc, "**WinZip AES（AE-1 / AE-2）**：2003 年加入，AES-128/192/256 + HMAC-SHA1 认证，16 字节盐，"
             "密钥由 PBKDF2-HMAC-SHA1 迭代 1000 次派生。**没有已知明文捷径**，只能老老实实猜密码。")
    P(doc, "判断方法：`zipinfo -v` 看 compression method，99 就是 AES；再看 extra field 0x9901 里的 AE 版本与强度。"
           "AI.zip 的 method=99、0x9901 = `01 00 41 45 03 08 00`，即 AE-1 + AES-256 + deflate。", indent=0.74)
    CAP(doc, "表 9-1　两种 ZIP 加密的对比")
    T(doc, ["项目", "ZipCrypto（传统）", "WinZip AES（AE-1/AE-2）"], [
        ["诞生", "1989 年（PKZIP）", "2003 年（WinZip 9）"],
        ["算法", "自研流密码，CRC32 参与密钥更新", "AES-CTR 加密 + HMAC-SHA1 认证"],
        ["密钥派生", "无盐、无迭代，口令直接初始化", "PBKDF2-HMAC-SHA1，1000 次，16 字节盐"],
        ["校验", "12 字节头里 1–2 字节", "2 字节口令校验 + 10 字节 HMAC-SHA1"],
        ["已知明文攻击", "**有**（bkcrack，分钟级）", "**无**"],
        ["hashcat 模式", "17200 / 17210 / 17220", "13600"],
        ["john 格式", "ZIP", "ZIP / ZIP-opencl"],
    ], [3.0, 6.6, 6.6], 8.4, (0,))

    H2(doc, "9.2　WinZip AES 的密钥派生与校验（为什么它慢）")
    P(doc, "AES-256 时，PBKDF2 一次派生出 66 字节：", indent=0.74)
    CODE(doc, "dk = PBKDF2-HMAC-SHA1(password, salt16, iterations=1000, dkLen=66)\n"
              "enc_key = dk[0:32]     # AES-256 加密密钥\n"
              "mac_key = dk[32:64]    # HMAC-SHA1 认证密钥\n"
              "verify  = dk[64:66]    # 2 字节口令校验")
    P(doc, "破解时先比 2 字节 verify，只有约 1/65536 的候选能通过，再算 HMAC-SHA1（覆盖整段密文）取前 10 字节比对。"
           "所以“每个候选都要算 143 MB”是错的：绝大多数候选死在 2 字节这一步。", indent=0.74)
    P(doc, "真正的成本在 PBKDF2 的 1000 轮 HMAC-SHA1（约 2000 次 SHA-1 压缩），单候选约 2 微秒/核。"
           "我们这份包的参数是 salt=16 字节、verify=0x7b75、auth=10 字节、密文 143,624,398 字节。", indent=0.74)

    H2(doc, "9.3　john 与 hashcat 的破解模型")
    P(doc, "两者做的是同一件事：**生成候选 → 用同样的 KDF 算一遍 → 和哈希里的校验值比对 → 命中就停**。"
           "区别只在候选生成器、后端实现和格式支持。", indent=0.74)
    BUL(doc, "候选生成：字典（`-a 0`）、字典+规则（`-r`）、组合（`-a 1`）、掩码（`-a 3`）、字典+掩码（`-a 6/7`）、PRINCE 等。")
    BUL(doc, "后端：CPU（AVX2/AVX-512）或 GPU（OpenCL/CUDA）。GPU 把成千上万个候选塞进 SM 并发算 1000 轮，"
             "延迟高但吞吐大；CPU 单核弱，但不用抢卡、不用传 287 MB 的哈希。")
    BUL(doc, "格式支持决定能不能跑：hashcat 的 13600 模式对 data 字段有 8 MB 上限（compress_length 最多 6 位十六进制），"
             "143 MB 的条目直接解析失败；john 的 zip2 格式标了 `FMT_HUGE_INPUT`，会把整段密文传进显存，所以能跑。")
    BUL(doc, "`--test` 的数字不可信：它用的是内置的小样例（HMAC size 记为 0 KiB），和我们真实的 143 MB 完全不是一回事。"
             "本机 `--test=5` 报 25.4 万/秒，真实哈希只有 2500/秒，差 100 倍。")

    H2(doc, "9.4　怎么减小搜索空间（真正有效的办法）")
    P(doc, "把“218 万亿”变成“几亿”，靠的是减少未知量，而不是更快的卡。按性价比排：", indent=0.74)
    CAP(doc, "表 9-2　减小搜索空间的手段与适用条件")
    T(doc, ["手段", "典型效果", "前提"], [
        ["已知长度/字符集", "62^8（218 万亿）→ 4 大写+4 数字（45.7 亿），缩小 4.8 万倍", "知道生成规则"],
        ["字典", "rockyou 1434 万、CrackStation 6400 万/14.9 亿、中文 Top10000", "密码是人选的、进过泄露库"],
        ["规则变形", "best64 约 64 条/词、OneRuleToRuleThemAll 约 5000 条/词", "口令是词典词的变体"],
        ["同站规律/OSINT", "把范围压到 45.7 亿（我们已试未中）", "有同源样本"],
        ["文件元数据", "zip 注释、文件名、mtime、压缩工具、PDF 作者", "文件里留了线索"],
        ["已知明文攻击", "仅 ZipCrypto：bkcrack 分钟级", "加密方式是 ZipCrypto"],
        ["先算成本", "`--keyspace` / `--speed-only` 先估时间与钱", "任何情况"],
        ["多卡/多机", "不缩空间，只压墙钟时间（价格线性）", "有预算"],
        ["碰撞攻击（王小云）", "**不减小空间**，见 9.5", "—"],
    ], [3.4, 8.6, 4.2], 8.4, (0,))
    BUL(doc, "最划算的顺序永远是：先问线索（同站其他密码、购买记录、站方规则），再上字典+规则，最后才是掩码穷举。"
             "我们这份包已经把 4 大写+4 数字、6 位全字符集、7 位纯大写/纯小写+数字都跑完了，说明它不落在这几个常见规律里。")

    H2(doc, "9.5　王小云的工作与“破解密码”不是一回事")
    P(doc, "2004 年王小云团队给出 MD5 的碰撞攻击，2005 年又给出 SHA-1 的碰撞攻击，这是哈希函数研究里的里程碑。"
           "但它解决的是**碰撞（collision）**，不是**原像（preimage）**，两者难度差着天文数字：", indent=0.74)
    CAP(doc, "表 9-3　碰撞与原像的区别")
    T(doc, ["问题", "定义", "MD5", "SHA-1"], [
        ["碰撞", "找两个不同消息 M≠M′，使 H(M)=H(M′)", "约 2^39，一小时级", "理论 2^63，2017 年实际做出"],
        ["原像", "给定 H(M)，反推出 M", "约 2^123", "约 2^160"],
        ["口令破解", "已知 H(口令)，猜口令", "属于原像问题", "属于原像问题"],
    ], [2.6, 6.8, 3.6, 3.2], 8.4, (0, 2, 3))
    BUL(doc, "碰撞攻击的前提是你能**同时构造两个消息**；破解口令时你只有一个哈希值，没有任何可“碰撞”的第二个消息，"
             "所以 MD5/SHA-1 的碰撞方法对口令恢复没有加速作用。")
    BUL(doc, "对 ZIP AES 更用不上：它用的是 PBKDF2-HMAC-SHA1 + AES-CTR，HMAC 的安全性不依赖抗碰撞性；"
             "就算 SHA-1 碰撞再便宜，也换不来一个口令候选。")
    BUL(doc, "碰撞的真实危害是伪造（证书、PDF、软件包、双花），不是“算出你的密码”。网上把两者混为一谈的说法，基本都是标题党。")

    H2(doc, "9.6　一句话总结")
    BUL(doc, "这个包是 WinZip AES-256（AE-1），只能猜口令；没有 ZipCrypto 那种已知明文捷径。")
    BUL(doc, "john 能跑、hashcat 跑不了，原因是 8 MB 的 data 上限；速度取决于单卡整数吞吐，不取决于显存大小或 NVLink。")
    BUL(doc, "减小搜索空间靠“减少未知量”（线索、字典、规则、掩码），不靠更快的卡，更不靠 MD5/SHA-1 碰撞。")


def ch10(doc):
    H1(doc, "10　结论与建议")
    BUL(doc, "6 位及以下的所有大小写 + 数字组合已全部排除；再往下只可能是 7 位以上或含特殊符号。")
    BUL(doc, "7 位混合要 3.36 万亿次，单卡 4090 约 6 天/¥299，8×H800 约 10 小时/¥818；这是“可做但要有预算”的级别。")
    BUL(doc, "8 位全空间 218 万亿，单卡 389 天/¥1.9 万，不建议。若坚持，只能加结构假设（见 6 章）。")
    BUL(doc, "从已排掉的空间看，密码更像随机生成或带符号；若这份文件还有别的线索（同站其他资源的密码形态、"
             "购买记录、站方规则），优先从线索出发比继续穷举划算得多。")
    P(doc, "最后提醒：以上全部是离线计算，未向任何第三方上传文件；密码仅供本人恢复自己购买的资料。", 9.5, indent=0.74)


def ch11(doc):
    H1(doc, "11　附录")
    CAP(doc, "表 11-1　相关文件")
    T(doc, ["文件", "说明"], [
        ["`D:\\hashb\\zip\\hash.txt`", "287,248,884 字节，剥掉前缀的 `$zip2$…$/zip2$`"],
        ["`D:\\hashb\\zip\\hh.txt`", "287,249,002 字节，zip2john 原始输出（带路径前缀）"],
        ["`D:\\hashb\\zip\\AI.zip`", "143,624,640 字节，待解压原件"],
        ["`D:\\hashb\\zip\\pat7.pot`", "本机 CPU 7 位 session 的 pot（未命中则 0 字节）"],
        ["`D:\\john\\...\\run\\mix7.rec`", "断点文件，约 10 秒写一次；`--restore` 靠它"],
        ["`D:\\hashb\\zip\\run_gpu.ps1`", "本机一键脚本：`-Len/-Resume/-Status/-Show`"],
        ["`D:\\run\\kernels\\`", "修复 john 内核 include 路径用的 145 个头文件副本"],
        ["`/root/pat2.pot`（服务器）", "6 位穷举的 pot，0 字节 = 未命中"],
        ["`/root/mixqueue.log`（服务器）", "2026-11-18 的队列日志"],
    ], [6.4, 9.8], 8.6)
    CAP(doc, "表 11-2　时间线")
    T(doc, ["时间", "事件"], [
        ["11-17 17:36", "创建 RTX 4090D 实例（¥1.88/h）"],
        ["11-17 18:08", "开始 7 位混合（`?u?d`），21:27 完成，0g"],
        ["11-17 21:28", "字典与规则队列跑完，0g"],
        ["11-18 02:55", "7 位小写 + 数字完成，0g；03:30 定时关机"],
        ["11-18 10:35", "创建 RTX 4090 实例（¥2.08/h）"],
        ["11-18 11:03", "62³–62⁶ 队列开始"],
        ["11-18 12:53", "62⁶ 完成（1h45m），0g，全队列结束"],
        ["11-18 12:58", "实例关机，停止计费"],
        ["11-18 17:40", "本机 OpenCL 排障开始（`OCL_ICD_VENDORS`）"],
        ["11-18 18:20", "补 `D:\\run\\kernels`，ZIP-opencl 内核可编译"],
        ["11-18 18:40", "`--test` 25.4 万/s；真实哈希可加载"],
        ["11-18 19:30", "真实哈希 GPU 仅 2.5–3.1 千/s，放弃本机 GPU"],
        ["11-18 21:00", "本机命令与坑写入第 8 章"],
    ], [4.2, 12.0], 8.6)


def main():
    doc = setup()
    cover(doc)
    ch1(doc)
    ch2(doc)
    ch3(doc)
    ch4(doc)
    ch5(doc)
    ch6(doc)
    ch7(doc)
    ch8(doc)
    ch9(doc)
    ch10(doc)
    ch11(doc)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    r = p.add_run("— 汇总完 —")
    set_run(r, 9, False, EA, EA, GREY)
    out = sys.argv[1] if len(sys.argv) > 1 else OUT
    doc.save(out)
    print("saved", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
