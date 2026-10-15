"""根据 tools/award_highlights.json 生成成果获奖页 award.html。

用法：python tools/build_award_page.py
输入：tools/award_highlights.json（证书图 + 奖项说明，按含金量排序）
产物：award.html

版式：沿用站内白色卡片，一条一幅 —— 证书图片在上、奖项说明在下；
说明里写清「什么时间、在什么比赛、荣获什么奖项」，并标注级别。
底部保留原始材料入口（成果获奖.pdf），便于查阅完整清册。
"""

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "award_highlights.json"
OUT = ROOT / "award.html"

LEVEL_CLASS = {"国家级": "lv-national", "省部级": "lv-province"}

STYLE = """
.award-intro {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 1rem;
    color: #4A5568;
    font-size: 16px;
    line-height: 1.8;
}

.award-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.2rem 0.7rem;
    border-radius: 1rem;
    background: #EAF1FA;
    color: #014D98;
    font-size: 15px;
}

.award-card {
    display: flex;
    flex-direction: column;
    height: 60rem;
}

.award-scroll {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 0.5rem;
}

.award-scroll::-webkit-scrollbar {
    width: 0.4rem;
}

.award-scroll::-webkit-scrollbar-thumb {
    background: #C8D2DE;
    border-radius: 0.2rem;
}

.award-item {
    padding: 1.2rem 0.4rem 1.5rem;
    border-bottom: 0.06rem dashed #E3E8EF;
}

.award-item:last-of-type {
    border-bottom: 0;
}

.award-item .award-img {
    display: block;
    width: 100%;
    max-width: 44rem;
    margin: 0 auto;
    border: 1px solid #E3E8EF;
    border-radius: 0.5rem;
    background: #FAFBFD;
    overflow: hidden;
}

.award-item .award-img img {
    display: block;
    width: 100%;
    height: auto;
}

.award-item .award-body {
    max-width: 44rem;
    margin: 0.9rem auto 0;
}

.award-item .award-name {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    color: #014D98;
    font-size: 19px;
    font-weight: 700;
    line-height: 1.6;
}

.award-item .award-name .level {
    padding: 0.1rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 14px;
    font-weight: 400;
    line-height: 1.6;
}

.award-item .award-name .level.lv-national {
    background: #C0392B;
    color: #FFFFFF;
}

.award-item .award-name .level.lv-province {
    background: #014D98;
    color: #FFFFFF;
}

.award-item .award-time {
    margin-top: 0.3rem;
    color: #7A8798;
    font-size: 15px;
}

.award-item .award-desc {
    margin-top: 0.5rem;
    color: #22334A;
    font-size: 17px;
    line-height: 1.85;
    text-align: justify;
}

.award-foot {
    margin-top: 1rem;
    padding-top: 0.9rem;
    border-top: 0.06rem dashed #E3E8EF;
    color: #7A8798;
    font-size: 14px;
    line-height: 1.8;
}

.award-foot a {
    color: #005699;
    text-decoration: underline;
}

@media screen and (max-width: 768px) {
    .award-card {
        height: auto;
    }

    .award-scroll {
        overflow: visible;
    }

    .award-item .award-desc {
        font-size: 16px;
    }
}
"""


def build_page(items):
    blocks = []
    for item in items:
        level = item.get("级别", "")
        level_class = LEVEL_CLASS.get(level, "lv-province")
        # 文字在上、证书在下
        blocks.append(
            '                    <div class="award-item">\n'
            '                        <div class="award-body">\n'
            '                            <div class="award-name">%s<span class="level %s">%s</span></div>\n'
            '                            <div class="award-time">%s</div>\n'
            '                            <div class="award-desc">%s</div>\n'
            '                        </div>\n'
            '                        <div class="award-img"><img src="%s" alt="%s" loading="lazy"></div>\n'
            '                    </div>' % (
                html.escape(item["奖项"]),
                level_class,
                html.escape(level),
                html.escape(item.get("时间", "")),
                html.escape(item.get("说明", "")),
                html.escape(item["图"], quote=True),
                html.escape(item["奖项"], quote=True),
            )
        )
    cards = "\n".join(blocks)
    national = sum(1 for item in items if item.get("级别") == "国家级")
    province = sum(1 for item in items if item.get("级别") == "省部级")

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8"/>
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=no">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <title>成果获奖-高职创新创业教育生态共同体的构建与实践</title>
    <link type="text/css" rel="stylesheet" href="./css/layui.css"/>
    <link type="text/css" rel="stylesheet" href="./css/common.css"/>
    <link type="text/css" rel="stylesheet" href="./css/cghj.css"/>
    <style>%(style)s</style>
    <script type="text/javascript" src="./js/layui.js"></script>
    <script type="text/javascript" src="./js/init.js"></script>
