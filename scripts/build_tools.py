"""
build_tools.py -- Reads data/tools_kb/*.json and generates tool detail pages.
Run: python build_tools.py
"""
import json, re
from pathlib import Path
from urllib.parse import urlparse

ROOT_DIR  = Path(__file__).parent.parent
SITE_DIR  = ROOT_DIR / "site"
KB_DIR    = ROOT_DIR / "data" / "tools_kb"
TOOLS_DIR = SITE_DIR / "tools"
TOOLS_JSON = SITE_DIR / "tools" / "index.json"
BASE_URL  = "https://2193824842-spec.github.io/ai-pulse"


def load_tools_index():
    with open(TOOLS_JSON, encoding="utf-8") as f:
        return json.load(f)


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def get_domain(url, favicon_domain=None):
    if favicon_domain:
        return favicon_domain
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


def pricing_class(p):
    return {"free": "free", "freemium": "freemium", "paid": "paid"}.get(p, "")


def pricing_label(p):
    return {"free": "Free", "freemium": "Freemium", "paid": "Paid"}.get(p, "")


def render_similar(tool_data, all_tools, base="/ai-pulse/tools/"):
    slug = tool_data.get("slug", "")
    cat  = tool_data.get("category", "")
    alts = [a.lower() for a in tool_data.get("alternatives", [])]
    similar = []
    for t in all_tools:
        if slugify(t["name"]) == slug:
            continue
        if t["name"].lower() in alts or t.get("category") == cat:
            similar.append(t)
        if len(similar) >= 6:
            break
    rows = []
    for t in similar[:6]:
        d  = get_domain(t["url"])
        ts = slugify(t["name"])
        pc = pricing_class(t.get("pricing", ""))
        pl = pricing_label(t.get("pricing", ""))
        n  = t["name"]
        tc = t.get("category", "")
        co = t.get("company", "")
        rows.append(
            f'          <a href="{base}{ts}.html" class="similar-tool-item">\n'
            f'            <img src="https://www.google.com/s2/favicons?domain={d}&sz=64" alt="{n}" class="similar-tool-logo" />\n'
            f'            <div class="similar-tool-info">\n'
            f'              <div class="similar-tool-name">{n}</div>\n'
            f'              <div class="similar-tool-cat">{tc} &middot; {co}</div>\n'
            f'            </div>\n'
            f'            <span class="similar-pricing {pc}">{pl}</span>\n'
            f'          </a>'
        )
    return "\n".join(rows)


def render_pricing(plans, zh_plans=None, lang="en"):
    rows = []
    for i, p in enumerate(plans):
        if lang == "zh" and zh_plans and i < len(zh_plans):
            highlights = zh_plans[i].get("zh_highlights") or p.get("highlights", [])
        else:
            highlights = p.get("highlights", [])
        h = " &middot; ".join(highlights)
        rows.append(
            f'              <tr>\n'
            f'                <td><span class="plan-name">{p["name"]}</span></td>\n'
            f'                <td><span class="plan-price">{p["price"]}</span></td>\n'
            f'                <td><span class="plan-highlights">{h}</span></td>\n'
            f'              </tr>'
        )
    return "\n".join(rows)


def render_features(features):
    return "\n".join(
        f'            <div class="feature-item">{f}</div>' for f in features
    )


def render_list(items):
    return "\n".join(f"                <li>{i}</li>" for i in items)


def render_tags(tags, zh_tags=None, lang="en"):
    rows = []
    base = "/ai-pulse/zh/tools.html" if lang == "zh" else "/ai-pulse/tools.html"
    labels = zh_tags if (lang == "zh" and zh_tags and len(zh_tags) == len(tags)) else tags
    for tag, label in zip(tags, labels):
        ts = tag.lower().replace(" ", "-").replace("/", "-")
        rows.append(f'            <a href="{base}?q={ts}" class="best-for-tag">{label}</a>')
    return "\n".join(rows)


