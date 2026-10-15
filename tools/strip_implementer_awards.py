"""主要完成人页：删除每人简介里的「获奖情况」段落，只保留简介正文。

用法：python tools/strip_implementer_awards.py
范围：implementer.html 里 persons 数组的 bio_html 字段

页面里 persons 是标准 JSON 数组（JavaScript 也认），因此用 json 解析、
改完再写回，避免用行替换动到 HTML 结构。简介正文一个字都不改。
"""

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "implementer.html"

# 获奖情况整段以这个标题开头，到 bio_html 结束
AWARD_BLOCK = re.compile(r'<div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #ddd;[^"]*">\s*<strong>获奖情况：</strong>.*?</div>\s*$', re.S)


def main():
    text = PAGE.read_text(encoding="utf-8")
    marker = "var persons = "
    start = text.find(marker)
    if start == -1:
        raise SystemExit("找不到 persons 数组")
    start += len(marker)
    end = text.find("}];", start)
    if end == -1:
        raise SystemExit("找不到 persons 数组结尾")
    end += 2  # 连上 "}" 与 "]"

    persons = json.loads(text[start:end])
    removed = []
    for person in persons:
        bio = person.get("bio_html", "")
        cleaned = AWARD_BLOCK.sub("", bio)
        if cleaned != bio:
            person["bio_html"] = cleaned.rstrip()
            removed.append(person["name"])

    # 写回时保持与原文件一致的紧凑 JSON（分隔符与页面里一致）
    new_block = json.dumps(persons, ensure_ascii=False, separators=(", ", ": "))
    PAGE.write_text(text[:start] + new_block + text[end:], encoding="utf-8")

    print("完成人总数=%d 删除获奖情况=%d 人" % (len(persons), len(removed)))
    print("已处理：%s" % "、".join(removed))
    print("仍有「获奖情况：」的条目=%d" % sum(1 for p in persons if "获奖情况：" in p.get("bio_html", "")))


if __name__ == "__main__":
    main()
