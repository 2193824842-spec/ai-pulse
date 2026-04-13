"""
把中文翻译 Markdown 文件构建成 zh/posts/[slug].html 并更新 zh/posts/index.json
用法：python scripts/build_zh_article.py <zh_md_path>
"""

import sys
import os
import json
import re
from datetime import datetime

try:
    import markdown as md_lib
    _HAS_MARKDOWN = True
except ImportError:
    _HAS_MARKDOWN = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_metadata(text: str) -> tuple[str, dict]:
    """分离 Markdown 正文和 SEO_METADATA，返回 (body, meta_dict)"""
    if "---\nSEO_METADATA:" in text:
        body, meta_block = text.split("---\nSEO_METADATA:", 1)
    elif "---\r\nSEO_METADATA:" in text:
        body, meta_block = text.split("---\r\nSEO_METADATA:", 1)
    else:
        raise ValueError("SEO_METADATA block not found")

    meta = {}
    for line in meta_block.strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()

    return body.strip(), meta


def md_to_html(text: str) -> str:
    """把 Markdown 正文转成 HTML，支持表格和 FAQ 结构"""
    if _HAS_MARKDOWN:
        html = md_lib.markdown(text, extensions=['tables', 'fenced_code', 'nl2br'])
        # 给表格加 table-wrap 容器
        html = re.sub(r'<table>', '<div class="table-wrap"><table>', html)
        html = re.sub(r'</table>', '</table></div>', html)
    else:
        html = _md_to_html_fallback(text)

    # 裸 URL → 可点击链接（跳过已在 href 属性里的）
    html = re.sub(
        r'(?<!href=")(https?://[^\s<>"\']+)',
        lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>',
        html
    )
    # FAQ 段落包裹：把 <h2>常见问题</h2> 后面的 h3+p 组合包成 callout-faq 结构
    html = _wrap_faq_section(html)
    return html


def _wrap_faq_section(html: str) -> str:
    """把 FAQ h2 段落转成 callout-faq 结构"""
    faq_h2_pattern = re.compile(
        r'(<h2>(?:常见问题|FAQ|常见问答)[^<]*</h2>)(.*?)(?=<h2>|$)',
        re.DOTALL
    )
    def replace_faq(m):
        h2_tag = m.group(1)
        faq_body = m.group(2)
        # 把每个 h3+p 对包成 faq-item
        items_html = re.sub(
            r'(<h3>.*?</h3>)\s*(<p>.*?</p>)',
            r'<div class="faq-item">\1\2</div>',
            faq_body,
            flags=re.DOTALL
        )
        return (
            '<div class="callout-card callout-faq">'
            + h2_tag
            + '<div class="faq-grid">'
            + items_html
            + '</div></div>'
        )
    return faq_h2_pattern.sub(replace_faq, html)


