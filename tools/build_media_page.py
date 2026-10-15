"""根据 媒体数据.json 生成媒体报道页 media.html。

用法：python tools/parse_media_pdf.py   # 先生成/更新 媒体数据.json
      python tools/check_embed.py       # 再检测各链接能否内嵌（可选，缺省则全部新窗口打开）
      python tools/build_media_page.py  # 最后生成 media.html

产物：media.html（覆盖写入，页面样式沿用站点主题色 #014D98 / #005699）

页面结构沿用站内既有版式：左侧栏目菜单 + 右侧白底卡片内容区，
列表样式参考常见新闻列表（红点 + 标题 + 右侧媒体与日期），
排列顺序与 PDF 原表序号一致，支持关键词搜索与分页。
点击标题时：允许内嵌的链接在页内整屏打开并带返回条（和四库平台一致），
禁止内嵌的链接才新窗口打开，用户不会"点进去回不来"。
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "媒体数据.json"
EMBED_DATA = ROOT / "媒体数据.嵌入检测.json"
VERIFY_DATA = ROOT / "媒体数据.链接核对.json"
REPLACE_DATA = ROOT / "媒体数据.链接替换.json"
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

/* 页内整屏阅读层：允许内嵌的媒体链接在站内打开，
   顶部固定一条返回条（尺寸与四库平台页一致），用户随时能回列表。 */
.media-viewer {
    position: fixed;
    inset: 0;
    z-index: 2000;
    display: none;
    flex-direction: column;
    background: #FFFFFF;
}

.media-viewer.open {
    display: flex;
}

.media-viewer-bar {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    gap: 0.9rem;
    min-height: 4.6rem;
    padding: 0.45rem 1.1rem;
    box-sizing: border-box;
    background: #014D98;
    color: #FFFFFF;
    box-shadow: 0 0.12rem 0.4rem rgba(0, 0, 0, 0.22);
}

.media-viewer-bar .viewer-back,
.media-viewer-bar .viewer-new {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    height: 4rem;
    padding: 0 1.4rem;
    border: 1px solid rgba(255, 255, 255, 0.7);
    border-radius: 2rem;
    background: rgba(255, 255, 255, 0.08);
    color: #FFFFFF;
    font-size: 1.8rem;
    font-family: inherit;
    line-height: 1;
    text-decoration: none;
    cursor: pointer;
    white-space: nowrap;
}

.media-viewer-bar .viewer-new {
    height: 2.6rem;
    padding: 0 1rem;
    font-size: 1.05rem;
    margin-left: auto;
}

.media-viewer-bar .viewer-back:hover,
.media-viewer-bar .viewer-new:hover {
    background: #FFFFFF;
    color: #014D98;
    border-color: #FFFFFF;
}

.media-viewer-bar .viewer-title {
    flex: 1 1 auto;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 1.25rem;
    color: #EAF1FA;
}

.media-viewer-frame {
    flex: 1 1 auto;
    min-height: 0;
    width: 100%;
    border: 0;
    background: #FFFFFF;
}

.media-viewer-hint {
    flex: 1 1 auto;
    display: none;
    padding: 3rem 2rem;
    color: #4A5568;
    font-size: 1.05rem;
    line-height: 2;
}

.media-viewer.blocked .media-viewer-frame {
    display: none;
}

.media-viewer.blocked .media-viewer-hint {
    display: block;
}

@media screen and (max-width: 768px) {
    .media-viewer-bar {
        flex-wrap: wrap;
        min-height: 7rem;
        gap: 0.4rem;
        padding-top: 0.4rem;
        padding-bottom: 0.4rem;
    }

    .media-viewer-bar .viewer-back {
        flex: 1 1 100%;
        height: 3.5rem;
        font-size: 1.5rem;
    }

    .media-viewer-bar .viewer-new {
        flex: 1 1 100%;
        height: 2.2rem;
        margin-left: 0;
        font-size: 1.05rem;
    }

    .media-viewer-bar .viewer-title {
        display: none;
    }
}

@media screen and (max-width: 360px) {
    .media-viewer-bar .viewer-back {
        height: 3.2rem;
        font-size: 1.35rem;
    }
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
    font-size: 15px;
    margin-bottom: 0.7rem;
}

/* 列表字号用 px 明确指定：站点根字号随视口缩放，rem 会让字号跟着变小 */
.media-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    padding: 0.72rem 0.2rem;
    border-bottom: 0.06rem dashed #E3E8EF;
    font-size: 19px;
    line-height: 1.75;
}

.media-list .dot {
    flex: 0 0 auto;
    width: 0.5rem;
    height: 0.5rem;
    margin-top: 0.85rem;
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
    padding: 0 0.45rem;
    border: 1px solid #C8D2DE;
    border-radius: 0.2rem;
    color: #7A8798;
    font-size: 14px;
    line-height: 1.6;
    vertical-align: 0.15rem;
    white-space: nowrap;
}

.media-list .meta {
    flex: 0 0 auto;
    color: #6B7A8D;
    font-size: 15px;
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
    /* 字号放大后卡片定高在手机上会显得太挤，改成按视口高度收缩。
       这里直接用 px，不用 rem / vh 混算：站点根字号会随视口缩放，
       rem 换算出来的高度反而比 60rem 还大 */
    .media-card {
        height: 520px;
    }

    .media-list li {
        font-size: 17px;
    }

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

/* 左侧「境内外媒体报道」栏目已去掉，卡片列改成整行宽，
   否则长标题会被挤成两行、类别标签也被顶到下一行 */
.media-row > .layui-col-md9 {
    width: 100%;
}

/* 禁止内嵌的链接保持新窗口打开，这类链接不给"可点开"的手型提示 */
.media-list .title.embeddable {
    cursor: pointer;
}

/* 打印时不要带上整屏阅读层 */
@media print {
    .media-viewer {
        display: none !important;
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

        var first = item.sources[0];
        var link = document.createElement('a');
        link.className = 'title';
        link.href = first.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = item.title;
        if (window.MEDIA_EMBEDDABLE[first.url]) {
            link.setAttribute('data-url', first.url);
            link.setAttribute('data-site', first.site || '');
            link.className = 'title embeddable';
        }
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

    var viewer = document.getElementById('media-viewer');
    var viewerFrame = document.getElementById('media-viewer-frame');
    var viewerNew = document.getElementById('media-viewer-new');
    var viewerTitle = document.getElementById('media-viewer-source');
    var viewerHintLink = document.getElementById('media-viewer-hint-link');

    function closeViewer() {
        viewer.classList.remove('open', 'blocked');
        viewerFrame.removeAttribute('src');
        document.body.style.overflow = '';
        if (window.history && window.history.replaceState) {
            window.history.replaceState(null, '', window.location.pathname + window.location.search);
        }
    }

    function openViewer(url, site) {
        var embeddable = !!window.MEDIA_EMBEDDABLE[url];
        viewerTitle.textContent = site || '媒体报道';
        viewerNew.setAttribute('data-url', url);
        viewerHintLink.href = url;
        if (embeddable) {
            viewer.classList.remove('blocked');
            viewerFrame.setAttribute('src', url);
        } else {
            viewer.classList.add('blocked');
            viewerFrame.removeAttribute('src');
        }
        viewer.classList.add('open');
        document.body.style.overflow = 'hidden';
        if (window.history && window.history.replaceState) {
            window.history.replaceState(null, '', '#view=' + encodeURIComponent(url));
        }
    }

    // 点标题：能内嵌的在页内整屏打开并带返回条，不能内嵌的才新窗口打开
    function bindMediaLinks() {
        listNode.addEventListener('click', function (event) {
            var link = event.target.closest('a.embeddable');
            if (!link) return;
            event.preventDefault();
            openViewer(link.getAttribute('data-url'), link.getAttribute('data-site'));
        });
        document.getElementById('media-viewer-back').addEventListener('click', closeViewer);
        viewerNew.addEventListener('click', function () {
            var url = viewerNew.getAttribute('data-url');
            if (url) window.open(url, '_blank', 'noopener');
        });
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && viewer.classList.contains('open')) closeViewer();
        });
        // 支持 #view=链接 直达
        var match = /^#view=(.+)$/.exec(window.location.hash || '');
        if (match) openViewer(decodeURIComponent(match[1]), '');
    }

    bindMediaLinks();
    render();
})();
"""


