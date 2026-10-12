"""根据 媒体数据.json 生成媒体报道页 media.html。

用法：python tools/build_media_page.py
输入：媒体数据.json（由 tools/parse_media_pdf.py 生成）
产物：media.html（覆盖写入，页面样式沿用站点主题色 #014D98 / #005699）

页面结构沿用站内既有版式：左侧栏目菜单 + 右侧白底卡片内容区，
列表样式参考常见新闻列表（红点 + 标题 + 右侧媒体与日期），
排列顺序与 PDF 原表序号一致，支持关键词搜索与分页，全部为页内脚本，无外部依赖。
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "媒体数据.json"
OUT = ROOT / "media.html"

PAGE_SIZE = 15

STYLE = """
.media-toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-bottom: 0.6rem;
}

/* 内容区沿用站内 PDF 阅读页的框架：卡片高度固定 60rem，
   条目在卡片内部滚动，页脚不会被长列表顶到页面中间。
   min-height:0 是 flex 子项能出现滚动条的关键。 */
.media-card {
    display: flex;
    flex-direction: column;
    height: 60rem;
}

.media-scroll {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 0.4rem;
}

.media-scroll::-webkit-scrollbar {
    width: 0.4rem;
}

.media-scroll::-webkit-scrollbar-thumb {
    background: #C8D2DE;
    border-radius: 0.2rem;
}

.media-scroll::-webkit-scrollbar-thumb:hover {
    background: #014D98;
}

.media-search {
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.media-search input {
    width: 12rem;
    height: 2.1rem;
    padding: 0 0.7rem;
    border: 1px solid #C8D2DE;
    border-radius: 0.3rem;
    font-size: 0.95rem;
    color: #333;
}

.media-search input:focus {
    border-color: #014D98;
}

.media-count {
    color: #7A8798;
    font-size: 0.9rem;
    margin-bottom: 0.6rem;
}

.media-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.62rem 0.2rem;
    border-bottom: 0.06rem dashed #E3E8EF;
    font-size: 1.05rem;
    line-height: 1.75;
}

.media-list .dot {
    flex: 0 0 auto;
    width: 0.42rem;
    height: 0.42rem;
    margin-top: 0.62rem;
    background: #C0392B;
    border-radius: 0.05rem;
}

.media-list .title {
    flex: 1 1 auto;
    min-width: 0;
    color: #014D98;
}

.media-list .title:hover {
    color: #C0392B;
    text-decoration: underline;
}

.media-list .tag {
    display: inline-block;
    margin-left: 0.5rem;
    padding: 0 0.4rem;
    border: 1px solid #C8D2DE;
    border-radius: 0.2rem;
    color: #7A8798;
    font-size: 0.78rem;
    line-height: 1.5;
    vertical-align: 0.12rem;
    white-space: nowrap;
}

.media-list .meta {
    flex: 0 0 auto;
    color: #6B7A8D;
    font-size: 0.92rem;
    white-space: nowrap;
}

.media-list .meta .site {
    margin-right: 0.65rem;
}

.media-more {
    margin-top: 0.5rem;
}

.media-more summary {
    color: #005699;
    font-size: 0.9rem;
    cursor: pointer;
}

.media-more .more-link {
    display: block;
    padding: 0.28rem 0 0.28rem 1rem;
    color: #014D98;
    font-size: 0.92rem;
}

.media-more .more-link:hover {
    color: #C0392B;
    text-decoration: underline;
}

.media-empty {
    padding: 2rem 0;
    color: #7A8798;
    text-align: center;
}

.media-pager {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    padding-top: 1.2rem;
}

.media-pager button {
    min-width: 2.1rem;
    height: 2.1rem;
    padding: 0 0.55rem;
    border: 1px solid #C8D2DE;
    border-radius: 0.3rem;
    background: #FFFFFF;
    color: #014D98;
    font-size: 0.95rem;
    font-family: inherit;
    cursor: pointer;
}

.media-pager button:hover:not(:disabled) {
    border-color: #014D98;
}

.media-pager button.active {
    border-color: #014D98;
    background: #014D98;
    color: #FFFFFF;
}