def _md_to_html_fallback(text: str) -> str:
    """无 markdown 库时的简易转换（不支持表格）"""
    lines = text.splitlines()
    html_parts = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#### "):
            html_parts.append(f"<h4>{inline_md(line[5:])}</h4>")
        elif line.startswith("### "):
            html_parts.append(f"<h3>{inline_md(line[4:])}</h3>")
        elif line.startswith("## "):
            html_parts.append(f"<h2>{inline_md(line[3:])}</h2>")
        elif line.startswith("# "):
            html_parts.append(f"<h1>{inline_md(line[2:])}</h1>")
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{inline_md(lines[i][2:])}</li>")
                i += 1
            html_parts.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif re.match(r"^\d+\. ", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                items.append(f"<li>{inline_md(re.sub(r'^\\d+\\. ', '', lines[i]))}</li>")
                i += 1
            html_parts.append("<ol>" + "".join(items) + "</ol>")
            continue
        elif line.startswith("> "):
            html_parts.append(f"<blockquote><p>{inline_md(line[2:])}</p></blockquote>")
        elif line.strip() == "":
            pass
        else:
            html_parts.append(f"<p>{inline_md(line)}</p>")
        i += 1
    return "\n".join(html_parts)


def inline_md(text: str) -> str:
    """处理行内 Markdown：链接、粗体、斜体、代码"""
    # 链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # 粗体
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 斜体
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # 行内代码
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # 裸 URL → 可点击链接（跳过已在 href 属性里的）
    text = re.sub(
        r'(?<!href=")(https?://[^\s<>"\']+)',
        lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>',
        text
    )
    return text


def parse_tags(tags_str: str) -> list:
    """解析 tags 字段，支持 JSON 数组或逗号分隔"""
    tags_str = tags_str.strip()
    if tags_str.startswith("["):
        try:
            return json.loads(tags_str)
        except Exception:
            pass
    return [t.strip().strip('"') for t in tags_str.strip("[]").split(",") if t.strip()]


def build(zh_md_path: str):
    with open(zh_md_path, "r", encoding="utf-8") as f:
        text = f.read()

    body, meta = parse_metadata(text)

    # 去掉正文里的 H1（模板里已有标题）
    body_no_h1 = re.sub(r'^# .+\n?', '', body, count=1).strip()

    slug = meta.get("slug", "")
    title = meta.get("title", "")
    description = meta.get("excerpt", "")
    date_iso = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
    article_type = meta.get("article_type", "Opinion")
    level = meta.get("level", "Intermediate")
    tags = parse_tags(meta.get("tags", "[]"))
    word_count = int(meta.get("word_count", 1500))
    og_title = meta.get("og_title", title)
    og_description = meta.get("og_description", description)
    breadcrumb_raw = meta.get("breadcrumb", f"首页 > 文章 > {title}")

    # 日期格式
    try:
        dt = datetime.strptime(date_iso, "%Y-%m-%d")
        date_cn = dt.strftime("%Y年%m月%d日")
    except Exception:
        date_cn = date_iso

    # 转换正文 HTML
    content_html = md_to_html(body_no_h1)

    # 标签 HTML
    tags_html = "".join(
        f'<a href="/ai-pulse/zh/blog.html?tag={t}" class="tag">{t}</a>' for t in tags
    )
    tag_list = ", ".join(tags)

    # level badge
    level_badge = f'<span class="post-level">{level}</span>'

    # breadcrumb
    parts = [p.strip() for p in breadcrumb_raw.split(">")]
    breadcrumb_html = ""
    if len(parts) >= 1:
        breadcrumb_html += f'<a href="/ai-pulse/zh/">首页</a>'
    if len(parts) >= 2:
        breadcrumb_html += f' &gt; <a href="/ai-pulse/zh/blog.html">{parts[1]}</a>'
    if len(parts) >= 3:
        breadcrumb_html += f' &gt; <span>{parts[2]}</span>'

    # schema JSON-LD
    schema_parts = []
    for key in ("schema_article", "schema_faq", "schema_howto", "schema_breadcrumb"):
        val = meta.get(key, "none").strip()
        if val and val != "none":
            schema_parts.append(f'<script type="application/ld+json">{val}</script>')
    schema_html = "\n".join(schema_parts)

    # 读模板
    template_path = os.path.join(ROOT, "site", "zh", "posts", "_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 填占位符
    replacements = {
        "{{TITLE}}": title,
        "{{DESCRIPTION}}": description,
        "{{SLUG}}": slug,
        "{{CANONICAL_URL}}": f"https://2193824842-spec.github.io/ai-pulse/zh/posts/{slug}.html",
        "{{DATE_ISO}}": date_iso,
        "{{DATE}}": date_cn,
        "{{COVER_IMAGE}}": f"../../assets/images/{slug}.jpg",
        "{{OG_IMAGE}}": f"https://2193824842-spec.github.io/ai-pulse/assets/images/{slug}.jpg",
        "{{OG_TITLE}}": og_title,
        "{{OG_DESCRIPTION}}": og_description,
        "{{TAGS}}": tags_html,
        "{{TAG_LIST}}": tag_list,
        "{{LEVEL_BADGE}}": level_badge,
        "{{BREADCRUMB_NAV}}": breadcrumb_html,
        "{{CONTENT}}": content_html,
        "{{SCHEMA_JSON_LD}}": schema_html,
    }

    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    # 写 HTML 文件
    out_path = os.path.join(ROOT, "site", "zh", "posts", f"{slug}.html")
    # 术语标准化
    try:
        sys.path.insert(0, os.path.join(ROOT, "core"))
        from zh_glossary import apply_all
        html = apply_all(html)
    except Exception:
        pass

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Written: {out_path} ({len(html)} chars)")

    # 更新 index.json
    index_path = os.path.join(ROOT, "site", "zh", "posts", "index.json")
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    # 去重
    index = [a for a in index if a.get("slug") != slug]

    new_entry = {
        "slug": slug,
        "title": title,
        "excerpt": description,
        "date": date_iso,
        "category": article_type,
        "level": level,
        "tags": tags,
        "cover_image": f"/ai-pulse/assets/images/{slug}.jpg",
        "word_count": word_count,
        "view_count": 0,
        "featured": False,
    }
    index.insert(0, new_entry)

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"Updated: {index_path} ({len(index)} articles)")
    print(f"ZH_PUBLISHED: {slug}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/build_zh_article.py <zh_md_path>")
        sys.exit(1)
    build(sys.argv[1])
