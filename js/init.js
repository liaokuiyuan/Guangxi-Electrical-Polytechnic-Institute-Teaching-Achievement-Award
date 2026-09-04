/**
 * 全局初始化脚本
 * - 响应式字体缩放
 * - 动态注入 responsive.css
 * - 移动端导航横向滚动
 * - 视口修正
 */
var screenConfig = {
    oWindowWidth: 1280,
    oFontSize: 10,
    windowWidth: 0,
    fontSize: 0,
};

(function initAll() {
    injectResponsiveCSS();
    injectMenuStyleFix();
    fixViewportMeta();
    fontInit();
    initNavScroll();
    bindResizeEvents();
})();

document.addEventListener('DOMContentLoaded', function () {
    initProjectSite();
    initNavScroll();
});

/* ========================================
   全站项目标题、成果申报菜单与 PDF 版式
   ======================================== */
function initProjectSite() {
    var projectTitle = '高职创新创业教育生态共同体的构建与实践';
    var currentPage = (window.location.pathname.split('/').pop() || 'index.html').toLowerCase();

    updateProjectTitle(projectTitle);
    buildApplicationNavigation(currentPage);
    buildPdfLayout(currentPage);
    normalizeAwardLinks();
}

function updateProjectTitle(projectTitle) {
    var oldProjectTitle = '职教出海新高度：职业院校境外办学2.0的创新与实践';
    if (document.title.indexOf(oldProjectTitle) !== -1) {
        document.title = document.title.replace(oldProjectTitle, projectTitle);
    } else if (document.title !== projectTitle && document.title.indexOf(projectTitle) === -1) {
        document.title = projectTitle;
    }

    ['keywords', 'description'].forEach(function (name) {
        var meta = document.querySelector('meta[name="' + name + '"]');
        if (meta) meta.setAttribute('content', projectTitle);
    });

    var titleKicker = document.querySelector('.header-title-kicker');
    if (titleKicker) {
        titleKicker.textContent = '北引·东联·西融';
    }

    var titleImage = document.querySelector('.header-title-img');
    if (!titleImage) return;

    var titleText = document.createElement('div');
    titleText.className = 'header-title-text';
    titleText.setAttribute('role', 'heading');
    titleText.setAttribute('aria-level', '1');
    titleText.innerHTML =
        '<div class="header-title-kicker">北引·东联·西融</div>' +
        '<div class="header-project-title">' + projectTitle + '</div>';
    titleImage.parentNode.replaceChild(titleText, titleImage);
}

function buildApplicationNavigation(currentPage) {
    var nav = document.querySelector('.main2-body');
    if (!nav) return;

    var applicationLink = nav.querySelector('a[href="shenbaoshu.html"]');
    var reportLink = nav.querySelector('a[href="report.html"]');
    if (!applicationLink || !reportLink) return;

    var applicationItem = applicationLink.parentNode;
    var reportItem = reportLink.parentNode;
    applicationItem.classList.add('nav-has-submenu');
    applicationLink.textContent = '成果申报';
    applicationLink.setAttribute('href', '#');
    applicationLink.setAttribute('aria-haspopup', 'true');
    applicationLink.setAttribute('aria-expanded', 'false');

    var submenu = document.createElement('ul');
    submenu.className = 'nav-submenu';
    submenu.innerHTML =
        '<li><a href="shenbaoshu.html">申报书</a></li>' +
        '<li><a href="report.html">成果报告</a></li>';
    applicationItem.appendChild(submenu);

    if (currentPage === 'shenbaoshu.html' || currentPage === 'report.html') {
        applicationItem.classList.add('selected');
        reportItem.classList.remove('selected');
        var currentSubLink = submenu.querySelector('a[href="' + currentPage + '"]');
        if (currentSubLink) currentSubLink.classList.add('current');
    }
    reportItem.parentNode.removeChild(reportItem);

    applicationLink.addEventListener('click', function (event) {
        event.preventDefault();
        var isOpen = applicationItem.classList.toggle('submenu-open');
        applicationLink.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        if (window.innerWidth <= 992) {
            submenu.style.top = nav.getBoundingClientRect().bottom + 'px';
        } else {
            submenu.style.top = '';
        }
    });

    document.addEventListener('click', function (event) {
        if (!applicationItem.contains(event.target)) {
            applicationItem.classList.remove('submenu-open');
            applicationLink.setAttribute('aria-expanded', 'false');
        }
    });
}