def render_items(entries, verified, replacements):
    """把条目整理成页面脚本使用的数据。

    verified:     链接核对结果（tools/verify_media_links.py 的产物），
                  用于给原表没印标题的条目补上联网核到的真实标题。
    replacements: 失效链接的替换结果（tools/fix_dead_links.py 的产物），
                  把打不开的地址换成找回的正确地址。
    """
    items = []
    for entry in entries:
        sources = [
            {"site": source["媒体"], "url": source["链接"], "date": source["日期"]}
            for source in entry["来源"]
            if source["链接"]
        ]
        if not sources:
            continue
        live_titles = []
        for source in sources:
            info = verified.get(source["url"]) or {}
            if info.get("标题"):
                live_titles.append(info["标题"])
        title = entry["标题"] or (live_titles[0] if live_titles else (sources[0]["site"] or "查看原文"))
        # 有明确核对结果时以核对结果为准，避免出现"标题就是媒体名"
        title = TITLE_OVERRIDES.get(entry["序号"], title)

        for source in sources:
            # 失效链接已在 tools/fix_dead_links.py 里逐个找回正确地址（或按标题搜索入口），
            # 这里统一替换成可用地址，页面上所有条目都是正常可点的链接
            fix = replacements.get(source["url"]) or {}
            if fix.get("替换"):
                source["url"] = fix["替换"]
            elif fix.get("备用搜索"):
                source["url"] = fix["备用搜索"]

        items.append(
            {
                "index": entry["序号"],
                "title": title,
                "category": entry["类别"] or "其他",
                "date": entry["日期"],
                "sources": sources,
            }
        )
    # 按原表序号排列，顺序与「媒体报道.pdf」里的表格完全一致
    items.sort(key=lambda item: item["index"])
    return items