</head>
<body>
<div class="container">
    <div class="main1" style="height:15rem;">
        <div class="wid82 main1-body" style="height:15rem; justify-content:flex-start;">
            <img class="header-logo" src="new%%20images/logo.png" alt="广西电力职业技术学院">
            <div class="header-divider"></div>
            <div class="header-title-text" role="heading" aria-level="1">
                <div class="header-title-kicker">北引·东联·西融</div>
                <div class="header-project-title">高职创新创业教育生态共同体的构建与实践</div>
            </div>
        </div>
    </div>
    <div class="main2">
\t<ul class="wid82 main2-body">
\t\t<li><a href="index.html">首页</a></li>
\t\t<li><a href="introduction.html">成果简介</a></li>
\t\t<li><a href="shenbaoshu.html">成果申报书</a></li>
\t\t<li><a href="implementer.html">主要完成人</a></li>
\t\t<li><a href="report.html">成果报告</a></li>
\t\t<li class="selected"><a href="award.html">成果获奖</a></li>
\t\t<li><a href="siku.html">四库平台</a></li>
\t\t<li><a href="kechengjiaocai.html">专著教材</a></li>
\t\t<li><a href="chengxiaoyingyong.html">成效应用</a></li>
\t\t<li><a href="liluntuiguang.html">理论推广</a></li>
\t\t<li><a href="fushexiangmeng.html">辐射东盟</a></li>
\t\t<li><a href="media.html">媒体报道</a></li>
\t\t<li><a href="lingdaorenke.html">领导认可</a></li>
\t</ul>
</div>
    <div class="main3">
        <div class="wid82">
            <div class="main-list-title">
                <div class="main-list-title-1">成果获奖</div>
                <div class="main-list-title-2">您的位置：首页 | 成果获奖</div>
            </div>
            <div class="main3-body">
                <div class="main3-body-right award-card">
                    <div class="main3-body-right-title">代表性获奖成果</div>
                    <div class="award-intro">
                        <span class="award-badge">国家级 %(national)d 项</span>
                        <span class="award-badge">省部级 %(province)d 项</span>
                    </div>
                    <div class="award-scroll">
%(cards)s
                        <div class="award-foot">
                            完整获奖清册（含国家级 21 项、省部级 36 项及学生竞赛、课程建设、教材建设、师资建设等分类明细）见
                            <a href="pdfjs/web/viewer.html?file=../../new%%20pdf/%%E6%%88%%90%%E6%%9E%%9C%%E6%%8E%%88%%E5%%A5%%96.pdf" target="_blank" rel="noopener">成果获奖.pdf</a>。
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="foot">版权所有：广西电力职业技术学院&emsp;&emsp;|&emsp;&emsp;网站备案号：桂ICP备08001145号-1&emsp;&emsp;|&emsp;&emsp;桂公网安备:45010702000119号&emsp;&emsp;|&emsp;&emsp;地址：广西南宁市玉洞大道109号&emsp;&emsp;|&emsp;&emsp;邮编：530007&emsp;&emsp;|&emsp;&emsp;联系电话：0771-2212798    </div>
</div>
</body>
</html>
""" % {
        "style": STYLE.strip(),
        "national": national,
        "province": province,
        "cards": cards,
    }


def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    items = payload["奖项"]
    OUT.write_text(build_page(items), encoding="utf-8")
    print("奖项=%d（国家级 %d、省部级 %d）已写入 %s" % (
        len(items),
        sum(1 for i in items if i.get("级别") == "国家级"),
        sum(1 for i in items if i.get("级别") == "省部级"),
        OUT.name,
    ))


if __name__ == "__main__":
    main()