def render_related(category, lang="en"):
    if lang == "zh":
        index_path = SITE_DIR / "zh" / "posts" / "index.json"
        post_base  = "/ai-pulse/zh/posts/"
    else:
        index_path = SITE_DIR / "posts" / "index.json"
        post_base  = "/ai-pulse/posts/"
    try:
        with open(index_path, encoding="utf-8") as f:
            posts = json.load(f)
    except Exception:
        return ""
    cat_tags = {
        "AI Coding":      ["code-generation", "ai-tools"],
        "AI Writing":     ["writing", "ai-tools", "generative-ai"],
        "AI Image":       ["image", "generative-ai"],
        "AI Video":       ["video", "generative-ai"],
        "AI Audio":       ["audio", "voice"],
        "AI Search":      ["search", "ai-research"],
        "AI Design":      ["design", "ai-tools"],
        "AI Productivity":["productivity", "ai-tools"],
        "AI Developer":   ["api", "ai-tools", "code-generation"],
    }
    target = cat_tags.get(category, ["ai-tools"])
    scored = []
    for p in posts:
        ptags = [t.lower() for t in p.get("tags", [])]
        score = sum(1 for t in target if t in ptags)
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: -x[0])
    related = [p for _, p in scored[:3]] or posts[:3]
    rows = []
    for p in related:
        exc = p.get("excerpt", "")[:120] + "..."
        rows.append(
            f'            <a href="{post_base}{p["slug"]}.html" class="related-card">\n'
            f'              <h4>{p.get("title", "")}</h4>\n'
            f'              <p>{exc}</p>\n'
            f'            </a>'
        )
    return "\n".join(rows)


def render_stats(tool_data, lang="en"):
    is_zh  = lang == "zh"
    pop    = tool_data.get("popularity", 0)
    stars  = "&#9733;" * round(pop / 20) + "&#9734;" * (5 - round(pop / 20))
    plans  = tool_data.get("pricing", {}).get("plans", [])
    start  = plans[0]["price"] if plans else "&#8212;"
    company = tool_data.get("company", "&#8212;")
    lbl_pop   = "热度" if is_zh else "Popularity"
    lbl_price = "起始价格" if is_zh else "Starting Price"
    lbl_dev   = "开发商" if is_zh else "Developer"
    return (
        f'          <div class="stat-item">\n'
        f'            <div class="stat-value" style="font-size:16px;">{stars}</div>\n'
        f'            <div class="stat-label">{lbl_pop}</div>\n'
        f'          </div>\n'
        f'          <div class="stat-item">\n'
        f'            <div class="stat-value" style="font-size:13px;">{start}</div>\n'
        f'            <div class="stat-label">{lbl_price}</div>\n'
        f'          </div>\n'
        f'          <div class="stat-item" style="grid-column:span 2;">\n'
        f'            <div class="stat-value" style="font-size:14px;">{company}</div>\n'
        f'            <div class="stat-label">{lbl_dev}</div>\n'
        f'          </div>'
    )