function buildPdfLayout(currentPage) {
    var pdf = document.querySelector('.wp_pdf_player');
    var isApplicationPage = currentPage === 'shenbaoshu.html' || currentPage === 'report.html';
    if (!pdf && !isApplicationPage) return;

    var main = document.querySelector('.main3');
    var titleRow = main && main.querySelector('.main-list-title');
    var body = main && main.querySelector('.main3-body');
    if (!main || !titleRow || !body) return;

    main.classList.add('pdf-page');
    var pageTitle = titleRow.querySelector('.main-list-title-1');
    var breadcrumb = titleRow.querySelector('.main-list-title-2');
    var sidebarColumn = body.querySelector('.layui-col-md3');
    var contentColumn = body.querySelector('.layui-col-md9');
    var subnav = document.createElement('div');
    subnav.className = 'pdf-subnav';
    subnav.setAttribute('aria-label', '本栏目二级菜单');

    if (isApplicationPage) {
        if (pageTitle) pageTitle.textContent = '成果申报';
        subnav.innerHTML =
            '<a href="shenbaoshu.html"' + (currentPage === 'shenbaoshu.html' ? ' class="active"' : '') + '>申报书</a>' +
            '<a href="report.html"' + (currentPage === 'report.html' ? ' class="active"' : '') + '>成果报告</a>';
    } else if (sidebarColumn) {
        var sourceLinks = sidebarColumn.querySelectorAll('.layui-menu a[href]');
        var panelItems = sidebarColumn.querySelectorAll('.sidebar-item[data-index]');
        if (panelItems.length) {
            Array.prototype.forEach.call(panelItems, function (sourceItem) {
                var button = document.createElement('button');
                var sourceTitle = sourceItem.querySelector('.layui-menu-body-title');
                var panelIndex = sourceItem.getAttribute('data-index');
                button.type = 'button';
                button.textContent = sourceTitle ? sourceTitle.textContent.trim() : '材料' + (Number(panelIndex) + 1);
                button.setAttribute('data-panel-index', panelIndex);
                if (sourceItem.classList.contains('active')) button.className = 'active';
                button.addEventListener('click', function () {
                    Array.prototype.forEach.call(body.querySelectorAll('.pdf-panel'), function (panel) {
                        panel.classList.remove('active');
                    });
                    Array.prototype.forEach.call(sidebarColumn.querySelectorAll('.sidebar-item'), function (item) {
                        item.classList.remove('active');
                    });
                    Array.prototype.forEach.call(subnav.querySelectorAll('button'), function (item) {
                        item.classList.remove('active');
                    });
                    var targetPanel = body.querySelector('#pdf-' + panelIndex);
                    if (targetPanel) targetPanel.classList.add('active');
                    sourceItem.classList.add('active');
                    button.classList.add('active');
                });
                subnav.appendChild(button);
            });
        } else if (sourceLinks.length) {
            Array.prototype.forEach.call(sourceLinks, function (sourceLink) {
                var link = document.createElement('a');
                link.href = sourceLink.getAttribute('href');
                link.textContent = sourceLink.textContent.trim();
                if (link.href === window.location.href) link.className = 'active';
                subnav.appendChild(link);
            });
        } else {
            var sourceTitle = sidebarColumn.querySelector('.layui-menu-body-title');
            if (sourceTitle) {
                var label = document.createElement('span');
                label.className = 'active';
                label.textContent = sourceTitle.textContent.trim();
                subnav.appendChild(label);
            }
        }
    }

    if (subnav.children.length) {
        titleRow.insertBefore(subnav, breadcrumb || null);
    }
    if (sidebarColumn) sidebarColumn.classList.add('pdf-sidebar-source');
    if (contentColumn) contentColumn.classList.add('pdf-content-column');
}

function normalizeAwardLinks() {
    var awardSection = document.querySelector('.main6');
    if (!awardSection) return;
    Array.prototype.forEach.call(awardSection.querySelectorAll('a'), function (link) {
        link.setAttribute('href', 'award.html');
    });
}

/* ========================================
   1. 动态注入 responsive.css
   所有页面只需引入 init.js 即可获得移动端适配
   ======================================== */
function injectResponsiveCSS() {
    if (document.querySelector('link[href*="responsive.css"]')) return;
    var link = document.createElement('link');
    link.type = 'text/css';
    link.rel = 'stylesheet';
    link.href = './css/responsive.css';
    document.head.appendChild(link);
}

/* ========================================
   2. 侧边栏按钮间距修正
   ======================================== */
function injectMenuStyleFix() {
    var style = document.createElement('style');
    style.textContent = '.layui-menu .layui-menu-item-group>.layui-menu-body-title{padding-right:28px!important}.layui-menu .layui-menu-body-title>.layui-icon-right{right:6px!important}';
    document.head.appendChild(style);
}

