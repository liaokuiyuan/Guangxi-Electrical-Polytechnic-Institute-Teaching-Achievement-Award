"""主要完成人页：删除每人简介里的「主要贡献」段落，只保留简介正文。

用法：python tools/strip_implementer_contrib.py
范围：implementer.html 里 persons 数组的 bio_html 字段

不假设冒号是全角还是半角：先用「主要贡献」定位，再往前找该段 <p 起点、
往后找最近的 </p> 终点，整段删掉。简介正文一个字都不改。
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "implementer.html"

KEYWORD = "主要贡献"


def strip_contribution(bio):
    """删掉所有含「主要贡献」的整段 <p>...</p>。"""
    changed = False
    while True:
        position = bio.find(KEYWORD)
        if position == -1:
            break
        start = bio.rfind("<p", 0, position)
        end = bio.find("</p>", position)
        if start == -1 or end == -1:
            break
        end += len("</p>")
        bio = (bio[:start] + bio[end:]).strip()
        changed = True
    return bio, changed


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
    end += 2

    persons = json.loads(text[start:end])
    removed = []
    for person in persons:
        cleaned, changed = strip_contribution(person.get("bio_html", ""))
        if changed:
            person["bio_html"] = cleaned
            removed.append(person["name"])

    new_block = json.dumps(persons, ensure_ascii=False, separators=(", ", ": "))
    PAGE.write_text(text[:start] + new_block + text[end:], encoding="utf-8")

    print("完成人总数=%d 删除主要贡献=%d 人" % (len(persons), len(removed)))
    print("已处理：%s" % "、".join(removed))
    print("仍含「主要贡献」的条目=%d" % sum(1 for p in persons if KEYWORD in p.get("bio_html", "")))


if __name__ == "__main__":
    main()
