"""清理 tools/verify_media_links.py 抓到的网页标题：去掉站点名尾巴、压缩空白。

用法：python tools/clean_media_titles.py
输入/产物：媒体数据.链接核对.json（就地更新「标题」字段）

网页 <title> 常见两种脏尾巴：
  1. 站点名用 - / _ / -- / | 与新闻标题相连，例如「xxx-新华网」「xxx_动态_广西八桂职教网」；
  2. 标题里被插入了多余空格。
只清理明确的站点名标记，正文标题本身不动。
"""

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "媒体数据.链接核对.json"

# 站点名标记：出现这些片段就把它及之后的内容当成站点尾巴切掉
SITE_MARKS = [
    "-新华网", "_新华网", "新华网客户端", "-人民网", "_人民网", "--人民网",
    "-中国教育新闻网", "-中国职业技术教育网", "-中国报道", "_中国报道",
    "|手机广西网", "-广西新闻网", "_广西新闻网", "-广西八桂职教网", "_动态_广西八桂职教网",
    "-凤凰网", "_凤凰网", "_中华网", "-中华网", "-中国新闻网", "_中国新闻网",
    "--中新网", "-中新网", "_中新网", "-中国教育在线", "-教育在线", "-广西云", "_广西云",
    "-中国青年网", "-环球网", "_环球网", "-光明网", "-中国网", "-人民网+", "_人民网+",
    " - 国家", "-国家职业教育", "—教育在线", "--教育--人民网", "-广西日报", "_广西日报",
]
# 明显是站点首页/错误页的标题，不作为新闻标题使用
JUNK_TITLES = {
    "网站地图—教育在线", "广西云客户端欢迎你", "广西云", "中国新闻网", "新华网", "人民网+",
    "广西日报数字报刊", "广西画报数字报刊", "“学习强国”学习平台", "页面走丢了，请稍候再试",
    "该页面已经过期!", "Not Found- 中国教育新网网", "广西八桂职教网--有职教的地方就有我们!",
}


def clean(title):
    text = re.sub(r"\s+", " ", title or "").strip()
    if not text:
        return ""
    if text in JUNK_TITLES:
        return ""
    for mark in SITE_MARKS:
        position = text.find(mark)
        if position > 4:
            text = text[:position].strip()
    # 去掉结尾的站点分隔符与零散标点
    text = re.sub(r"[\s\-_|—]+$", "", text)
    if len(text) < 6:
        return ""
    return text


def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    changed = dropped = 0
    for info in payload.values():
        original = info.get("标题", "")
        cleaned = clean(original)
        if cleaned != original:
            info["标题"] = cleaned
            if cleaned:
                changed += 1
            else:
                dropped += 1
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已清理标题=%d 判定为站点页而弃用=%d 总链接=%d" % (changed, dropped, len(payload)))


if __name__ == "__main__":
    main()
