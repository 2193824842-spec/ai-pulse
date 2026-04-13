#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新翻译已有文章 - 使用完整HTML翻译方法
"""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
import anthropic
import os

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
    prompt = f"""You are translating a technical article about AI from English to Chinese.

**Context:**
- Article type: {context.get('article_type', 'article')}
- Category: {context.get('category', 'AI')}
- Target audience: {', '.join(context.get('target_audience', ['professionals']))}

**Translation requirements:**
1. Preserve ALL HTML tags, attributes, and structure exactly
2. Only translate text content inside tags
3. Keep technical terms in their common Chinese form:
   - "AI" → "AI" (keep as is)
   - "machine learning" → "机器学习"
   - "API" → "API"
   - Company/product names → keep original (e.g., "OpenAI", "Claude")
4. Maintain professional, natural Chinese
5. Do NOT translate:
   - URLs in href attributes
   - CSS class names
   - Code blocks content
   - Image alt text with technical identifiers
6. Preserve special HTML structures:
   - FAQ sections: `<div class="callout-card callout-faq">`
   - Pros/Cons grids: `<div class="pros-cons-grid">`
   - Tables: `<table>...</table>`
   - References: `<h2>References</h2><ul>...</ul>`
   - Related articles: `<!-- RELATED_START -->...<!-- RELATED_END -->`

**HTML to translate:**
{html_section}

**Output:** Return ONLY the translated HTML with no explanations or markdown code blocks."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()

def generate_chinese_html(slug, translated_body, zh_meta, template):
    """生成完整的中文HTML文件"""
    meta = zh_meta[slug]

    # 替换模板占位符
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

    # 生成标签
    tags_html = ''.join([f'<a href="/ai-pulse/zh/blog.html?tag={tag}" class="tag">{tag}</a>' for tag in meta['tags']])
    html = html.replace('{{TAGS}}', tags_html)

    # 生成面包屑
    breadcrumb = f'<a href="/ai-pulse/zh/">首页</a> &gt; <a href="/ai-pulse/zh/blog.html?category={meta["category"]}">{meta["category"]}</a> &gt; <span>{meta["title"]}</span>'
    html = html.replace('{{BREADCRUMB_NAV}}', breadcrumb)

    # Schema JSON-LD
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

    # 插入翻译后的内容
    html = html.replace('{{CONTENT}}', translated_body)

    return html

def main():
    print("开始重新翻译所有文章...")

    # 初始化Claude客户端
    client = anthropic.Anthropic(
        api_key=ANTHROPIC_API_KEY,
        base_url=ANTHROPIC_BASE_URL
    )

    # 读取中文元数据
    with open('site/zh/posts/index.json', 'r', encoding='utf-8') as f:
        zh_meta = {item['slug']: item for item in json.load(f)}

    # 读取中文模板
    with open('site/zh/posts/_template.html', 'r', encoding='utf-8') as f:
        template = f.read()

    # 获取所有英文文章
    posts_dir = Path('site/posts')
    articles = [f.stem for f in posts_dir.glob('*.html') if f.stem != '_template']

    print(f"找到 {len(articles)} 篇文章")

    for i, slug in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}] 翻译: {slug}")

        # 读取英文文章
        en_path = Path(f'site/posts/{slug}.html')
        if not en_path.exists():
            print(f"  [X] 英文文章不存在")
            continue

        # 检查中文元数据
        if slug not in zh_meta:
            print(f"  [X] 中文元数据不存在，跳过")
            continue

        # 提取完整的 article-body
        article_body_html = extract_article_body(en_path)
        if not article_body_html:
            print(f"  [X] 无法提取文章正文")
            continue

        # 准备上下文
        context = {
            "article_type": "technical article",
            "category": zh_meta[slug].get('category', 'AI'),
            "target_audience": ["professionals", "developers"]
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
                # 使用原文
                translated_sections.append(section)

        # 合并翻译结果
        translated_body = '\n'.join(translated_sections)

        # 生成完整HTML
        html = generate_chinese_html(slug, translated_body, zh_meta, template)

        # 保存文件
        output_path = Path(f'site/zh/posts/{slug}.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  [OK] 完成: {output_path}")

    print("\n所有文章重新翻译完成！")

if __name__ == '__main__':
    main()