def load_embeddable():
    """读取 tools/check_embed.py 的检测结果，返回 {链接: True}。

    没有做过检测时返回空表，页面会退化成"全部新窗口打开"，不会出现空白 iframe。
    """
    if not EMBED_DATA.exists():
        return {}
    checked = json.loads(EMBED_DATA.read_text(encoding="utf-8"))
    return {url: True for url, info in checked.items() if info.get("可内嵌")}


def build_page(items, embeddable):
    payload = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    embed_payload = json.dumps(embeddable, ensure_ascii=False, separators=(",", ":"))

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
            <div class="main3-body layui-row media-row">
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
<div class="media-viewer" id="media-viewer">
    <div class="media-viewer-bar">
        <button type="button" class="viewer-back" id="media-viewer-back">← 返回媒体报道</button>
        <span class="viewer-title" id="media-viewer-source"></span>
        <button type="button" class="viewer-new" id="media-viewer-new">在新窗口打开</button>
    </div>
    <iframe class="media-viewer-frame" id="media-viewer-frame" title="报道原文" allowfullscreen></iframe>
    <div class="media-viewer-hint">
        该媒体站点不允许在网页内直接显示，请点右上角「在新窗口打开」查看原文：<br>
        <a id="media-viewer-hint-link" href="#" target="_blank" rel="noopener noreferrer"></a>
    </div>
</div>
<script type="text/javascript">
window.MEDIA_DATA = %(payload)s;
window.MEDIA_EMBEDDABLE = %(embeddable)s;
</script>
<script type="text/javascript">
%(script)s
</script>
</body>
</html>
""" % {
        "style": STYLE.strip(),
        "payload": payload,
        "embeddable": embed_payload,
        "script": SCRIPT.strip() % {"page_size": PAGE_SIZE},
    }


def load_verified():
    """读取 tools/verify_media_links.py 的链接核对结果；没跑过就返回空表。"""
    if not VERIFY_DATA.exists():
        return {}
    return json.loads(VERIFY_DATA.read_text(encoding="utf-8"))


def load_replacements():
    """读取 tools/fix_dead_links.py 的链接替换结果；没跑过就返回空表。"""
    if not REPLACE_DATA.exists():
        return {}
    return json.loads(REPLACE_DATA.read_text(encoding="utf-8"))


# 少数条目原表未印标题、网页标题也取不到（报刊电子版接口、客户端分享页），
# 这里按页面正文/纸媒版次核对后补齐，避免页面上只显示"广西日报""中华网"这种媒体名
TITLE_OVERRIDES = {
    29: "广西职业院校创新创业教育联盟在南宁成立",
    30: "广西职业院校创新创业教育联盟成立",
    34: "专创赋能，“蚕燃一新”助推广西桑蚕产业转型升级",
    67: "广西职业院校创新创业教育联盟2023年度工作会议在邕召开",
    91: "校园创业新星王俊杰：从“梦想家”到“创新创业引领者”",
    95: "广西职业院校创新创业教育联盟2024年度工作会议召开",
    97: "广西职业院校创新创业教育联盟2024年度工作会议在南宁召开",
    99: "“碳”见未来，引领绿色建材高质量发展",
    162: "“龙狮少年”的追光之路",
}


def main():
    entries = json.loads(DATA.read_text(encoding="utf-8"))
    verified = load_verified()
    replacements = load_replacements()
    items = render_items(entries, verified, replacements)
    embeddable = load_embeddable()
    page = build_page(items, embeddable)
    OUT.write_text(page, encoding="utf-8")

    total_sources = sum(len(item["sources"]) for item in items)
    original = {source["链接"] for entry in entries for source in entry["来源"] if source.get("链接")}
    fixed = sum(1 for item in items for source in item["sources"] if source["url"] not in original)
    filled = sum(1 for item in items if verified.get(item["sources"][0]["url"], {}).get("标题") and item["title"])
    print("条目=%d 链接=%d 可内嵌=%d 已换用替换地址=%d 已用联网标题=%d 已写入 %s" % (
        len(items), total_sources, len(embeddable), fixed, filled, OUT.name))
    print("序号区间=%s ~ %s" % (items[0]["index"], items[-1]["index"]))
    print("日期区间=%s ~ %s" % (items[0]["date"], items[-1]["date"]))


if __name__ == "__main__":
    main()
