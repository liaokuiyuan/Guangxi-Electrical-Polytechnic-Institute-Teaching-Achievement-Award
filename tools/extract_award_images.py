"""把《成果获奖.pdf》里的证书图片全部导出（学生竞赛与成果获奖两部分）。

用法：python tools/extract_award_images.py
产物：new images/获奖证书原图/证书-pNN-M.png

PDF 里证书是整页内的独立位图，按「页号-第几张」命名导出，便于逐张核对后使用。
"""

import pathlib

import fitz

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF = ROOT / "new pdf" / "成果获奖.pdf"
OUT_DIR = ROOT / "new images" / "获奖证书原图"

PAGES = range(5, 42)      # 第 5~41 页（1 基）包含主要发文、奖牌、课程、师资、学生竞赛的证书图
MIN_WIDTH = 300
MIN_HEIGHT = 200


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    exported = []
    for page_number in PAGES:
        page = doc[page_number - 1]
        for index, info in enumerate(page.get_images(full=True), 1):
            xref, width, height = info[0], info[2], info[3]
            if width < MIN_WIDTH or height < MIN_HEIGHT:
                continue
            pixmap = fitz.Pixmap(doc, xref)
            if pixmap.n - pixmap.alpha >= 4:
                pixmap = fitz.Pixmap(fitz.csRGB, pixmap)
            name = "证书-p%02d-%d.png" % (page_number, index)
            pixmap.save(OUT_DIR / name)
            exported.append(name)
            pixmap = None
    print("共导出 %d 张到 %s" % (len(exported), OUT_DIR))
    print("、".join(exported[:12]) + (" …" if len(exported) > 12 else ""))


if __name__ == "__main__":
    main()
