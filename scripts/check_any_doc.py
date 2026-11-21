# -*- coding: utf-8 -*-
"""Generic docx structure/OOXML check: python check_any_doc.py <docx> [...]"""
import sys
from collections import Counter

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm

P_ORDER = ["w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr",
           "w:widowControl", "w:numPr", "w:suppressLineNumbers", "w:pBdr", "w:shd",
           "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap", "w:overflowPunct",
           "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi", "w:adjustRightInd",
           "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents",
           "w:suppressOverlap", "w:jc", "w:textDirection", "w:textAlignment",
           "w:textboxTightWrap", "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr",
           "w:sectPr", "w:pPrChange"]
TC_ORDER = ["w:cnfStyle", "w:tcW", "w:gridSpan", "w:hMerge", "w:vMerge", "w:tcBorders",
            "w:shd", "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign",
            "w:hideMark"]
TBL_ORDER = ["w:tblStyle", "w:tblpPr", "w:tblOverlap", "w:bidiVisual", "w:tblStyleRowBandSize",
             "w:tblStyleColBandSize", "w:tblW", "w:jc", "w:tblCellSpacing", "w:tblInd",
             "w:tblBorders", "w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook",
             "w:tblCaption", "w:tblDescription"]
TR_ORDER = ["w:cnfStyle", "w:divId", "w:gridBefore", "w:gridAfter", "w:wBefore", "w:wAfter",
            "w:cantSplit", "w:trHeight", "w:tblHeader", "w:tblCellSpacing", "w:jc", "w:hidden"]
R_ORDER = ["w:rStyle", "w:rFonts", "w:b", "w:bCs", "w:i", "w:iCs", "w:caps", "w:smallCaps",
           "w:strike", "w:dstrike", "w:outline", "w:shadow", "w:emboss", "w:imprint",
           "w:noProof", "w:snapToGrid", "w:vanish", "w:webHidden", "w:color", "w:spacing",
           "w:w", "w:kern", "w:position", "w:sz", "w:szCs", "w:highlight", "w:u",
           "w:effect", "w:bdr", "w:shd", "w:fitText", "w:vertAlign", "w:rtl", "w:cs",
           "w:em", "w:lang", "w:eastAsianLayout", "w:specVanish", "w:oMath"]


def check_order(root, tag, order, problems):
    tags = [qn(t) for t in order]
    for parent in root.iter(qn(tag)):
        seen, last = [], -1
        for child in parent:
            if child.tag not in tags:
                continue
            idx = tags.index(child.tag)
            if idx < last:
                problems.append("%s out of order: %s after %s" % (
                    tag, tags[idx].split("}")[1], tags[last].split("}")[1]))
            last = max(last, idx)
            seen.append(child.tag)
        dups = [t for t, c in Counter(seen).items() if c > 1]
        if dups:
            problems.append("%s duplicate: %s" % (tag, [d.split("}")[1] for d in dups]))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for path in sys.argv[1:]:
        doc = Document(path)
        root = doc.element
        problems = []
        for tag, order in (("w:pPr", P_ORDER), ("w:tcPr", TC_ORDER), ("w:tblPr", TBL_ORDER),
                           ("w:trPr", TR_ORDER), ("w:rPr", R_ORDER)):
            check_order(root, tag, order, problems)
        widths = []
        for i, t in enumerate(doc.tables, 1):
            ws = [c.width for c in t.columns]
            tot = sum((w or Cm(0)) for w in ws) / 360000.0
            widths.append(round(tot, 2))
        heads = [p for p in doc.paragraphs if p.style.name.startswith("Heading")]
        pics = len(doc.inline_shapes)
        print("=" * 8, path)
        print("paragraphs=%d tables=%d headings=%d images=%d" % (len(doc.paragraphs), len(doc.tables), len(heads), pics))
        print("table widths(cm):", widths)
        print("table width ok:", all(w <= 16.25 for w in widths))
        print("order problems:", len(problems))
        for p in problems[:10]:
            print("  -", p)


if __name__ == "__main__":
    main()
