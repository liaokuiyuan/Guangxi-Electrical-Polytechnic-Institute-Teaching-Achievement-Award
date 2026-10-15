"""从「媒体报道.pdf」的案例宣传报道一览表提取结构化报道数据。

用法：python tools/parse_media_pdf.py
产物：媒体数据.json

PDF 排版上有三处坑，脚本按下面的办法绕开：

1. 表格里是逐字换行的文本层。"guangxi news" 后面单独一行 "_" 才是原本的下划线，
   拼回网址要先把下划线还原，再删掉其余空白。

2. 表格带边框，用 PyMuPDF 的 find_tables 按格子取值最稳（182 条一条不漏，
   包括第 18、19 页那 20 条）。格子里是逐行文本，标题、类别、网址、日期都可能跨行。

3. 日期列与来源行不是同一套 y：日期被拆成 "2015" / "年9" / "月20" / "日" 四行，
   年份还可能压在下一条序号行的上方。所以日期脱离格子单独扫一遍文字层，
   按阅读顺序收集成序列，再与来源行一一对齐（两条流水线的顺序是一致的），
   并用年份单调不降做校验。
"""

import json
import pathlib
import re

import fitz

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF = ROOT / "new pdf" / "媒体报道.pdf"
OUT_JSON = ROOT / "媒体数据.json"

TABLE_PAGES = range(0, 19)  # 一览表在第 1~19 页；第 20 页起是报道截图与经验交流
DATE_COLUMN_X0 = 480        # "发表时间"列左边界（链接列在 x=410 左右，日期在 504 左右）
ROW_TOLERANCE = 4           # 同一行的 y 容差（磅）
HEADER_TEXTS = {"序号", "新闻标题", "类别", "发布网站", "链接", "发表", "时间", "序", "号"}

DATE_RE = re.compile(r"(\d{4})\D{0,2}(\d{1,2})\D{0,2}(\d{1,2})\D{0,2}日")


def compress(text):
    if not text:
        return ""
    return re.sub(r"[\s\u3000]+", "", text)


def clean_title(text):
    """换行引入的空格按中文习惯去掉，英数之间保留一个空格。"""
    title = text.strip()
    title = re.sub(r"\s*([，。、；：？！（）“”‘’《》—·|])\s*", r"\1", title)
    title = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", title)
    return re.sub(r"\s{2,}", " ", title).strip()


def fix_link(text):
    """'guangxi news' + '_' -> 'guangxi_news'；'20150923_1320283' 保持原样。"""
    cleaned = (text or "").replace("\u3000", " ")
    cleaned = re.sub(r"\s*\n\s*", " ", cleaned)
    cleaned = re.sub(r"\s+(?=_)", "", cleaned)
    cleaned = re.sub(r"\s+", "", cleaned)
    return cleaned.rstrip("_")


def normalize_category(text):
    joined = compress(text)
    if "校企" in joined:
        return "校企（就业）育人案例"
    if "电亮" in joined:
        return "电亮+（思政）育人案例"
    if "优秀学生" in joined:
        return "优秀学生（校友）典型"
    return joined


def collect_rows(doc):
    """按阅读顺序取出表格里的数据行，并带上该行的纵坐标。

    返回 [(y_center, 序号或 None, 标题, 类别, 发布网站, 链接), ...]；
    序号为 None 表示这一行是上一条报道的续行（同一序号跨页/跨行）。
    """
    rows = []
    page_height = 10 ** 4
    for page_number in TABLE_PAGES:
        offset = page_number * page_height
        for table in doc[page_number].find_tables().tables:
            data = table.extract()
            boxes = table.rows
            for index, cells in enumerate(data):
                if not cells or len(cells) < 6:
                    continue
                first = compress(cells[0])
                if first and not first.isdigit():
                    continue
                site = compress(cells[3])
                link = fix_link(cells[4])
                if not (site or link):
                    continue
                y_center = 0.0
                if index < len(boxes):
                    box = boxes[index].bbox
                    y_center = offset + (box[1] + box[3]) / 2
                rows.append(
                    {
                        "y": y_center,
                        "序号": int(first) if first.isdigit() else None,
                        "标题": clean_title(cells[1] or ""),
                        "类别": normalize_category(cells[2] or ""),
                        "媒体": site,
                        "链接": link,
                    }
                )
    return rows


