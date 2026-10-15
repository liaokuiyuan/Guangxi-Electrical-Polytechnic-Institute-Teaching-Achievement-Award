"""根据 tools/student_award_highlights.json 生成学生获奖页 student-award.html。

用法：python tools/extract_award_images.py        # 从成果获奖.pdf 导出证书原图
      python tools/collect_student_awards.py      # 归档、改名为站点图片
      python tools/build_student_award_page.py    # 生成页面

产物：student-award.html
版式与「成果分享」详情页一致：白色卡片 + 卡片内滚动 + 顶部「← 返回上一页」；
每条一块：文字在上（赛事、等次、时间、参赛项目），证书/照片在下。
只展示能配到图的项目。
"""

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "student_award_highlights.json"
OUT = ROOT / "student-award.html"

AWARD_CLASS = {"金奖": "aw-gold", "银奖": "aw-silver", "铜奖": "aw-bronze"}

# 置顶顺序：廖奎源的两项证书排最前（职规赛国金 → 大创赛国银），其余按含金量排
PINNED = [
    "第三届全国大学生职业规划大赛 全国金奖",
    "中国国际大学生创新大赛（2025）全国银奖",
]


def sort_items(items):
    """按 PINNED 顺序把指定条目提到最前，其余保持原顺序。"""
    head = [item for name in PINNED for item in items if item["奖项"] == name]
    rest = [item for item in items if item not in head]
    return head + rest

STYLE = """
.stu-card {
    display: flex;
    flex-direction: column;
    height: 60rem;
}

.stu-scroll {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 0.5rem;
}

.stu-scroll::-webkit-scrollbar {
    width: 0.4rem;
}

.stu-scroll::-webkit-scrollbar-thumb {
    background: #C8D2DE;
    border-radius: 0.2rem;
}

.stu-scroll::-webkit-scrollbar-thumb:hover {
    background: #014D98;
}

.stu-item {
    padding: 1.1rem 0.4rem 1.5rem;
    border-bottom: 0.06rem dashed #E3E8EF;
}

.stu-item:last-child {
    border-bottom: 0;
}

/* 文字在上、图片在下 */
.stu-item .stu-text {
    max-width: 46rem;
    margin: 0 auto;
}

.stu-item .stu-line1 {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    color: #014D98;
    font-size: 20px;
    font-weight: 700;
    line-height: 1.6;
}

.stu-item .stu-line1 .aw {
    padding: 0.1rem 0.5rem;
    border-radius: 0.25rem;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 400;
}

.stu-item .stu-line1 .aw-gold { background: #C0392B; }
.stu-item .stu-line1 .aw-silver { background: #5B6F9E; }
.stu-item .stu-line1 .aw-bronze { background: #B07A46; }

.stu-item .stu-desc {
    margin-top: 0.35rem;
    color: #22334A;
    font-size: 17px;
    line-height: 1.85;
    text-align: justify;
}

.stu-item .stu-img {
    display: block;
    width: 100%;
    max-width: 46rem;
    margin: 0.9rem auto 0;
    border: 1px solid #E3E8EF;
    border-radius: 0.5rem;
    background: #FAFBFD;
    overflow: hidden;
}

.stu-item .stu-img img {
    display: block;
    width: 100%;
    height: auto;
}

@media screen and (max-width: 768px) {
    .stu-card {
        height: 40rem;
    }

    .stu-item .stu-line1 {
        font-size: 18px;
    }

    .stu-item .stu-desc {
        font-size: 16px;
    }
}
"""

SCRIPT = """
(function () {
    // 返回上一页：从站内别的页面进来的回上一页，直接打开的回首页；
    // 回退没生效时兜底跳首页，避免点了没反应。
    document.getElementById('stu-back').addEventListener('click', function () {
        var referrer = document.referrer || '';
        var sameSite = referrer.indexOf(window.location.origin + '/') === 0;
        var referrerPage = sameSite ? referrer.split('/').pop() : '';
        var fromOtherPage = sameSite && referrerPage && referrerPage !== 'student-award.html';
        if (fromOtherPage && window.history.length > 1) {
            window.history.back();
            setTimeout(function () {
                if (!window.__stuLeft) window.location.href = 'index.html';
            }, 600);
            return;
        }
        window.location.href = 'index.html';
    });
    window.addEventListener('pagehide', function () { window.__stuLeft = true; });

    // 点证书整屏放大：图片按原比例完整显示，不裁剪
    var viewer = document.getElementById('cert-viewer');
    var viewerImg = document.getElementById('cert-viewer-img');
    var viewerTitle = document.getElementById('cert-viewer-title');

    function closeViewer() {
        viewer.classList.remove('open');
        viewerImg.removeAttribute('src');
        document.body.style.overflow = '';
    }

    document.querySelector('.stu-scroll').addEventListener('click', function (event) {
        var box = event.target.closest('.cert-zoomable');
        if (!box) return;
        var img = box.querySelector('img');
        if (!img) return;
        viewerImg.src = img.getAttribute('src');
        viewerImg.alt = img.getAttribute('alt') || '';
        viewerTitle.textContent = img.getAttribute('alt') || '';
        viewer.classList.add('open');
        document.body.style.overflow = 'hidden';
    });

    document.getElementById('cert-viewer-back').addEventListener('click', closeViewer);
    viewer.addEventListener('click', function (event) {
        if (event.target === viewer) closeViewer();
    });
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && viewer.classList.contains('open')) closeViewer();
    });
})();
"""


