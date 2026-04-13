#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合修复脚本：
1. 重新翻译 how-to-evaluate-ai-companies-framework（使用完整HTML方法）
2. 修复 build_site.py 添加中文相关文章注入
"""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
import anthropic

# 配置
ANTHROPIC_API_KEY = "sk-aVuKn67DUQquA9IyypAoD0Lq2tQKEp2Z9FHFmhWVhIHlQRBs"
ANTHROPIC_BASE_URL = "https://aiapi.tnt-pub.com"

def extract_article_body(html_path):
    """提取完整的 article-body HTML"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    article_body = soup.find('div', class_='article-body')
    if article_body:
        return str(article_body)
    return None

def split_by_h2(html_content):
    """按 h2 标签分割HTML"""
    # 移除 <div class="article-body"> 包裹
    html_content = re.sub(r'^<div class="article-body">\s*', '', html_content)
    html_content = re.sub(r'\s*</div>$', '', html_content)

    sections = []
    lines = html_content.split('\n')
    current_section = []

    for line in lines:
        if '<h2>' in line and current_section:
            sections.append('\n'.join(current_section))
            current_section = [line]
        else:
            current_section.append(line)

    if current_section:
        sections.append('\n'.join(current_section))

    return sections

def translate_html_section(html_section, client, context):
    """翻译HTML片段，保留所有结构"""
    prompt = f"""Translate this HTML section from English to Chinese.

**Context:**
- Article type: {context.get('article_type', 'article')}
- Category: {context.get('category', 'AI')}

**Requirements:**
1. Preserve ALL HTML tags, attributes, and structure exactly
2. Only translate text content inside tags
3. Keep technical terms: AI, API, OpenAI, Claude, etc.
4. Maintain professional Chinese
5. Do NOT translate:
   - URLs in href attributes
   - CSS class names
   - Code blocks
6. Preserve special structures:
   - FAQ: `<div class="callout-card callout-faq">`
   - Pros/Cons: `<div class="pros-cons-grid">`
   - Tables: `<table>...</table>`
   - References: `<h2>References</h2><ul>...</ul>`

**HTML:**
{html_section}

**Output:** Return ONLY the translated HTML."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    result = message.content[0].text.strip()

    # 移除可能的markdown代码块标记
    result = re.sub(r'^```html\s*', '', result)
    result = re.sub(r'^```\s*', '', result)
    result = re.sub(r'\s*```$', '', result)

    return result

def generate_chinese_html(slug, translated_body, zh_meta, template):
    """生成完整的中文HTML文件"""
    meta = zh_meta[slug]

    html = template
    html = html.replace('{{TITLE}}', meta['title'])
    html = html.replace('{{DESCRIPTION}}', meta['excerpt'])
    html = html.replace('{{SLUG}}', slug)
    html = html.replace('{{CANONICAL_URL}}', f'https://2193824842-spec.github.io/ai-pulse/zh/posts/{slug}.html')
    html = html.replace('{{OG_TITLE}}', meta['title'])
    html = html.replace('{{OG_DESCRIPTION}}', meta['excerpt'])
    html = html.replace('{{OG_IMAGE}}', meta['cover_image'])
    html = html.replace('{{DATE_ISO}}', meta['date'])
    html = html.replace('{{DATE}}', meta['date'].replace('-', '年', 1).replace('-', '月') + '日')
    html = html.replace('{{COVER_IMAGE}}', meta['cover_image'])
    html = html.replace('{{LEVEL_BADGE}}', f'<span class="post-level">{meta["level"]}</span>')

    tags_html = ''.join([f'<a href="/ai-pulse/zh/blog.html?tag={tag}" class="tag">{tag}</a>' for tag in meta['tags']])
    html = html.replace('{{TAGS}}', tags_html)

    breadcrumb = f'<a href="/ai-pulse/zh/">首页</a> &gt; <a href="/ai-pulse/zh/blog.html?category={meta["category"]}">{meta["category"]}</a> &gt; <span>{meta["title"]}</span>'
    html = html.replace('{{BREADCRUMB_NAV}}', breadcrumb)

    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta['title'],
        "description": meta['excerpt'],
        "datePublished": meta['date'],
        "author": {"@type": "Organization", "name": "AI Pulse"},
        "wordCount": meta.get('word_count', 0)
    }
    html = html.replace('{{SCHEMA_JSON_LD}}', f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>')

    # 插入翻译后的内容（包裹在 article-body div 中）
    html = html.replace('{{CONTENT}}', translated_body)

    return html

def main():
    print("修复 how-to-evaluate-ai-companies-framework...")

    client = anthropic.Anthropic(
        api_key=ANTHROPIC_API_KEY,
        base_url=ANTHROPIC_BASE_URL
    )

    with open('site/zh/posts/index.json', 'r', encoding='utf-8') as f:
        zh_meta = {item['slug']: item for item in json.load(f)}

    with open('site/zh/posts/_template.html', 'r', encoding='utf-8') as f:
        template = f.read()

    slug = 'how-to-evaluate-ai-companies-framework'
    en_path = Path(f'site/posts/{slug}.html')

    # 提取完整的 article-body HTML
    article_body_html = extract_article_body(en_path)
    if not article_body_html:
        print("  [X] 无法提取文章正文")
        return

    context = {
        "article_type": "how-to guide",
        "category": "Tool Guide"
    }

    # 按 h2 分割
    sections = split_by_h2(article_body_html)
    print(f"  分为 {len(sections)} 个章节")

    # 翻译每个章节
    translated_sections = []
    for j, section in enumerate(sections, 1):
        print(f"  翻译章节 {j}/{len(sections)}...")
        try:
            translated = translate_html_section(section, client, context)
            translated_sections.append(translated)
        except Exception as e:
            print(f"  [!] 章节 {j} 翻译失败: {e}")
            return

    # 合并翻译结果
    translated_body = '\n'.join(translated_sections)

    # 生成完整HTML
    html = generate_chinese_html(slug, translated_body, zh_meta, template)

    # 保存文件
    output_path = Path(f'site/zh/posts/{slug}.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  [OK] 完成: {output_path}")

if __name__ == '__main__':
    main()
