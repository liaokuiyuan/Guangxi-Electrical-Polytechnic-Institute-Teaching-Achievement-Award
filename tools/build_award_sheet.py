"""把导出的成果获奖证书图拼成一张总览页，便于挑选。

用法：python tools/build_award_sheet.py <证书图目录> <输出目录>
产物：<输出目录>/sheet.html
"""

import html
import pathlib
import sys


def sort_key(name):
    page, index = name[1:].split("_")
    return int(page), int(index.split(".")[0])


def main():
    source = pathlib.Path(sys.argv[1])
    out_dir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else source
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted((p.name for p in source.glob("p*.png")), key=sort_key)
    cards = [
        '<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (
            html.escape(name, quote=True), html.escape(name), html.escape(name))
        for name in files
    ]
    document = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>成果获奖证书总览</title>
<style>
body { background: #fff; font-family: sans-serif; margin: 0; padding: 8px; }
.grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
figure { margin: 0; border: 1px solid #ddd; padding: 4px; text-align: center; }
img { width: 100%; height: 150px; object-fit: contain; background: #fafafa; }
figcaption { font-size: 11px; color: #333; }
</style></head>
<body><div class="grid">
__CARDS__
</div></body></html>
""".replace("__CARDS__", "\n".join(cards))
    (out_dir / "sheet.html").write_text(document, encoding="utf-8")
    print("总览页已生成：%s（图片 %d 张）" % (out_dir / "sheet.html", len(files)))


if __name__ == "__main__":
    main()
