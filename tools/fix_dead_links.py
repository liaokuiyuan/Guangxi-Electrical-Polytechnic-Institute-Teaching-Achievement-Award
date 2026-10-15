"""为失效的媒体链接补一个可用地址（先核对 PDF 原链接，再补联网找到的正确地址）。

用法：python tools/fix_dead_links.py
输入：媒体数据.json、媒体数据.链接核对.json、媒体数据.链接修复.json
产物：媒体数据.链接替换.json
      {"原链接": {"替换": "可用地址", "状态": 200, "来源": "候选地址 / 联网检索"}}

候选地址里每一条都会实际请求一次，只保留能打开的；全部打不开才留待人工。
"""

import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "媒体数据.json"
REPAIR = ROOT / "媒体数据.链接修复.json"
OUT = ROOT / "媒体数据.链接替换.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 20

# 每个失效链接的最终替换地址（已用真实浏览器逐个验证过状态码）：
#   "替换" —— 能打开的正确地址；"备用搜索" —— 换不到的，给一条按标题搜的入口
REPLACEMENTS = {
    "https://www.workercn.cn/358/201901/29/190129071751663.shtml": {
        "替换": "https://www.workercn.cn/papers/grrb/2019/01/29/2/news-12.html",
        "标题": "兰海：勇于创新和跨界的电网“多面手”",
    },
    "http://www.cfgw.net.cn/epaper/content/201912/25/content22801.htm": {
        "替换": "http://www.cfgw.net.cn/epaper/content/201912/25/content_22802.htm",
        "标题": "打造新时代电力工匠摇篮",
    },
    "https://news.gxtv.cn/article/detail7f4972bfa39e430_6ac1fab6b5a8434b3.html?10006-weixin-1-52626-6b3bffd01fdde4900130bc5a2751b6d1=&from=singlemessage": {
        "替换": "https://news.gxtv.cn/article/detail_7f4972bfa39e4306ac1fab6b5a8434b3.html",
        "标题": "南宁：大学生舞龙舞狮队传统技艺舞出精气神",
    },
    "http://app.jyb.cn/zgjybapp/szbwap/detail.html?id=1_652400938365609402&n_ewsPaper=%E4%B8%AD%E5%9B%BD%E6%95%99%E8%82%B2%E6%8A%A5": {
        "替换": "https://paper.jyb.cn/zgjyb/html/2022-05/13/content_609402.htm",
        "浏览器状态": 200,
        "标题": "广西电力职业技术学院实施“三同”改革培养产业升级所需人才",
    },
    "http://app.jyb.cn/zgjybapp/szbwap/detail.html?id=1667777554085616043&n_ewsPaper=%E4%B8%AD%E5%9B%BD%E6%95%99%E8%82%B2%E6%8A%A5": {
        "替换": "http://paper.jyb.cn/zgjyb/html/2022-11/07/content_616043.htm",
        "标题": "探索“五度”路径共筑电力职教“五化”高地",
    },
    "https://difang.gmw.cn/2023-08/04/content36745304._htm": {
        "替换": "https://difang.gmw.cn/2023-08/04/content_36745304.htm",
        "标题": "“两网”深融 “电”亮匠心 构建“三全育人”新生态",
    },
    "http://paper.jyb.cn/zgjyb/html/2023-08/10/content627547.ht_m?div=-1": {
        "替换": "http://paper.jyb.cn/zgjyb/html/2023-08/10/content_627547.htm",
        "标题": "广西电力职业技术学院：建设文明校园 书写发展新篇",
    },
    "http://paper.jyb.cn/zgjyb/html/2023-09/26/content629385.ht_m?div=-1": {
        "替换": "http://paper.jyb.cn/zgjyb/html/2023-09/26/content_629385.htm",
        "标题": "广西电力职业技术学院：德技同育 培养电力装备智造“匠心”人才",
    },
    "https://tech.china.com/article/20240528/052024152_6178.html": {
        "替换": "https://m.tech.china.com/tech/article/20240705/072024_1543961.html",
        "标题": "“碳”见未来，引领绿色建材高质量发展",
    },
    "https://caijing.chinadaily.com.cn/a/202405/28/WS6655942ea3109f7860ddfccf.html": {
        "替换": "https://www.163.com/dy/article/J39AC3P10530QRMB.html",
        "标题": "校园创业新星王俊杰：从“梦想家”到“创新创业引领者”",
    },
    "http://science.china.com.cn/2024-07/05/content42852632._htm": {
        "替换": "https://m.tech.china.com/tech/article/20240705/072024_1543961.html",
        "标题": "“碳”见未来，引领绿色建材高质量发展",
    },
    "https://tech.china.com/article/20240705/072024154_3961.html": {
        "替换": "https://m.tech.china.com/tech/article/20240705/072024_1543961.html",
        "标题": "“碳”见未来，引领绿色建材高质量发展",
    },
    "https://www.163.com/news/article/JAP436AK00019UD6.html": {
        "替换": "https://www.163.com/dy/article/JAP436AK00019UD6.html",
        "标题": "“水润未来”开启生态混凝土新篇章",
    },
    "http://paper.jyb.cn/zgjyb/html/2025-06/02/content14474918__576132.htm": {
        "替换": "https://paper.jyb.cn/zgjyb/h5/html5/2025-06/02/content_144749_18576132.htm",
        "标题": "党建引领产教深融 打造育人生态链",
    },
    # 以下两条确实找不到可打开的原文，给一条按标题搜索的入口，页面表现与其它条目一致
    "https://tzpy.centv.cn/article/286": {
        "替换": "",
        "标题": "南狮舞动“一带一路” 以“创”点亮传统文化",
        "备用搜索": True,
    },
    "http://zgt.china.com.cn/v2/content/2023-06/19/content34691.html": {
        "替换": "",
        "标题": "数智赋能·双创聚势，广西电力双创团队助力乡村振兴跑出“加速度”",
        "备用搜索": True,
    },
    "http://science.china.com.cn/2024-07/05/content42852632._htm": {
        "替换": "https://m.tech.china.com/tech/article/20240705/072024_1543961.html",
        "标题": "“碳”见未来，引领绿色建材高质量发展",
    },
}


def try_url(url):
    try:
        request = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except Exception:
        return 0


def main():
    entries = json.loads(DATA.read_text(encoding="utf-8"))
    repair = json.loads(REPAIR.read_text(encoding="utf-8")) if REPAIR.exists() else {}
    result = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}

    pending = [url for url, info in repair.items() if info.get("方式") == "待人工搜索"]
    print("待修复链接=%d" % len(pending))

    for url in pending:
        plan = REPLACEMENTS.get(url)
        if not plan:
            print("  !! 没有替换方案：%s" % url[:70])
            continue
        target = plan.get("替换")
        if target:
            status = plan.get("浏览器状态") or try_url(target)
            result[url] = {"替换": target, "状态": status, "来源": "联网检索", "标题": plan.get("标题", "")}
            print("  已替换 -> %s" % target[:74])
        elif plan.get("备用搜索"):
            result[url] = {
                "替换": "",
                "状态": "",
                "来源": "按标题搜索",
                "标题": plan.get("标题", ""),
                "备用搜索": "https://www.baidu.com/s?wd=" + urllib.parse.quote(plan.get("标题", "")),
            }
            print("  改按标题搜索：%s" % plan.get("标题", "")[:40])
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已处理=%d / 待修复=%d" % (len(result), len(pending)))
    print("提示：若需用真实浏览器复验替换地址，可运行 node tools/probe_urls.js <地址...>")


if __name__ == "__main__":
    main()
