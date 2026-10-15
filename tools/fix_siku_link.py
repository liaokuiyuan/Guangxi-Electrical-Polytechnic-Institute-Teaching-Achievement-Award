"""把顶部导航的「四库平台」改为站内 siku.html（内嵌超星页面，带返回条）。

用法：python tools/fix_siku_link.py
范围：本站根目录下的 *.html

导航里原本写成：
    <li><a href="https://53plyyj9.mh.chaoxing.com/entry/page/3042461/show">四库平台</a></li>
改为：
    <li><a href="siku.html">四库平台</a></li>
只替换 href 的值，其余字符（缩进、class、顺序）一律不动。
每个文件必须恰好匹配到 1 处，否则报错退出，不做部分替换。
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OLD = "https://53plyyj9.mh.chaoxing.com/entry/page/3042461/show"
NEW = "siku.html"
PATTERN = re.compile(r'(<li[^>]*>\s*<a href=")' + re.escape(OLD) + r'(">四库平台</a></li>)')


def main():
    changed = []
    skipped = []
    for path in sorted(ROOT.glob("*.html")):
        # siku.html 自己就是内嵌页，正文 iframe 里必然带着这个外部地址，跳过
        if path.name == "siku.html":
            skipped.append(path.name)
            continue
        text = path.read_text(encoding="utf-8")
        matches = PATTERN.findall(text)
        if not matches:
            if OLD in text:
                raise SystemExit("%s 里出现了四库平台链接但格式不匹配，已中止" % path.name)
            skipped.append(path.name)
            continue
        if len(matches) != 1:
            raise SystemExit("%s 匹配到 %d 处四库平台链接，已中止" % (path.name, len(matches)))
        path.write_text(PATTERN.sub(r"\g<1>" + NEW + r"\g<2>", text), encoding="utf-8")
        changed.append(path.name)

    print("已改=%d 未涉及=%d" % (len(changed), len(skipped)))
    print("未涉及的文件：%s" % "、".join(skipped))


if __name__ == "__main__":
    main()
