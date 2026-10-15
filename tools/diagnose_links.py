"""诊断打不开的媒体链接：换请求方式、换域名前缀重试，找出原因。

用法：python tools/diagnose_links.py
输入：媒体数据.json + 媒体数据.链接核对.json（挑出状态 0 或 >=400 的链接）
产物：tools/link_diagnose.txt（逐条列出各种尝试的结果，供人工判断怎么修）
"""

import json
import pathlib
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "媒体数据.json"
VERIFY = ROOT / "媒体数据.链接核对.json"
OUT = ROOT / "tools" / "link_diagnose.txt"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 15


def attempt(url, note, headers=None, method="GET"):
    base_headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": url,
    }
    if headers:
        base_headers.update(headers)
    request = urllib.request.Request(url, headers=base_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return "%s -> HTTP %d %s" % (note, response.status, response.headers.get("Content-Type", ""))
    except urllib.error.HTTPError as error:
        return "%s -> HTTP %d" % (note, error.code)
    except Exception as error:
        return "%s -> %s: %s" % (note, type(error).__name__, str(error)[:80])


def main():
    entries = json.loads(DATA.read_text(encoding="utf-8"))
    verified = json.loads(VERIFY.read_text(encoding="utf-8")) if VERIFY.exists() else {}
    broken = []
    for entry in entries:
        for source in entry["来源"]:
            url = source.get("链接")
            if not url:
                continue
            info = verified.get(url) or {}
            status = info.get("状态")
            if status == 0 or (isinstance(status, int) and status >= 400):
                broken.append((entry["序号"], entry["标题"], source["媒体"], url, status))

    lines = ["待诊断链接 %d 条" % len(broken), ""]
    for number, title, site, url, status in broken:
        lines.append("=" * 70)
        lines.append("序号 %s | 媒体 %s | 表内状态 %s" % (number, site, status))
        lines.append("标题：%s" % (title or "(原表未印标题)"))
        lines.append("原链接：%s" % url)
        lines.append("  " + attempt(url, "普通 GET"))
        lines.append("  " + attempt(url, "HEAD", method="HEAD"))
        lines.append("  " + attempt(url, "加 Referer 同域", {"Referer": "/".join(url.split("/")[:3]) + "/"}))
        # 域名前缀互换再试（媒体站常见 http/https、有无 www 的差异）
        if url.startswith("http://"):
            lines.append("  " + attempt("https://" + url[len("http://"):], "换 https"))
        if "://www." in url:
            lines.append("  " + attempt(url.replace("://www.", "://"), "去掉 www"))
        lines.append("")
        print("诊断 %s %s" % (number, url[:70]))

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("诊断结果写入 %s" % OUT.name)


if __name__ == "__main__":
    main()
