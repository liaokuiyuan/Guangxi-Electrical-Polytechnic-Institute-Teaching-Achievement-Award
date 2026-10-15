"""让每个页面顶部导航里"自己"那一项保持选中高亮（白底蓝字）。

用法：python tools/fix_nav_selected.py
范围：站点根目录下的 *.html

规则：页面对应的导航项加上 class="selected"，同页其它项的 selected 去掉。
一个页面必须恰好匹配到 1 个自身导航项，否则报错中止，不做部分替换。
    index.html            -> index.html
    shenbaoshu.html       -> shenbaoshu.html
    report.html           -> report.html
    share.html            -> 无导航项（首页二级页，不参与）
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
# 页面对应的导航地址；None 表示该页在导航里没有自己的位置
NAV_TARGET = {
    "index.html": "index.html",
    "introduction.html": "introduction.html",
    "shenbaoshu.html": "shenbaoshu.html",
    "report.html": "report.html",
    "implementer.html": "implementer.html",
    "award.html": "award.html",
    "siku.html": None,
    "kechengjiaocai.html": "kechengjiaocai.html",
    "chengxiaoyingyong.html": "chengxiaoyingyong.html",
    "liluntuiguang.html": "liluntuiguang.html",
    "fushexiangmeng.html": "fushexiangmeng.html",
    "media.html": "media.html",
    "lingdaorenke.html": "lingdaorenke.html",
    "student-award.html": None,
    "share.html": None,
}


def nav_items(text):
    """取导航里的 <li> 片段（含自身完整标签），用于精确替换。"""
    block = text.split('<ul class="wid82 main2-body">', 1)
    if len(block) < 2:
        return None, []
    head, tail = block
    end = tail.find("</ul>")
    nav, rest = tail[:end], tail[end:]
    items = re.findall(r'<li[^>]*>\s*<a href="[^"]+">.*?</a>\s*</li>', nav)
    return (head, nav, rest), items


def main():
    changed = []
    skipped = []
    for path in sorted(ROOT.glob("*.html")):
        if path.name not in NAV_TARGET:
            skipped.append(path.name)
            continue
        target = NAV_TARGET[path.name]
        text = path.read_text(encoding="utf-8")
        parsed, items = nav_items(text)

        # siku.html 是整屏内嵌页，本身没有顶部导航，跳过；其余页面必须有导航
        if target is None:
            skipped.append(path.name)
            continue
        if parsed is None:
            raise SystemExit("%s 里找不到导航 <ul>，已中止" % path.name)
        head, nav, rest = parsed

        matches = [item for item in items if 'href="%s"' % target in item]
        if len(matches) != 1:
            raise SystemExit("%s 匹配到 %d 个自身导航项，已中止" % (path.name, len(matches)))
        own = matches[0]

        new_nav = nav
        # 先把页面上所有 selected 去掉，再给自己那项加上，避免出现两个高亮
        new_nav = re.sub(r'<li class="selected">', "<li>", new_nav)
        new_nav = new_nav.replace(own, own.replace("<li>", '<li class="selected">', 1))
        if new_nav != nav:
            path.write_text(head + '<ul class="wid82 main2-body">' + new_nav + rest, encoding="utf-8")
            changed.append(path.name)
        else:
            skipped.append(path.name + "(本来就对)")

    print("已改=%d" % len(changed))
    print("已改文件：%s" % "、".join(changed))
    print("未涉及：%s" % "、".join(skipped))


if __name__ == "__main__":
    main()
