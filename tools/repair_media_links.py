"""重核并尝试修复媒体报道链接。

用法：python tools/repair_media_links.py
输入：媒体数据.json + 媒体数据.链接核对.json（上一轮结果）
产物：媒体数据.链接修复.json
      {"原链接": {"最终链接": "...", "状态": 200, "方式": "原链接可用 / 变体修复 / 备用搜索"}}

判定方式比上一轮严格：用普通 GET（不带 Range）重试，避免把随机拒连误判成失效；
只有普通 GET 也失败才认为需要修复；修复时依次尝试常见变体
（http↔https、有无 www、去掉双斜杠、补回被解析漏掉的下划线等）。
"""

import json
import pathlib
import re
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "媒体数据.json"
VERIFY = ROOT / "媒体数据.链接核对.json"
OUT = ROOT / "媒体数据.链接修复.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 18


def fetch(url, method="GET"):
    request = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }, method=method)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.status, response.read(4000)


def try_url(url):
    """能打开返回状态码，失败返回 0。普通 GET，随机会失败时再给一次机会。"""
    for _ in range(2):
        try:
            status, _ = fetch(url)
            if status < 400:
                return status
            return status
        except urllib.error.HTTPError as error:
            return error.code
        except Exception:
            continue
    return 0


def variants(url):
    """常见可修复变体：协议、www、双斜杠、下划线被漏掉的情况。"""
    result = [url]
    if url.startswith("http://"):
        result.append("https://" + url[7:])
    else:
        result.append("http://" + url[8:])
    if "://www." in url:
        result.append(url.replace("://www.", "://"))
    else:
        result.append(re.sub(r"://", "://www.", url, count=1))
    if "//" in url.split("://", 1)[1]:
        result.append(url.replace("//", "/", 1) if url.count("//") > 1 else url)
    # PDF 解析时下划线常被拆出去：content_123 -> content123、content123 -> content_123
    if re.search(r"content_?\d", url):
        result.append(re.sub(r"content_(\d)", r"content\1", url))
        result.append(re.sub(r"content(\d)", r"content_\1", url))
    seen = []
    for item in result:
        if item not in seen:
            seen.append(item)
    return seen


def main():
    entries = json.loads(DATA.read_text(encoding="utf-8"))
    verified = json.loads(VERIFY.read_text(encoding="utf-8")) if VERIFY.exists() else {}
    repair = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}

    urls = []
    for entry in entries:
        for source in entry["来源"]:
            url = source.get("链接")
            if url and url not in urls:
                urls.append(url)

    # 第一轮：把上一轮判为失效的链接用普通 GET 重核一遍
    suspicious = [u for u in urls if (verified.get(u, {}).get("状态") in (0, None)
                                      or (isinstance(verified.get(u, {}).get("状态"), int)
                                          and verified[u]["状态"] >= 400))]
    print("上一轮判为失效=%d，开始用普通 GET 重核" % len(suspicious))

    fixed = kept = 0
    for index, url in enumerate(suspicious, 1):
        status = try_url(url)
        if status and status < 400:
            repair[url] = {"最终链接": url, "状态": status, "方式": "原链接可用"}
            kept += 1
            print("%2d/%d 原链接可用 %s" % (index, len(suspicious), url[:70]))
            continue
        chosen = None
        for candidate in variants(url):
            if candidate == url:
                continue
            candidate_status = try_url(candidate)
            if candidate_status and candidate_status < 400:
                chosen = (candidate, candidate_status)
                break
        if chosen:
            repair[url] = {"最终链接": chosen[0], "状态": chosen[1], "方式": "变体修复"}
            fixed += 1
            print("%2d/%d 变体修复 %s -> %s" % (index, len(suspicious), url[:44], chosen[0][:44]))
        else:
            repair[url] = {"最终链接": url, "状态": status or 0, "方式": "待人工搜索"}
            print("%2d/%d 仍需人工 %s" % (index, len(suspicious), url[:70]))
        OUT.write_text(json.dumps(repair, ensure_ascii=False, indent=2), encoding="utf-8")

    OUT.write_text(json.dumps(repair, ensure_ascii=False, indent=2), encoding="utf-8")
    pending = [u for u, v in repair.items() if v["方式"] == "待人工搜索"]
    print("重核完成：原链接可用 %d，变体修复 %d，仍需人工 %d" % (kept, fixed, len(pending)))
    for url in pending:
        print("   待人工：", url)


if __name__ == "__main__":
    main()