.media-pager button:disabled {
    color: #B7C0CC;
    cursor: default;
}

@media screen and (max-width: 768px) {
    .media-list li {
        flex-wrap: wrap;
        gap: 0.2rem;
    }

    .media-list .meta {
        width: 100%;
        padding-left: 1rem;
    }

    .media-search {
        margin-left: 0;
        width: 100%;
    }

    .media-search input {
        width: 100%;
    }
}
"""

SCRIPT = """
(function () {
    var listNode = document.getElementById('media-list');
    var pagerNode = document.getElementById('media-pager');
    var countNode = document.getElementById('media-count');
    var emptyNode = document.getElementById('media-empty');
    var searchInput = document.getElementById('media-search');

    var pageSize = %(page_size)d;
    var currentPage = 1;
    var keyword = '';

    function buildItem(item) {
        var li = document.createElement('li');
        var dot = document.createElement('span');
        dot.className = 'dot';
        li.appendChild(dot);

        var body = document.createElement('div');
        body.className = 'title';

        var link = document.createElement('a');
        link.className = 'title';
        link.href = item.sources[0].url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = item.title;
        body.appendChild(link);

        if (item.category) {
            var tag = document.createElement('span');
            tag.className = 'tag';
            tag.textContent = item.category;
            body.appendChild(tag);
        }

        if (item.sources.length > 1) {
            var more = document.createElement('details');
            more.className = 'media-more';
            var summary = document.createElement('summary');
            summary.textContent = '另有 ' + (item.sources.length - 1) + ' 家媒体报道';
            more.appendChild(summary);
            item.sources.slice(1).forEach(function (source) {
                var extra = document.createElement('a');
                extra.className = 'more-link';
                extra.href = source.url;
                extra.target = '_blank';
                extra.rel = 'noopener noreferrer';
                extra.textContent = (source.site || '查看原文') + (source.date ? '（' + source.date + '）' : '');
                more.appendChild(extra);
            });
            body.appendChild(more);
        }

        li.appendChild(body);

        var meta = document.createElement('div');
        meta.className = 'meta';
        var site = document.createElement('span');
        site.className = 'site';
        site.textContent = item.sources[0].site || '';
        meta.appendChild(site);
        meta.appendChild(document.createTextNode(item.date || ''));
        li.appendChild(meta);
        return li;
    }

    function render() {
        var text = keyword.trim().toLowerCase();
        var filtered = window.MEDIA_DATA.filter(function (item) {
            if (!text) {
                return true;
            }
            var haystack = (item.title + ' ' + item.category + ' ' + item.date + ' ' +
                item.sources.map(function (source) { return source.site; }).join(' ')).toLowerCase();
            return haystack.indexOf(text) !== -1;
        });

        var totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
        if (currentPage > totalPages) {
            currentPage = totalPages;
        }
        var start = (currentPage - 1) * pageSize;
        var pageItems = filtered.slice(start, start + pageSize);

        listNode.innerHTML = '';
        pageItems.forEach(function (item) {
            listNode.appendChild(buildItem(item));
        });
        emptyNode.style.display = filtered.length ? 'none' : 'block';
        countNode.textContent = '共 ' + filtered.length + ' 条报道（第 ' + currentPage + ' / ' + totalPages + ' 页）';

        pagerNode.innerHTML = '';
        if (totalPages <= 1) {
            return;
        }
        function addButton(label, page, active, disabled) {
            var button = document.createElement('button');
            button.type = 'button';
            button.textContent = label;
            if (active) {
                button.className = 'active';
            }
            button.disabled = !!disabled;
            button.addEventListener('click', function () {
                currentPage = page;
                render();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
            pagerNode.appendChild(button);
        }
        addButton('上一页', currentPage - 1, false, currentPage === 1);
        for (var page = 1; page <= totalPages; page += 1) {
            addButton(String(page), page, page === currentPage, false);
        }
        addButton('下一页', currentPage + 1, false, currentPage === totalPages);
    }

    searchInput.addEventListener('input', function () {
        keyword = searchInput.value;
        currentPage = 1;
        render();
    });

    render();
})();
"""


def render_items(entries):
    """把条目整理成页面脚本使用的数据。"""
    items = []
    for entry in entries:
        sources = [
            {"site": source["媒体"], "url": source["链接"], "date": source["日期"]}
            for source in entry["来源"]
            if source["链接"]
        ]
        if not sources:
            continue
        items.append(
            {
                "index": entry["序号"],
                "title": entry["标题"] or "（原表未列标题，详见原文）",
                "category": entry["类别"] or "其他",
                "date": entry["日期"],
                "sources": sources,
            }
        )
    # 按原表序号排列，顺序与「媒体报道.pdf」里的表格完全一致
    items.sort(key=lambda item: item["index"])
    return items


def build_page(items):
    payload = json.dumps(items, ensure_ascii=False, separators=(",", ":"))

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8"/>
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=no">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <title>媒体报道-高职创新创业教育生态共同体的构建与实践</title>
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
\t\t<li><a href="https://53plyyj9.mh.chaoxing.com/entry/page/3042461/show">四库平台</a></li>
\t\t<li><a href="kechengjiaocai.html">专著教材</a></li>
\t\t<li><a href="chengxiaoyingyong.html">成效应用</a></li>
\t\t<li><a href="liluntuiguang.html">理论推广</a></li>
\t\t<li><a href="fushexiangmeng.html">辐射东盟</a></li>
\t\t<li class="selected"><a href="media.html">媒体报道</a></li>
\t\t<li><a href="lingdaorenke.html">领导认可</a></li>
\t</ul>
</div>
    <div class="main3">
        <div class="wid82">
            <div class="main-list-title">
                <div class="main-list-title-1">媒体报道</div>
                <div class="main-list-title-2">您的位置：首页 | 媒体报道 </div>
            </div>
            <div class="main3-body layui-row">
                <div class="layui-col-md3">
                    <div class="main3-body-left">
                        <ul class="layui-menu" id="demo-menu">
                            <li class="layui-menu-item-group layui-menu-item-down" lay-options="{type: 'group'}">
                                <div class="layui-menu-body-title">
                                    境内外媒体报道 <i class="layui-icon layui-icon-right"></i>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>
                <div class="layui-col-md9">
                    <div class="main3-body-right media-card">
                        <div class="main3-body-right-title">媒体报道一览</div>
                        <div class="media-toolbar">
                            <div class="media-search">
                                <input id="media-search" type="search" placeholder="搜索标题或媒体" autocomplete="off">
                            </div>
                        </div>
                        <div class="media-count" id="media-count"></div>
                        <div class="media-scroll">
                            <ul class="media-list" id="media-list"></ul>
                            <div class="media-empty" id="media-empty" style="display:none;">没有符合条件的报道</div>
                        </div>
                        <div class="media-pager" id="media-pager"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="foot">版权所有：广西电力职业技术学院&emsp;&emsp;|&emsp;&emsp;网站备案号：桂ICP备08001145号-1&emsp;&emsp;|&emsp;&emsp;桂公网安备:45010702000119号&emsp;&emsp;|&emsp;&emsp;地址：广西南宁市玉洞大道109号&emsp;&emsp;|&emsp;&emsp;邮编：530007&emsp;&emsp;|&emsp;&emsp;联系电话：0771-2212798    </div>
</div>
<script type="text/javascript">
window.MEDIA_DATA = %(payload)s;
</script>
<script type="text/javascript">
%(script)s
</script>
</body>
</html>
""" % {
        "style": STYLE.strip(),
        "payload": payload,
        "script": SCRIPT.strip() % {"page_size": PAGE_SIZE},
    }


def main():
    entries = json.loads(DATA.read_text(encoding="utf-8"))
    items = render_items(entries)
    page = build_page(items)
    OUT.write_text(page, encoding="utf-8")
    print("条目=%d 已写入 %s" % (len(items), OUT.name))
    print("序号区间=%s ~ %s" % (items[0]["index"], items[-1]["index"]))
    print("日期区间=%s ~ %s" % (items[0]["date"], items[-1]["date"]))


if __name__ == "__main__":
    main()