CSS = """
    .tool-detail-wrap{display:grid;grid-template-columns:1fr 300px;gap:32px;margin:32px 0 64px;align-items:start}
    .breadcrumb{font-size:13px;color:var(--text-muted);margin:24px 0 0;display:flex;align-items:center;gap:6px}
    .breadcrumb a{color:var(--text-muted);text-decoration:none}
    .breadcrumb a:hover{color:var(--accent)}
    .tool-hero{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:28px 32px;margin-bottom:24px}
    .tool-hero-top{display:flex;align-items:flex-start;gap:20px}
    .tool-hero-logo{width:72px;height:72px;border-radius:16px;border:1px solid var(--border);object-fit:contain;flex-shrink:0;background:#fff;padding:4px}
    .tool-hero-info{flex:1;min-width:0}
    .tool-hero-name{font-size:26px;font-weight:700;color:var(--text);margin-bottom:4px}
    .tool-hero-company{font-size:13px;color:var(--text-muted);margin-bottom:8px}
    .tool-hero-tagline{font-size:15px;color:var(--text-secondary);line-height:1.5}
    .tool-hero-actions{display:flex;align-items:center;gap:12px;margin-top:20px;flex-wrap:wrap}
    .btn-visit{display:inline-flex;align-items:center;gap:8px;background:var(--gradient);color:#fff;font-size:15px;font-weight:600;padding:10px 24px;border-radius:8px;text-decoration:none;transition:opacity .2s}
    .btn-visit:hover{opacity:.88}
    .btn-visit svg{width:16px;height:16px}
    .tool-meta-tags{display:flex;gap:8px;flex-wrap:wrap}
    .meta-tag{font-size:12px;padding:4px 10px;border-radius:20px;border:1px solid var(--border);color:var(--text-secondary);background:var(--bg)}
    .meta-tag.pricing-freemium{border-color:#f59e0b;color:#b45309;background:#fffbeb}
    .meta-tag.pricing-free{border-color:#10b981;color:#065f46;background:#ecfdf5}
    .meta-tag.pricing-paid{border-color:#6366f1;color:#4338ca;background:#eef2ff}
    .detail-section{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:24px 28px;margin-bottom:20px}
    .detail-section h2{font-size:17px;font-weight:700;color:var(--text);margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border)}
    .detail-section p{font-size:14px;color:var(--text-secondary);line-height:1.7}
    .features-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    .feature-item{display:flex;align-items:flex-start;gap:10px;font-size:13.5px;color:var(--text-secondary);line-height:1.5}
    .feature-item::before{content:"\\2726";color:var(--accent);font-size:11px;margin-top:3px;flex-shrink:0}
    .pricing-table{width:100%;border-collapse:collapse;font-size:13.5px}
    .pricing-table th{text-align:left;padding:10px 14px;background:var(--bg);color:var(--text-secondary);font-weight:600;border-bottom:1px solid var(--border)}
    .pricing-table td{padding:10px 14px;border-bottom:1px solid var(--border);color:var(--text-secondary);vertical-align:top}
    .pricing-table tr:last-child td{border-bottom:none}
    .pricing-table tr:hover td{background:var(--bg)}
    .plan-name{font-weight:600;color:var(--text)}
    .plan-price{font-weight:700;color:var(--accent);white-space:nowrap}
    .plan-highlights{color:var(--text-muted);font-size:12.5px;line-height:1.6}
    .pros-cons-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
    .pros-box,.cons-box{border-radius:10px;padding:16px 18px}
    .pros-box{background:#f0fdf4;border:1px solid #bbf7d0}
    .cons-box{background:#fff7f7;border:1px solid #fecaca}
    .pros-box h3{color:#15803d;font-size:14px;font-weight:700;margin-bottom:12px}
    .cons-box h3{color:#dc2626;font-size:14px;font-weight:700;margin-bottom:12px}
    .pros-cons-list{list-style:none;display:flex;flex-direction:column;gap:8px}
    .pros-cons-list li{font-size:13px;line-height:1.5;display:flex;align-items:flex-start;gap:8px}
    .pros-box li{color:#166534}
    .cons-box li{color:#991b1b}
    .pros-box li::before{content:"\\2713";font-weight:700;flex-shrink:0}
    .cons-box li::before{content:"\\2717";font-weight:700;flex-shrink:0}
    .best-for-list{display:flex;flex-wrap:wrap;gap:8px}
    .best-for-tag{font-size:13px;padding:6px 14px;border-radius:20px;background:var(--accent-bg);color:var(--accent);border:1px solid rgba(99,102,241,.2);text-decoration:none;transition:background .15s}
    .best-for-tag:hover{background:rgba(99,102,241,.15)}
    .tool-sidebar{position:sticky;top:80px}
    .sidebar-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px;margin-bottom:20px}
    .sidebar-card h3{font-size:14px;font-weight:700;color:var(--text);margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--border)}
    .similar-tool-item{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border);text-decoration:none;color:inherit;transition:opacity .15s}
    .similar-tool-item:last-child{border-bottom:none;padding-bottom:0}
    .similar-tool-item:hover{opacity:.75}
    .similar-tool-logo{width:36px;height:36px;border-radius:8px;border:1px solid var(--border);object-fit:contain;flex-shrink:0;background:#fff;padding:2px}
    .similar-tool-info{flex:1;min-width:0}
    .similar-tool-name{font-size:13.5px;font-weight:600;color:var(--text)}
    .similar-tool-cat{font-size:11.5px;color:var(--text-muted);margin-top:1px}
    .similar-pricing{font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600;flex-shrink:0}
    .similar-pricing.freemium{background:#fffbeb;color:#b45309}
    .similar-pricing.free{background:#ecfdf5;color:#065f46}
    .similar-pricing.paid{background:#eef2ff;color:#4338ca}
    .quick-stats{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    .stat-item{text-align:center;padding:12px 8px;background:var(--bg);border-radius:8px}
    .stat-value{font-size:16px;font-weight:700;color:var(--accent);word-break:break-all;line-height:1.3}
    .stat-label{font-size:11px;color:var(--text-muted);margin-top:2px}
    @media(max-width:900px){.tool-detail-wrap{grid-template-columns:1fr}.tool-sidebar{position:static}.features-grid{grid-template-columns:1fr}.pros-cons-grid{grid-template-columns:1fr}}
    @media(max-width:600px){.tool-hero{padding:20px}.tool-hero-name{font-size:22px}.detail-section{padding:18px 20px}}
"""