def collect_date_groups(doc):
    """按纵坐标收集日期组。

    日期被拆成 "2015" / "年9" / "月20" / "日" 四行，
    以 "日" 所在行的纵坐标作为这一组日期的定位点。
    """
    groups = []
    page_height = 10 ** 4
    for page_number in TABLE_PAGES:
        offset = page_number * page_height
        rows = {}
        for word in doc[page_number].get_text("words"):
            if word[0] < DATE_COLUMN_X0:
                continue
            bucket = round((word[1] + word[3]) / 2 / ROW_TOLERANCE)
            rows[bucket] = rows.get(bucket, "") + word[4].replace("\x01", "")
        buffer = ""
        for bucket in sorted(rows):
            text = compress(rows[bucket])
            if not text or text in HEADER_TEXTS:
                continue
            if re.match(r"^\d{4}$", text) and not buffer.endswith("日"):
                buffer += text
                continue
            buffer += text
            if not buffer.endswith("日"):
                continue
            match = DATE_RE.search(buffer)
            buffer = ""
            if not match:
                continue
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if 1000 <= year <= 2999 and 1 <= month <= 12 and 1 <= day <= 31:
                groups.append(
                    {
                        "y": offset + bucket * ROW_TOLERANCE,
                        "date": "%04d-%02d-%02d" % (year, month, day),
                    }
                )
    return groups


def assign_dates(rows, groups):
    """把日期组按纵坐标就近挂到来源行上。

    "日" 所在行的 y 与该行序号行的 y 最接近，用最近邻配对；
    同一行只挂一条，因此按 y 顺序贪心，已被占用的行不再接收。
    """
    for row in rows:
        row["日期"] = ""
    claimed = set()
    for group in sorted(groups, key=lambda item: item["y"]):
        candidates = [
            row for row in rows
            if not row["日期"] and id(row) not in claimed
        ]
        if not candidates:
            break
        nearest = min(candidates, key=lambda row: abs(row["y"] - group["y"]))
        nearest["日期"] = group["date"]
        claimed.add(id(nearest))
    return rows


def build_entries(rows):
    """序号行开新条目，续行并入上一条。"""
    entries = []
    for row in rows:
        if row["序号"] is not None:
            entries.append(
                {
                    "序号": row["序号"],
                    "标题": row["标题"],
                    "类别": row["类别"],
                    "日期": row["日期"],
                    "来源": [],
                }
            )
        elif not entries:
            continue
        entry = entries[-1]
        if row["日期"] and not entry["日期"]:
            entry["日期"] = row["日期"]
        if row["标题"]:
            if not entry["标题"]:
                entry["标题"] = row["标题"]
            elif entry["标题"].endswith(("：", ":")) or len(entry["标题"]) < 6:
                # 表格里标题被换行截断：前一截以冒号收尾或过短，把下一行接上
                entry["标题"] += row["标题"]
        if row["类别"] and not entry["类别"]:
            entry["类别"] = row["类别"]
        source = {"媒体": row["媒体"], "链接": row["链接"], "日期": row["日期"]}
        if not (source["媒体"] or source["链接"]):
            continue
        # 长网址跨行时，续行的格子只有后半截（没有 http 前缀、也没有媒体名），
        # 这一行不是新来源；再看上一行网址是否已经收尾（.html / .shtml 等），
        # 还没收尾就直接拼上去。
        fragment = source["链接"] and not source["链接"].startswith("http") and not source["媒体"]
        if fragment and entry["来源"]:
            # 没有媒体名的行一律是上一行网址的后半截（PDF 换行 + 下划线被拆出去），
            # 即使上一行看起来已经"结尾"也要拼，否则网址会缺一截。
            previous = entry["来源"][-1]
            previous["链接"] = fix_link(previous["链接"] + source["链接"])
            if source["日期"] and not previous["日期"]:
                previous["日期"] = source["日期"]
            continue
        source["链接"] = fix_link(source["链接"])
        if source not in entry["来源"]:
            entry["来源"].append(source)
    return entries


def main():
    doc = fitz.open(PDF)
    rows = assign_dates(collect_rows(doc), collect_date_groups(doc))
    entries = build_entries(rows)

    for entry in entries:
        entry["媒体数"] = len(entry["来源"])
        if not entry["日期"]:
            entry["日期"] = min((s["日期"] for s in entry["来源"] if s["日期"]), default="")

    OUT_JSON.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    with_date = [e for e in entries if e["日期"]]
    years = [int(e["日期"][:4]) for e in with_date]
    print("数据行=%d 条目=%d 有日期=%d" % (len(rows), len(entries), len(with_date)))
    print("无日期=%s" % [e["序号"] for e in entries if not e["日期"]])
    print("无标题=%s" % [e["序号"] for e in entries if not e["标题"]])
    print("无来源=%s" % [e["序号"] for e in entries if not e["来源"]])
    print("序号连续=%s" % (sorted(e["序号"] for e in entries) == list(range(1, len(entries) + 1))))
    print("条目日期单调=%s 区间=%s~%s" % (years == sorted(years), min(years), max(years)))
    print("多家媒体=%s" % [e["序号"] for e in entries if e["媒体数"] > 1])
    for entry in entries[:3] + entries[124:132] + entries[-3:]:
        source = entry["来源"][0] if entry["来源"] else {"链接": ""}
        print(entry["序号"], entry["日期"], entry["类别"], entry["标题"][:26], source["链接"][:40])


if __name__ == "__main__":
    main()
