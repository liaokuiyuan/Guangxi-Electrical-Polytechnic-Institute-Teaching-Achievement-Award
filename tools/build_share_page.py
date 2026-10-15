"""根据 tools/share_docx_images.json 生成「成果分享」详情页 share.html。

用法：python tools/extract_share_docx.py   # 先从 docx 导出图片与说明
      python tools/build_share_page.py    # 再生成 share.html

页面做法：沿用站内版式（顶部导航 + 白色卡片），卡片内按 Word 文档顺序
一行一幅：图片在上、说明文字在下；卡片顶部有「← 返回上一页」按钮。
"""

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "share_docx_images.json"
OUT = ROOT / "share.html"

PAGE_SIZE = 12

STYLE = """
.share-toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 1rem;
}

.share-back {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    height: 2.5rem;
    padding: 0 1.1rem;
    border: 1px solid #005699;
    border-radius: 1.25rem;
    background: #FFFFFF;
    color: #014D98;
    font-size: 17px;
    line-height: 1;
    text-decoration: none;
    cursor: pointer;
}

.share-back:hover {
    background: #014D98;
    color: #FFFFFF;
    border-color: #014D98;
}

.share-count {
    color: #7A8798;
    font-size: 15px;
}

.share-card {
    display: flex;
    flex-direction: column;
    height: 60rem;
}

.share-scroll {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 0.5rem;
}

.share-scroll::-webkit-scrollbar {
    width: 0.4rem;
}

.share-scroll::-webkit-scrollbar-thumb {
    background: #C8D2DE;
    border-radius: 0.2rem;
}

.share-item {
    padding: 1.1rem 0.4rem 1.4rem;
    border-bottom: 0.06rem dashed #E3E8EF;
}

.share-item:last-child {
    border-bottom: 0;
}

.share-item .share-img {
    display: block;
    width: 100%;
    max-width: 46rem;
    margin: 0 auto;
    background: #F2F5F9;
    border: 1px solid #E3E8EF;
    border-radius: 0.5rem;
    overflow: hidden;
}

.share-item .share-img img {
    display: block;
    width: 100%;
    height: auto;
}

.share-item .share-cap {
    max-width: 46rem;
    margin: 0.85rem auto 0;
    color: #22334A;
    font-size: 18px;
    line-height: 1.85;
    text-align: justify;
}

.share-item .share-cap .share-no {
    display: inline-block;
    min-width: 2.4rem;
    margin-right: 0.5rem;
    padding: 0 0.4rem;
    border-radius: 0.25rem;
    background: #014D98;
    color: #FFFFFF;
    font-size: 15px;
    line-height: 1.7;
    text-align: center;
    vertical-align: 0.1rem;
}

@media screen and (max-width: 768px) {
    .share-card {
        height: auto;
    }

    .share-scroll {
        overflow: visible;
    }

    .share-item .share-cap {
        font-size: 16px;
        margin-top: 0.7rem;
    }

    .share-item {
        padding: 0.9rem 0.2rem 1.1rem;
    }
}
"""

SCRIPT = """
(function () {
    // 返回上一页：只有确实是从站内别的页面点进来的，才走浏览器历史；
    // 直接打开（输入网址、从收藏、二维码扫码）时上一页不是本站，一律回首页。
    // 这样不会出现"点了返回出现空白页/没反应"。
    document.getElementById('share-back').addEventListener('click', function () {
        var referrer = document.referrer || '';
        var sameSite = referrer.indexOf(window.location.origin + '/') === 0;
        var referrerPage = sameSite ? referrer.split('/').pop() : '';
        var fromOtherPage = sameSite && referrerPage && referrerPage !== 'share.html';
        if (fromOtherPage && window.history.length > 1) {
            window.history.back();
            // 历史里其实没有可回退的动作时，兜底回首页
            setTimeout(function () {
                if (!window.__shareLeft) window.location.href = 'index.html';
            }, 600);
            return;
        }
        window.location.href = 'index.html';
    });
    window.addEventListener('pagehide', function () { window.__shareLeft = true; });
})();
"""


def build_page(items):
    blocks = []
    for index, item in enumerate(items, 1):
        blocks.append(
            '                    <div class="share-item">\n'
            '                        <div class="share-img"><img src="%s" alt="%s" loading="lazy"></div>\n'
            '                        <div class="share-cap"><span class="share-no">%02d</span>%s</div>\n'
            '                    </div>' % (
                html.escape(item["文件"], quote=True),
                html.escape(item["说明"], quote=True),
                index,
                html.escape(item["说明"]),
            )
        )
    cards = "\n".join(blocks)

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8"/>
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=no">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <title>成果分享-高职创新创业教育生态共同体的构建与实践</title>
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
\t\t<li><a href="award.html">成果获奖</a></li>
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
                <div class="main-list-title-1">成果分享</div>
                <div class="main-list-title-2">您的位置：首页 | 成果分享</div>
            </div>
            <div class="main3-body">
                <div class="main3-body-right share-card">
                    <div class="main3-body-right-title">成果研究在多个会议上分享 12 次</div>
                    <div class="share-toolbar">
                        <button type="button" class="share-back" id="share-back">← 返回上一页</button>
                        <span class="share-count">共 %(count)d 次分享</span>
                    </div>
                    <div class="share-scroll">
%(cards)s
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="foot">版权所有：广西电力职业技术学院&emsp;&emsp;|&emsp;&emsp;网站备案号：桂ICP备08001145号-1&emsp;&emsp;|&emsp;&emsp;桂公网安备:45010702000119号&emsp;&emsp;|&emsp;&emsp;地址：广西南宁市玉洞大道109号&emsp;&emsp;|&emsp;&emsp;邮编：530007&emsp;&emsp;|&emsp;&emsp;联系电话：0771-2212798    </div>
</div>
<script type="text/javascript">
%(script)s
</script>
</body>
</html>
""" % {
        "style": STYLE.strip(),
        "count": len(items),
        "cards": cards,
        "script": SCRIPT.strip(),
    }


def main():
    items = json.loads(MANIFEST.read_text(encoding="utf-8"))
    items = [item for item in items if item.get("文件")]
    OUT.write_text(build_page(items), encoding="utf-8")
    print("分享条目=%d 已写入 %s" % (len(items), OUT.name))


if __name__ == "__main__":
    main()
