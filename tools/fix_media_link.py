"""把顶部导航的「媒体报道」从学校新闻页改成本站自己的 media.html。

用法：python tools/fix_media_link.py
范围：本站根目录下的 *.html（不含子目录与 pdfjs 等第三方页面）

导航都写成 <li ...><a href="https://www.gxdlxy.com/xwdt/mtkdy.htm">媒体报道</a></li>，
这里只替换 href 的值，其余字符（缩进、class、顺序）一律不动。
任一文件匹配到的次数不是 1 次就直接报错退出，不做部分替换。
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OLD = 'https://www.gxdlxy.com/xwdt/mtkdy.htm'
NEW = 'media.html'
PATTERN = re.compile(r'(<li[^>]*>\s*<a href=")' + re.escape(OLD) + r'(">媒体报道</a></li>)')


def main():
    changed = []
    skipped = []
    for path in sorted(ROOT.glob("*.html")):
        text = path.read_text(encoding="utf-8")
        matches = PATTERN.findall(text)
        if not matches:
            if OLD in text:
                raise SystemExit("%s 里出现了媒体链接但格式不匹配，已中止" % path.name)
            skipped.append(path.name)
            continue
        if len(matches) != 1:
            raise SystemExit("%s 匹配到 %d 处媒体链接，已中止" % (path.name, len(matches)))
        path.write_text(PATTERN.sub(r"\g<1>" + NEW + r"\g<2>", text), encoding="utf-8")
        changed.append(path.name)

    print("已改=%d 未涉及=%d" % (len(changed), len(skipped)))
    print("未涉及的文件：%s" % "、".join(skipped))


if __name__ == "__main__":
    main()
