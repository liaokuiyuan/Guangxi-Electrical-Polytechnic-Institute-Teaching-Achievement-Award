"""核对媒体报道所有链接：能否打开、页面真实标题是什么。

用法：python tools/verify_media_links.py
输入：媒体数据.json
产物：媒体数据.链接核对.json
      {"链接": {"状态": 200, "标题": "网页标题", "说明": "...", "可内嵌": true/false}}

只取首字节（Range: bytes=0-0）拿响应头，能打开再取正文前 200KB 解析 <title>。
检测慢，脚本会把已核对的结果写进产物，重跑时跳过已核对的链接。
"""

import html
import json
import pathlib
import re
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "媒体数据.json"
EMBED = ROOT / "媒体数据.嵌入检测.json"
OUT = ROOT / "媒体数据.链接核对.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 15
TITLE_RE = re.compile(rb"<title[^>]*>(.*?)</title>", re.S | re.I)


def fetch(url, with_body=False):
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*",
    }
    if not with_body:
        headers["Range"] = "bytes=0-0"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        body = response.read(200000) if with_body else b""
        return response.status, body


def decode_title(raw):
    if not raw:
        return ""
    match = TITLE_RE.search(raw)
    if not match:
        return ""
    chunk = match.group(1)
    for encoding in ("utf-8", "gb18030"):
        try:
            text = chunk.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = chunk.decode("utf-8", errors="replace")
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def check(url):
    try:
        status, _ = fetch(url)
    except urllib.error.HTTPError as error:
        return {"状态": error.code, "标题": "", "说明": "HTTP %d" % error.code}
    except Exception as error:
        return {"状态": 0, "标题": "", "说明": "打不开：%s" % type(error).__name__}
    if status >= 400:
        return {"状态": status, "标题": "", "说明": "HTTP %d" % status}
    title = ""
    try:
        _, body = fetch(url, with_body=True)
        title = decode_title(body)
    except Exception as error:
        return {"状态": status, "标题": "", "说明": "取到响应头但读不到正文：%s" % type(error).__name__}
    return {"状态": status, "标题": title, "说明": "正常" if title else "正文里没有 title"}


def main():
    entries = json.loads(DATA.read_text(encoding="utf-8"))
    embeddable = {}
    if EMBED.exists():
        embeddable = {u: bool(v.get("可内嵌")) for u, v in json.loads(EMBED.read_text(encoding="utf-8")).items()}
    result = {}
    if OUT.exists():
        result = json.loads(OUT.read_text(encoding="utf-8"))

    urls = []
    for entry in entries:
        for source in entry["来源"]:
            url = source.get("链接")
            if url and url not in urls:
                urls.append(url)

    todo = [u for u in urls if u not in result]
    print("链接总数=%d 待核对=%d" % (len(urls), len(todo)))
    for index, url in enumerate(todo, 1):
        info = check(url)
        info["可内嵌"] = embeddable.get(url, False)
        result[url] = info
        print("%3d/%d %s %s %s" % (index, len(todo), info["状态"], info["标题"][:34], url[:60]))
        if index % 10 == 0:
            OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for v in result.values() if v["状态"] and v["状态"] < 400)
    titled = sum(1 for v in result.values() if v["标题"])
    print("核对完成：可打开 %d / %d，含真实标题 %d" % (ok, len(result), titled))


if __name__ == "__main__":
    main()
