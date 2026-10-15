"""从《成果获奖.pdf》提取学生竞赛获奖一览表（创新创业大赛 / 挑战杯 / 职业规划大赛）。

用法：python tools/parse_student_awards.py
产物：tools/student_awards_from_pdf.json
      [{"赛事": "...", "级别": "国家级", "项目": "...", "等次": "金奖", "年份": "2021"}, ...]

表格带边框，用 PyMuPDF 的 find_tables 按格子取值最稳；
每页表头行会重复出现，按「序号是数字」判断数据行，跳过年份统计小表。
"""

import json
import pathlib
import re

import fitz

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF = ROOT / "new pdf" / "成果获奖.pdf"
OUT = ROOT / "tools" / "student_awards_from_pdf.json"

PAGES = range(23, 37)          # 学生竞赛部分：第 24~37 页（1 基）
KEEP_LEVELS = ("国家级", "自治区级", "省部级")
AWARD_ORDER = ["金奖", "银奖", "铜奖"]


def clean(text):
    return re.sub(r"[\s\u3000]+", "", (text or "").replace("\n", ""))


def main():
    doc = fitz.open(PDF)
    entries = []
    seen = set()
    for page_number in PAGES:
        for table in doc[page_number].find_tables().tables:
            for row in table.extract():
                if not row or len(row) < 6:
                    continue
                index = clean(row[0])
                if not index.isdigit():          # 表头行与统计小表都从这里排掉
                    continue
                level = clean(row[2])
                if level not in KEEP_LEVELS:
                    continue
                award = clean(row[4])
                match = re.match(r"(金|银|铜)奖", award) or re.match(r"(特等奖|一等奖|二等奖|三等奖)", award)
                key = (clean(row[1]), level, clean(row[3]), award, clean(row[5]))
                if key in seen:
                    continue
                seen.add(key)
                entries.append({
                    "序号": int(index),
                    "赛事": clean(row[1]),
                    "级别": level,
                    "项目": clean(row[3]),
                    "等次": match.group(1) + "奖" if match and not match.group(1).endswith("奖") else award,
                    "年份": (re.search(r"20\d{2}", clean(row[5])) or [None]) and
                            (re.search(r"20\d{2}", clean(row[5])).group(0) if re.search(r"20\d{2}", clean(row[5])) else ""),
                })

    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    national = [e for e in entries if e["级别"] == "国家级"]
    print("解析条目=%d（国家级 %d，自治区级 %d）" % (
        len(entries), len(national), sum(1 for e in entries if e["级别"] != "国家级")))
    for award in AWARD_ORDER:
        group = [e for e in national if e["等次"] == award]
        print("  国家级%s %d 项" % (award, len(group)))
        for entry in group[:3]:
            print("     %s %s｜%s" % (entry["年份"], entry["赛事"][:22], entry["项目"][:26]))


if __name__ == "__main__":
    main()