def _zh(tool_data, key):
    """Return zh_ field if available, else fall back to English field."""
    return tool_data.get(f"zh_{key}") or tool_data.get(key)


def generate_page(tool_data, all_tools, lang="en"):
    is_zh   = lang == "zh"
    slug    = tool_data["slug"]
    name    = tool_data["name"]
    company = tool_data.get("company", "")
    url     = tool_data.get("url", "#")
    cat     = tool_data.get("category", "")
    tagline = _zh(tool_data, "tagline") if is_zh else tool_data.get("tagline", "")
    desc    = _zh(tool_data, "description") if is_zh else tool_data.get("description", "")
    feats   = _zh(tool_data, "features") if is_zh else tool_data.get("features", [])
    pricing = tool_data.get("pricing", {})
    plans   = pricing.get("plans", [])
    zh_plans = tool_data.get("zh_plans", [])
    pm      = pricing.get("model", "freemium")
    pros    = _zh(tool_data, "pros") if is_zh else tool_data.get("pros", [])
    cons    = _zh(tool_data, "cons") if is_zh else tool_data.get("cons", [])
    tags    = tool_data.get("tags", tool_data.get("best_for", []))
    zh_tags = tool_data.get("zh_tags", [])
    domain  = get_domain(url, tool_data.get("favicon_domain"))
    pc      = pricing_class(pm)
    pl      = pricing_label(pm)
    first   = name[0] if name else "?"
    meta    = f"{name} by {company}: {tagline}. Features, pricing, pros & cons, and alternatives."

    if is_zh:
        html_lang   = "zh"
        css_path    = "../../assets/css/style.css?v=3"
        canonical   = f'{BASE_URL}/zh/tools/{slug}.html'
        nav_home    = f'<a href="/ai-pulse/zh/">首页</a>'
        nav_blog    = f'<a href="/ai-pulse/zh/blog.html">博客</a>'
        nav_tools   = f'<a href="/ai-pulse/zh/tools.html" class="active">工具</a>'
        nav_about   = f'<a href="/ai-pulse/zh/about.html">关于</a>'
        lang_sw     = f'<a href="/ai-pulse/tools/{slug}.html" class="lang-link">EN</a><span class="lang-active">&#20013;</span>'
        bc_home     = f'<a href="/ai-pulse/zh/">首页</a>'
        bc_tools    = f'<a href="/ai-pulse/zh/tools.html">工具</a>'
        logo_href   = "/ai-pulse/zh/"
        title_sfx   = f' 评测 2026 &mdash; 功能、定价、优缺点 | AI Pulse'
        visit_btn   = f'访问 {name}'
        what_is     = f'<h2>什么是 {name}？</h2>'
        h_features  = '<h2>核心功能</h2>'
        h_pricing   = '<h2>定价方案</h2>'
        th_plan, th_price, th_get = '<th>方案</th>', '<th>价格</th>', '<th>包含内容</th>'
        h_pros_cons = '<h2>优缺点</h2>'
        h_pros      = '&#128077; 优点'
        h_cons      = '&#128078; 缺点'
        h_tags      = '<h2>相关标签</h2>'
        h_articles  = '<h2>相关文章</h2>'
        h_stats     = '<h3>基本信息</h3>'
        h_similar   = '<h3>相似工具</h3>'
        try_label   = f'试用 {name}'
        visit_site  = '访问官网 &rarr;'
        footer_desc = '深度解读AI领域的最新动态，提供每日资讯、教程和洞察，覆盖人工智能前沿进展。'
        footer_cats = '分类'
        footer_links= '链接'
        ft_home     = f'<a href="/ai-pulse/zh/">首页</a>'
        ft_blog     = f'<a href="/ai-pulse/zh/blog.html">所有文章</a>'
        ft_cat_links = [
            f'<li><a href="/ai-pulse/zh/blog.html?category=Model+Comparison">模型对比</a></li>',
            f'<li><a href="/ai-pulse/zh/blog.html?category=Product+Review">产品评测</a></li>',
            f'<li><a href="/ai-pulse/zh/blog.html?category=Industry+Analysis">行业分析</a></li>',
            f'<li><a href="/ai-pulse/zh/blog.html?category=Tool+Guide">工具指南</a></li>',
            f'<li><a href="/ai-pulse/zh/blog.html?category=Opinion">观点</a></li>',
            f'<li><a href="/ai-pulse/zh/blog.html?category=Research+%26+Innovation">研究与创新</a></li>',
        ]
        similar_base = f'/ai-pulse/zh/tools/'
    else:
        html_lang   = "en"
        css_path    = "../assets/css/style.css?v=3"
        canonical   = f'{BASE_URL}/tools/{slug}.html'
        nav_home    = f'<a href="/ai-pulse/">Home</a>'
        nav_blog    = f'<a href="/ai-pulse/blog.html">Blog</a>'
        nav_tools   = f'<a href="/ai-pulse/tools.html" class="active">Tools</a>'
        nav_about   = f'<a href="/ai-pulse/about.html">About</a>'
        lang_sw     = f'<span class="lang-active">EN</span><a href="/ai-pulse/zh/tools/{slug}.html" class="lang-link">&#20013;</a>'
        bc_home     = f'<a href="/ai-pulse/">Home</a>'
        bc_tools    = f'<a href="/ai-pulse/tools.html">Tools</a>'
        logo_href   = "/ai-pulse/"
        title_sfx   = f' Review 2026 &mdash; Features, Pricing, Pros &amp; Cons | AI Pulse'
        visit_btn   = f'Visit {name}'
        what_is     = f'<h2>What is {name}?</h2>'
        h_features  = '<h2>Core Features</h2>'
        h_pricing   = '<h2>Pricing Plans</h2>'
        th_plan, th_price, th_get = '<th>Plan</th>', '<th>Price</th>', '<th>What you get</th>'
        h_pros_cons = '<h2>Pros &amp; Cons</h2>'
        h_pros      = '&#128077; Pros'
        h_cons      = '&#128078; Cons'
        h_tags      = '<h2>Related Tags</h2>'
        h_articles  = '<h2>Related Articles</h2>'
        h_stats     = '<h3>Quick Stats</h3>'
        h_similar   = '<h3>Similar Tools</h3>'
        try_label   = f'Try {name}'
        visit_site  = 'Visit Site &rarr;'
        footer_desc = 'Cutting through the hype to decode what matters in AI. Daily news, tutorials, and insights covering the latest in artificial intelligence.'
        footer_cats = 'Categories'
        footer_links= 'Links'
        ft_home     = f'<a href="/ai-pulse/">Home</a>'
        ft_blog     = f'<a href="/ai-pulse/blog.html">All Articles</a>'
        ft_cat_links = [
            f'<li><a href="/ai-pulse/blog.html?category=Model+Comparison">Model Comparison</a></li>',
            f'<li><a href="/ai-pulse/blog.html?category=Product+Review">Product Review</a></li>',
            f'<li><a href="/ai-pulse/blog.html?category=Industry+Analysis">Industry Analysis</a></li>',
            f'<li><a href="/ai-pulse/blog.html?category=Tool+Guide">Tool Guide</a></li>',
            f'<li><a href="/ai-pulse/blog.html?category=Opinion">Opinion</a></li>',
            f'<li><a href="/ai-pulse/blog.html?category=Research+%26+Innovation">Research &amp; Innovation</a></li>',
        ]
        similar_base = f'/ai-pulse/tools/'

    svg_fb  = (
        f"data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 "
        f"width=%2272%22 height=%2272%22%3E%3Crect width=%2272%22 height=%2272%22 "
        f"fill=%22%23e0e0e0%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 "
        f"dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2228%22 "
        f"fill=%22%23999%22%3E{first}%3C/text%3E%3C/svg%3E"
    )

    lines = [
        "<!DOCTYPE html>",
        f'<html lang="{html_lang}">',
        "<head>",
        '  <meta charset="UTF-8" />',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />',
        '  <script async src="https://www.googletagmanager.com/gtag/js?id=G-8TZNRYLZ15"></script>',
        "  <script>",
        "    window.dataLayer = window.dataLayer || [];",
        "    function gtag(){dataLayer.push(arguments);}",
        "    gtag('js', new Date());",
        "    gtag('config', 'G-8TZNRYLZ15');",
        "  </script>",
        f'  <title>{name}{title_sfx}</title>',
        f'  <meta name="description" content="{meta}" />',
        f'  <link rel="canonical" href="{canonical}" />',
        '  <link rel="icon" href="/ai-pulse/favicon.svg" type="image/svg+xml" />',
        f'  <link rel="stylesheet" href="{css_path}" />',
        f"  <style>{CSS}  </style>",
        "</head>",
        "<body>",
        "  <header>",
        '    <div class="container header-inner">',
        f'      <a href="{logo_href}" class="logo">AI Pulse</a>',
        "      <nav>",
        f'        {nav_home}',
        f'        {nav_blog}',
        f'        {nav_tools}',
        f'        {nav_about}',
        f'        <span class="lang-switcher">{lang_sw}</span>',
        "      </nav>",
        "    </div>",
        "  </header>",
        "",
        '  <main class="container">',
        '    <nav class="breadcrumb">',
        f'      {bc_home}',
        "      <span>&rsaquo;</span>",
        f'      {bc_tools}',
        "      <span>&rsaquo;</span>",
        f"      <span>{name}</span>",
        "    </nav>",
        "",
        '    <div class="tool-detail-wrap">',
        '      <div class="tool-main">',
        "",
        '        <div class="tool-hero">',
        '          <div class="tool-hero-top">',
        f'            <img src="https://www.google.com/s2/favicons?domain={domain}&sz=128" alt="{name}" class="tool-hero-logo" onerror="this.src=\'{svg_fb}\'" />',
        '            <div class="tool-hero-info">',
        f'              <h1 class="tool-hero-name">{name}</h1>',
        f'              <div class="tool-hero-company">by {company}</div>',
        f'              <p class="tool-hero-tagline">{tagline}</p>',
        "            </div>",
        "          </div>",
        '          <div class="tool-hero-actions">',
        f'            <a href="{url}" target="_blank" rel="noopener noreferrer" class="btn-visit">',
        '              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>',
        f'              {visit_btn}',
        "            </a>",
        '            <div class="tool-meta-tags">',
        f'              <span class="meta-tag pricing-{pc}">{pl}</span>',
        f'              <span class="meta-tag">{cat}</span>',
        f'              <span class="meta-tag">by {company}</span>',
        "            </div>",
        "          </div>",
        "        </div>",
        "",
        '        <div class="detail-section">',
        f'          {what_is}',
        f"          <p>{desc}</p>",
        "        </div>",
        "",
        '        <div class="detail-section">',
        f'          {h_features}',
        '          <div class="features-grid">',
        render_features(feats),
        "          </div>",
        "        </div>",
        "",
        '        <div class="detail-section">',
        f'          {h_pricing}',
        '          <table class="pricing-table">',
        f"            <thead><tr>{th_plan}{th_price}{th_get}</tr></thead>",
        "            <tbody>",
        render_pricing(plans, zh_plans, lang),
        "            </tbody>",
        "          </table>",
        "        </div>",
        "",
        '        <div class="detail-section">',
        f'          {h_pros_cons}',
        '          <div class="pros-cons-grid">',
        '            <div class="pros-box">',
        f"              <h3>{h_pros}</h3>",
        '              <ul class="pros-cons-list">',
        render_list(pros),
        "              </ul>",
        "            </div>",
        '            <div class="cons-box">',
        f"              <h3>{h_cons}</h3>",
        '              <ul class="pros-cons-list">',
        render_list(cons),
        "              </ul>",
        "            </div>",
        "          </div>",
        "        </div>",
        "",
        '        <div class="detail-section">',
        f'          {h_tags}',
        '          <div class="best-for-list">',
        render_tags(tags, zh_tags, lang),
        "          </div>",
        "        </div>",
        "",
        '        <div class="detail-section">',
        f'          {h_articles}',
        '          <div class="related-grid">',
        render_related(cat, lang),
        "          </div>",
        "        </div>",
        "",
        "      </div>",
        "",
        '      <aside class="tool-sidebar">',
        '        <div class="sidebar-card">',
        f'          {h_stats}',
        '          <div class="quick-stats">',
        render_stats(tool_data, lang),
        "          </div>",
        "        </div>",
        "",
        '        <div class="sidebar-card">',
        f'          {h_similar}',
        render_similar(tool_data, all_tools, similar_base),
        "        </div>",
        "",
        '        <div class="sidebar-card" style="text-align:center;background:linear-gradient(135deg,#eef2ff 0%,#f5f3ff 100%);border-color:rgba(99,102,241,.2);">',
        f'          <img src="https://www.google.com/s2/favicons?domain={domain}&sz=64" alt="{name}" style="width:48px;height:48px;border-radius:12px;border:1px solid var(--border);margin-bottom:10px;" />',
        f'          <div style="font-size:14px;font-weight:600;color:var(--text);margin-bottom:6px;">{try_label}</div>',
        f'          <div style="font-size:12px;color:var(--text-muted);margin-bottom:14px;">{pl} &middot; {company}</div>',
        f'          <a href="{url}" target="_blank" rel="noopener noreferrer" class="btn-visit" style="width:100%;justify-content:center;">{visit_site}</a>',
        "        </div>",
        "      </aside>",
        "    </div>",
        "  </main>",
        "",
        "  <footer>",
        '    <div class="container">',
        '      <div class="footer-grid">',
        '        <div class="footer-brand">',
        f'          <a href="{logo_href}" class="logo">AI Pulse</a>',
        f"          <p>{footer_desc}</p>",
        "        </div>",
        '        <div class="footer-col">',
        f"          <h4>{footer_cats}</h4>",
        "          <ul>",
        *ft_cat_links,
        "          </ul>",
        "        </div>",
        '        <div class="footer-col">',
        f"          <h4>{footer_links}</h4>",
        "          <ul>",
        f'            <li>{ft_home}</li>',
        f'            <li>{ft_blog}</li>',
        '            <li><a href="https://github.com/2193824842-spec/ai-pulse" target="_blank">GitHub</a></li>',
        '            <li><a href="/ai-pulse/privacy.html">Privacy Policy</a></li>',
        "          </ul>",
        "        </div>",
        "      </div>",
        '      <div class="footer-bottom">',
        "        <span>&copy; 2026 AI Pulse</span>",
        "        <span>Built with curiosity &amp; code</span>",
        "      </div>",
        "    </div>",
        "  </footer>",
        "</body>",
        "</html>",
    ]
    return "\n".join(lines)


def main():
    import sys
    zh_only = "--zh-only" in sys.argv
    all_tools = load_tools_index()
    zh_dir = SITE_DIR / "zh" / "tools"
    zh_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for kb_file in sorted(KB_DIR.glob("*.json")):
        with open(kb_file, encoding="utf-8") as f:
            tool_data = json.load(f)
        slug = tool_data.get("slug") or slugify(tool_data["name"])
        tool_data["slug"] = slug
        if not zh_only:
            html = generate_page(tool_data, all_tools, lang="en")
            out = TOOLS_DIR / f"{slug}.html"
            with open(out, "w", encoding="utf-8") as f:
                f.write(html)
        zh_html = generate_page(tool_data, all_tools, lang="zh")
        zh_out = zh_dir / f"{slug}.html"
        with open(zh_out, "w", encoding="utf-8") as f:
            f.write(zh_html)
        suffix = " (zh only)" if zh_only else " + zh"
        print(f"  ok {slug}.html{suffix}")
        count += 1
    label = "ZH pages" if zh_only else "pages (EN + ZH)"
    print(f"\nDone: {count} {label} generated.")


if __name__ == "__main__":
    main()
