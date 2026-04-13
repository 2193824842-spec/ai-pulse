"""
从已发布的英文 HTML 提取内容，重组为 zh-rewriter 所需的 Markdown + SEO_METADATA 格式
用法：python scripts/extract_markdown.py <slug>
"""

import sys
import os
import json
import re
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def inline_to_markdown(element) -> str:
    """把内联元素（含链接）转成 Markdown，保留 <a> 链接"""
    from bs4 import NavigableString
    parts = []
    for child in element.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif hasattr(child, 'name'):
            tag = child.name
            if tag == 'a':
                href = child.get('href', '')
                text = child.get_text(strip=True)
                if href and text:
                    parts.append(f"[{text}]({href})")
                else:
                    parts.append(text)
            elif tag == 'strong':
                parts.append(f"**{child.get_text(strip=True)}**")
            elif tag == 'em':
                parts.append(f"*{child.get_text(strip=True)}*")
            elif tag == 'code':
                parts.append(f"`{child.get_text(strip=True)}`")
            else:
                parts.append(inline_to_markdown(child))
    return ''.join(parts)


def html_to_markdown(element) -> str:
    """递归把 HTML 元素转成 Markdown"""
    parts = []
    for child in element.children:
        if hasattr(child, 'name'):
            tag = child.name
            if tag in ('h1',):
                parts.append(f"# {child.get_text(strip=True)}\n")
            elif tag in ('h2',):
                parts.append(f"\n## {child.get_text(strip=True)}\n")
            elif tag in ('h3',):
                parts.append(f"\n### {child.get_text(strip=True)}\n")
            elif tag in ('h4',):
                parts.append(f"\n#### {child.get_text(strip=True)}\n")
            elif tag == 'p':
                text = inline_to_markdown(child).strip()
                if text:
                    parts.append(f"\n{text}\n")
            elif tag == 'ul':
                for li in child.find_all('li', recursive=False):
                    parts.append(f"- {inline_to_markdown(li).strip()}\n")
            elif tag == 'ol':
                for i, li in enumerate(child.find_all('li', recursive=False), 1):
                    parts.append(f"{i}. {inline_to_markdown(li).strip()}\n")
            elif tag == 'blockquote':
                parts.append(f"> {child.get_text(strip=True)}\n")
            elif tag == 'table':
                rows = child.find_all('tr')
                for j, row in enumerate(rows):
                    cells = row.find_all(['th', 'td'])
                    parts.append('| ' + ' | '.join(c.get_text(strip=True) for c in cells) + ' |\n')
                    if j == 0:
                        parts.append('| ' + ' | '.join('---' for _ in cells) + ' |\n')
            elif tag in ('div', 'section', 'article'):
                parts.append(html_to_markdown(child))
            elif tag == 'strong':
                parts.append(f"**{child.get_text(strip=True)}**")
            elif tag == 'em':
                parts.append(f"*{child.get_text(strip=True)}*")
            elif tag == 'a':
                href = child.get('href', '')
                text = child.get_text(strip=True)
                parts.append(f"[{text}]({href})")
            elif tag == 'code':
                parts.append(f"`{child.get_text(strip=True)}`")
            elif tag == 'pre':
                parts.append(f"\n```\n{child.get_text()}\n```\n")
        else:
            # 纯文本节点
            text = str(child).strip()
            if text:
                parts.append(text)
    return ''.join(parts)


def extract(slug: str) -> str:
    html_path = os.path.join(ROOT, 'site', 'posts', f'{slug}.html')
    if not os.path.isfile(html_path):
        raise FileNotFoundError(f"Not found: {html_path}")

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # --- metadata from head ---
    title = soup.find('meta', property='og:title')
    title = title['content'] if title else soup.title.get_text(strip=True).split('—')[0].strip()

    description = soup.find('meta', attrs={'name': 'description'})
    description = description['content'] if description else ''

    date_meta = soup.find('meta', property='article:published_time')
    date = date_meta['content'] if date_meta else '2026-04-10'

    tags_meta = soup.find('meta', attrs={'name': 'article-tags'})
    tags = [t.strip() for t in tags_meta['content'].split(',')] if tags_meta else []

    # article_type from schema
    article_type = 'Opinion'
    schema_scripts = soup.find_all('script', type='application/ld+json')
    for s in schema_scripts:
        try:
            data = json.loads(s.string)
            if data.get('@type') == 'Article':
                article_type = data.get('articleSection', article_type)
                word_count = data.get('wordCount', 1500)
                break
        except Exception:
            pass

    # slug
    canonical = soup.find('link', rel='canonical')
    if canonical:
        slug_from_url = canonical['href'].rstrip('/').split('/')[-1].replace('.html', '')
    else:
        slug_from_url = slug

    # --- article body ---
    body = soup.find(class_='article-body') or soup.find('article') or soup.find('main')
    if not body:
        raise ValueError("Cannot find article body in HTML")

    markdown_body = html_to_markdown(body).strip()

    # --- assemble output ---
    output = f"# {title}\n\n{markdown_body}\n\n---\nSEO_METADATA:\n"
    output += f"title: {title}\n"
    output += f"slug: {slug_from_url}\n"
    output += f"excerpt: {description}\n"
    output += f"article_type: {article_type}\n"
    output += f"level: Intermediate\n"
    output += f"tags: {json.dumps(tags, ensure_ascii=False)}\n"
    output += f"date: {date}\n"
    output += f"target_audience: [learner, investor]\n"
    output += f"word_count: {word_count}\n"

    return output


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/extract_markdown.py <slug>")
        sys.exit(1)

    slug = sys.argv[1]
    result = extract(slug)
    out_path = os.path.join(ROOT, 'data', f'{slug}_extracted.md')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"Saved to: {out_path}")
    print(f"Length: {len(result)} chars")
