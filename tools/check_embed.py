"""检测媒体链接是否允许被 iframe 内嵌（看响应头里的 X-Frame-Options / CSP）。

用法：python tools/check_embed.py
只读取 媒体数据.json，对每条报道的首个链接发一次 HEAD 请求（失败则退回 GET），
把结果写成 媒体数据.嵌入检测.json，供 build_media_page.py 判断用哪种打开方式。
"""

import json
import pathlib
import re
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "媒体数据.json"
OUT = ROOT / "媒体数据.嵌入检测.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 12


def probe(url):
    """返回 (是否允许内嵌, 说明)。拿不到响应时按不允许处理，保守一点。

    用 GET + Range: bytes=0-0 只取首字节拿响应头：
    不少站点拒绝 HEAD 请求（返回 403/405），用 HEAD 检测会把可内嵌的链接误判成不可内嵌。
    """
    request = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Range": "bytes=0-0",
    })
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            headers = {k.lower(): v for k, v in response.headers.items()}
            status = response.status
    except urllib.error.HTTPError as error:
        headers = {k.lower(): v for k, v in (error.headers or {}).items()}
        status = error.code
    except Exception as error:  # 网络不可达、超时、证书问题
        return False, "取不到响应：%s" % type(error).__name__

    xfo = headers.get("x-frame-options", "")
    csp = headers.get("content-security-policy", "")
    if xfo:
        return False, "X-Frame-Options: %s" % xfo
    if "frame-ancestors" in csp:
        match = re.search(r"frame-ancestors([^;]*)", csp)
        return False, "CSP frame-ancestors:%s" % (match.group(1) if match else "")
    if status >= 400:
        return False, "HTTP %d" % status
    return True, "允许内嵌（HTTP %d）" % status


def main():
    entries = json.loads(DATA.read_text(encoding="utf-8"))
    result = {}
    allowed = blocked = 0
    for entry in entries:
        for source in entry["来源"]:
            url = source.get("链接")
            if not url or url in result:
                continue
            ok, note = probe(url)
            result[url] = {"可内嵌": ok, "说明": note}
            if ok:
                allowed += 1
            else:
                blocked += 1
            print("%s  %s  %s" % ("可内嵌" if ok else "禁止内嵌", note, url[:90]))
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("链接总数=%d 可内嵌=%d 禁止内嵌=%d -> %s" % (len(result), allowed, blocked, OUT.name))


if __name__ == "__main__":
    main()