def build_page(items):
    # 只保留有证书的奖项；现场照片不上这一页
    items = sort_items([item for item in items if item.get("图") and item.get("等次") != "现场"])
    gold = sum(1 for item in items if item["等次"] == "金奖")
    silver = sum(1 for item in items if item["等次"] == "银奖")
    bronze = sum(1 for item in items if item["等次"] == "铜奖")

    blocks = []
    for item in items:
        award_class = AWARD_CLASS.get(item["等次"], "aw-bronze")
        blocks.append(
            '                <div class="stu-item">\n'
            '                    <div class="stu-text">\n'
            '                        <div class="stu-line1">%s<span class="aw %s">%s</span></div>\n'
            '                        <div class="stu-desc">%s</div>\n'
            '                    </div>\n'
            '                    <div class="stu-img cert-zoomable"><img src="%s" alt="%s" loading="lazy"></div>\n'
            '                </div>' % (
                html.escape(item["奖项"]),
                award_class,
                html.escape(item["等次"]),
                html.escape(item.get("说明", "")),
                html.escape(item["图"], quote=True),
                html.escape(item["奖项"], quote=True),
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
    <title>学生获奖-高职创新创业教育生态共同体的构建与实践</title>
    <link type="text/css" rel="stylesheet" href="./css/layui.css"/>
    <link type="text/css" rel="stylesheet" href="./css/common.css"/>
    <link type="text/css" rel="stylesheet" href="./css/cghj.css"/>
    <link type="text/css" rel="stylesheet" href="./css/page-nav.css"/>
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
        <ul class="wid82 main2-body">
            <li><a href="index.html">首页</a></li>
            <li><a href="introduction.html">成果简介</a></li>
            <li><a href="shenbaoshu.html">成果申报书</a></li>
            <li><a href="implementer.html">主要完成人</a></li>
            <li><a href="report.html">成果报告</a></li>
            <li><a href="award.html">成果获奖</a></li>
            <li><a href="siku.html">四库平台</a></li>
            <li><a href="kechengjiaocai.html">专著教材</a></li>
            <li><a href="chengxiaoyingyong.html">成效应用</a></li>
            <li><a href="liluntuiguang.html">理论推广</a></li>
            <li><a href="fushexiangmeng.html">辐射东盟</a></li>
            <li><a href="media.html">媒体报道</a></li>
            <li><a href="lingdaorenke.html">领导认可</a></li>
        </ul>
    </div>
    <div class="main3">
        <div class="wid82">
            <div class="main-list-title">
                <div class="main-list-title-1">学生获奖</div>
                <div class="main-list-title-2">您的位置：首页 | 学生获奖</div>
            </div>
            <div class="main3-body">
                <div class="main3-body-right stu-card">
                    <div class="main3-body-right-title">学生竞赛获奖</div>
                    <div class="share-toolbar">
                        <button type="button" class="share-back" id="stu-back">← 返回上一页</button>
                        <span class="share-count">金奖 %(gold)d 项 · 银奖 %(silver)d 项 · 铜奖 %(bronze)d 项</span>
                    </div>
                    <div class="stu-scroll">
%(cards)s
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="foot">版权所有：广西电力职业技术学院&emsp;&emsp;|&emsp;&emsp;网站备案号：桂ICP备08001145号-1&emsp;&emsp;|&emsp;&emsp;桂公网安备:45010702000119号&emsp;&emsp;|&emsp;&emsp;地址：广西南宁市玉洞大道109号&emsp;&emsp;|&emsp;&emsp;邮编：530007&emsp;&emsp;|&emsp;&emsp;联系电话：0771-2212798    </div>
</div>
<div class="cert-viewer" id="cert-viewer">
    <div class="cert-viewer-bar">
        <button type="button" class="cert-viewer-back" id="cert-viewer-back">← 返回</button>
        <span class="cert-viewer-title" id="cert-viewer-title"></span>
    </div>
    <div class="cert-viewer-body"><img id="cert-viewer-img" src="" alt=""></div>
</div>
<script type="text/javascript">
%(script)s
</script>
</body>
</html>
""" % {
        "style": STYLE.strip(),
        "gold": gold,
        "silver": silver,
        "bronze": bronze,
        "cards": cards,
        "script": SCRIPT.strip(),
    }


def main():
    items = json.loads(DATA.read_text(encoding="utf-8"))["奖项"]
    with_image = [item for item in items if item.get("图")]
    # 现场照片不上这一页，只保留证书类奖项
    awards = sort_items([item for item in with_image if item.get("等次") != "现场"])
    OUT.write_text(build_page(items), encoding="utf-8")
    print("学生获奖条目=%d（金奖 %d、银奖 %d、铜奖 %d）已写入 %s" % (
        len(awards),
        sum(1 for i in awards if i["等次"] == "金奖"),
        sum(1 for i in awards if i["等次"] == "银奖"),
        sum(1 for i in awards if i["等次"] == "铜奖"),
        OUT.name))
    for index, item in enumerate(awards, 1):
        print("  %2d. %s | %s" % (index, item["等次"], item["奖项"][:38]))


if __name__ == "__main__":
    main()
