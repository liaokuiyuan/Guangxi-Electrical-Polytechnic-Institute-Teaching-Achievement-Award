"""把学生获奖页的数据准备好：国家级获奖全量 + 可配的证书图。

用法：python tools/prepare_student_awards.py
输入：tools/student_awards_from_pdf.json（tools/parse_student_awards.py 的产物）
产物：tools/student_award_highlights.json（build_student_award_page.py 的输入）

输出结构：
  {"奖项": [{"序号":1, "等次":"金奖", "赛事":"...", "项目":"...", "年份":"2021",
            "级别":"国家级", "说明":"...", "图":"..."}]}
排序：金奖 → 银奖 → 铜奖；同档按年份先后。
证书图只给确实拿到图片的条目，其余条目同一版式显示，不重复贴同一张图。
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tools" / "student_awards_from_pdf.json"
OUT = ROOT / "tools" / "student_award_highlights.json"

# 有证书/现场照片的条目：命中项目关键词就挂这张图
IMAGES = [
    ("白色森林儿童美术", "new%20images/学生获奖/中国国际互联网%2B大赛-全国金奖-白色森林儿童美术.png"),
    ("蚕燃一新", "new%20images/学生获奖/中国国际互联网%2B大赛-全国铜奖-蚕燃一新智能蚕茧烤房.png"),
    ("逃出生天", "new%20images/学生获奖/挑战杯创业计划竞赛-全国银奖-逃出生天.png"),
    ("汽车落水", "new%20images/学生获奖/挑战杯创业计划竞赛-全国银奖-逃出生天.png"),
    ("源启星链", "new%20images/大创赛国银证书.jpg"),
    ("廖奎源", "new%20images/廖奎源职规国金通知.png"),
]

AWARD_RANK = {"金奖": 0, "特等奖": 0, "银奖": 1, "一等奖": 1, "铜奖": 2, "二等奖": 2, "三等奖": 3}


def pick_image(project):
    for keyword, path in IMAGES:
        if keyword in project:
            return path
    return ""


def describe(entry):
    year = ("%s 年，" % entry["年份"]) if entry["年份"] else ""
    where = "全国总决赛" if entry["级别"] == "国家级" else "广西赛区"
    return "%s%s%s，参赛项目《%s》荣获%s。" % (year, entry["赛事"], where, entry["项目"], entry["等次"])


def main():
    entries = json.loads(SOURCE.read_text(encoding="utf-8"))
    national = [e for e in entries if e["级别"] == "国家级"]
    national.sort(key=lambda e: (AWARD_RANK.get(e["等次"], 9), e["年份"], e["序号"]))

    items = []
    for index, entry in enumerate(national, 1):
        items.append({
            "序号": index,
            "等次": entry["等次"],
            "赛事": entry["赛事"],
            "项目": entry["项目"],
            "年份": entry["年份"],
            "级别": entry["级别"],
            "说明": describe(entry),
            "图": pick_image(entry["项目"]),
        })

    for name, path, year, note in (
        ("创新创业大赛参赛团队", "new%20images/大创赛合照.jpg", "2025",
         "学校参赛团队在中国国际大学生创新大赛现场合影。"),
        ("职业规划大赛参赛团队", "new%20images/职规赛合照.jpg", "2024—2025",
         "学校参赛团队在首届、第二届全国大学生职业规划大赛现场合影；两届赛事累计获全国金奖 1 项、银奖 1 项、铜奖 4 项。"),
    ):
        items.append({
            "序号": len(items) + 1,
            "等次": "现场",
            "赛事": name,
            "项目": "",
            "年份": year,
            "级别": "现场",
            "说明": note,
            "图": path,
        })

    payload = {
        "说明": "学生获奖页数据。国家级获奖取自 new pdf/成果获奖.pdf 的学生竞赛获奖一览表，"
                "按等次与年份排序；证书图与现场照片取自申报材料。",
        "奖项": items,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("条目=%d（国家级 %d，有证书图 %d）已写入 %s" % (
        len(items), len(national), sum(1 for i in items if i["图"]), OUT.name))
    for item in items[:5]:
        print("  %s｜%s｜%s｜图：%s" % (item["年份"], item["等次"], item["项目"][:24], item["图"] or "无"))


if __name__ == "__main__":
    main()