/* ========================================
   3. 修复 viewport meta，允许移动端缩放
   ======================================== */
function fixViewportMeta() {
    var meta = document.querySelector('meta[name="viewport"]');
    if (meta) {
        meta.setAttribute('content',
            'width=device-width, initial-scale=1.0, maximum-scale=5.0, minimum-scale=0.5, user-scalable=yes');
    }
}

/* ========================================
   3. 响应式字体缩放（优化移动端）
   ======================================== */
function fontInit() {
    var windowWidth = layui.$(window).width();
    screenConfig.windowWidth = windowWidth;
    screenConfig.windowHeight = layui.$(window).height();

    var oWindowWidth = screenConfig.oWindowWidth;
    var oFontSize = screenConfig.oFontSize;

    // 基础计算：按 1280px = 10px 等比缩放
    var fontSize = oFontSize * windowWidth / oWindowWidth;

    // 移动端 (< 768px): 使用 vw 方案，保证可读性
    // 375px → ~13px, 414px → ~14px, 768px → ~12px
    if (windowWidth < 768) {
        fontSize = Math.max(13, windowWidth / 28.8);  // 375/28.8≈13, 414/28.8≈14.4
        fontSize = Math.min(fontSize, 15);
    }
    // 平板 (768-992px): 适中大小
    else if (windowWidth < 992) {
        fontSize = Math.max(10, windowWidth / 76.8);  // 768/76.8=10, 992/76.8≈12.9
        fontSize = Math.min(fontSize, 13);
    }
    // 桌面 (≥ 993px): 原始算法
    else {
        var maxFontSize = 1200 / 90;
        var minFontSize = 900 / 90;
        if (fontSize > maxFontSize) fontSize = maxFontSize;
        else if (fontSize < minFontSize) fontSize = minFontSize;
    }

    screenConfig.fontSize = fontSize;
    layui.$('html').css({
        'font-size': fontSize + 'px',
    });
}

function px(number) {
    return number * screenConfig.windowWidth / screenConfig.oWindowWidth;
}

/* ========================================
   4. 移动端导航栏 — 自动滚动到当前选中项
   ======================================== */
function initNavScroll() {
    var navBody = document.querySelector('.main2-body');
    if (!navBody) return;

    var selected = navBody.querySelector('li.selected');
    if (selected) {
        // 延迟执行确保 CSS 已渲染
        setTimeout(function () {
            var navLeft = navBody.getBoundingClientRect().left;
            var itemLeft = selected.getBoundingClientRect().left;
            var scrollTo = navBody.scrollLeft + (itemLeft - navLeft) - 10;
            if (scrollTo > 0) {
                navBody.scrollTo({ left: scrollTo, behavior: 'smooth' });
            }
        }, 300);
    }
}

/* ========================================
   5. resize 事件绑定（字体 + 菜单状态）
   ======================================== */
function bindResizeEvents() {
    var resizeTimer;
    layui.$(window).on('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            fontInit();
        }, 200);
    });
}

/* ========================================
   6. 页面切换过渡
   ======================================== */
(function initPageTransition() {
    document.addEventListener('click', function (e) {
        var link = e.target.closest('a');
        if (!link) return;
        var href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('javascript') || link.target === '_blank') return;
        // 只处理同站内 .html 链接
        if (!href.endsWith('.html') && href.indexOf('.') !== -1 && !href.endsWith('.pdf')) return;
        if (href.indexOf('://') !== -1) return;

        e.preventDefault();
        document.body.classList.add('page-out');
        setTimeout(function () {
            window.location.href = href;
        }, 350);
    });
})();

/* ========================================
   7. IE 版本检测（保留兼容）
   ======================================== */
function IEVersion() {
    var userAgent = navigator.userAgent;
    var isIE = userAgent.indexOf("compatible") > -1 && userAgent.indexOf("MSIE") > -1;
    var isEdge = userAgent.indexOf("Edge") > -1 && !isIE;
    var isIE11 = userAgent.indexOf('Trident') > -1 && userAgent.indexOf("rv:11.0") > -1;
    if (isIE) {
        var reIE = new RegExp("MSIE (\\d+\\.\\d+);");
        reIE.test(userAgent);
        var fIEVersion = parseFloat(RegExp["$1"]);
        if (fIEVersion == 7) { return 7; }
        else if (fIEVersion == 8) { return 8; }
        else if (fIEVersion == 9) { return 9; }
        else if (fIEVersion == 10) { return 10; }
        else { return 6; }
    } else if (isEdge) {
        return 'edge';
    } else if (isIE11) {
        return 11;
    } else {
        return -1;
    }
}
