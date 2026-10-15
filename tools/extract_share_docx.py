"""提取《成果研究在多个会议上分享12次.docx》的文字与图片，用于制作成果分享详情页。

用法：python tools/extract_share_docx.py
输入：docs/成果研究在多个会议上分享12次.docx
产物：
  tools/share_docx_dump.txt        按文档顺序列出文字与图片位置（核对用）
  tools/share_docx_images.json     图片清单
  new images/成果分享/*.png|jpg     导出到站点图片目录

文档正文大量使用表格与文本框排版，document.paragraphs 只能拿到最外层段落，
因此这里直接按 body 的 XML 顺序遍历：段落、表格、文本框都按原顺序处理。
"""

import json
import pathlib
import re
from xml.etree import ElementTree

from docx import Document

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCX = ROOT / "docs" / "成果研究在多个会议上分享12次.docx"
IMAGE_DIR = ROOT / "new images" / "成果分享"
DUMP = ROOT / "tools" / "share_docx_dump.txt"
MANIFEST = ROOT / "tools" / "share_docx_images.json"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
V = "{urn:schemas-microsoft-com:vml}"


def paragraph_text(node):
    return "".join(t.text or "" for t in node.iter(W + "t")).strip()


def paragraph_images(node):
    """段落里的图片关系 id，按出现顺序；drawing 与 vml 都覆盖。"""
    found = []
    for child in node.iter():
        if child.tag == A + "blip":
            rid = child.get(R + "embed")
            if rid:
                found.append(rid)
        elif child.tag == V + "imagedata":
            rid = child.get(R + "id")
            if rid:
                found.append(rid)
    return found


def image_size(node, index):
    extents = [e for e in node.iter(A + "ext")]
    if index < len(extents):
        cx = int(extents[index].get("cx", 0) or 0)
        cy = int(extents[index].get("cy", 0) or 0)
        if cx and cy:
            return round(cx / 914400 * 96), round(cy / 914400 * 96)
    return None


def safe_name(text):
    cleaned = re.sub(r'[\\/:*?"<>|\s]+', "", text)
    return cleaned[:22] or "图片"


class Extractor:
    def __init__(self, document):
        self.parts = document.part.related_parts
        self.lines = []
        self.manifest = []
        self.counter = 0
        self.used = set()
        self.last_text = ""
        self.table_depth = 0

    def walk(self, element):
        for child in element:
            if child.tag == W + "p":
                self.handle_paragraph(child)
            elif child.tag == W + "tbl":
                self.table_depth += 1
                self.lines.append("【表格开始】")
                self.walk(child)
                self.lines.append("【表格结束】")
                self.table_depth -= 1
            elif child.tag == W + "tr":
                self.lines.append("  ── 行 ──")
                self.walk(child)
            elif child.tag == W + "tc":
                self.walk(child)
            else:
                # 文本框等其它容器：继续往下找段落
                self.walk(child)

    def handle_paragraph(self, node):
        text = paragraph_text(node)
        if text:
            self.last_text = text
            self.lines.append(("  " * self.table_depth) + text)
        for position, rid in enumerate(paragraph_images(node)):
            self.counter += 1
            part = self.parts.get(rid)
            if part is None:
                self.lines.append("[第%d张图：关系 %s 找不到]" % (self.counter, rid))
                continue
            caption = text or self.last_text or ("图%d" % self.counter)
            suffix = pathlib.Path(str(part.partname)).suffix or ".png"
            base = "分享%02d-%s" % (self.counter, safe_name(caption))
            name = base + suffix
            suffix_index = 1
            while name in self.used:
                suffix_index += 1
                name = "%s-%d%s" % (base, suffix_index, suffix)
            self.used.add(name)
            (IMAGE_DIR / name).write_bytes(part.blob)
            size = image_size(node, position)
            self.manifest.append({
                "序号": self.counter,
                "文件": "new%20images/成果分享/" + name,
                "说明": caption,
                "尺寸": size,
                "字节": len(part.blob),
            })
            self.lines.append("[第%d张图 -> %s%s]" % (
                self.counter, name, "，显示尺寸 %dx%d" % tuple(size) if size else ""))


def main():
    document = Document(DOCX)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    extractor = Extractor(document)
    extractor.walk(document.element.body)

    DUMP.write_text("\n".join(extractor.lines), encoding="utf-8")
    MANIFEST.write_text(json.dumps(extractor.manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("输出行数=%d 图片数=%d" % (len(extractor.lines), len(extractor.manifest)))
    for item in extractor.manifest:
        print("  ", item["序号"], item["文件"], item["尺寸"], item["说明"][:36])


if __name__ == "__main__":
    main()
