#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量翻译英文文章到中文
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

# 需要翻译的文章列表
ARTICLES_TO_TRANSLATE = [
    "best-machine-learning-frameworks-2026-beginners-guide",
    "best-reasoning-models-ai-2026",
    "slackbot-ai-features-enterprise-automation-2026",
    "generative-video-ai-guide-2025",
    "openai-122b-agentic-workflows-gpt54",
    "gemini-3-1-pro-vs-gpt-5-4-comparison"
]

def translate_content(content, client):
    """使用Claude API翻译内容"""
    prompt = f"""请将以下英文技术文章内容翻译成中文。要求：

1. 保持专业性和可读性
2. 技术术语使用常见的中文翻译（如AI、机器学习、深度学习等可保留英文或使用通用译法）
3. 保持原文的段落结构
4. 翻译要自然流畅，符合中文技术文章习惯
5. 只返回翻译后的内容，不要添加任何解释

原文：
{content}"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

def extract_article_body(html_path):
    """提取文章正文内容"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    article_body = soup.find('div', class_='article-body')
    if article_body:
        return str(article_body)
    return None

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
    print("开始批量翻译文章...")

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

    # 逐篇翻译
    for i, slug in enumerate(ARTICLES_TO_TRANSLATE, 1):
        print(f"\n[{i}/{len(ARTICLES_TO_TRANSLATE)}] 翻译: {slug}")

        # 检查是否已存在
        output_path = Path(f'site/zh/posts/{slug}.html')
        if output_path.exists():
            print(f"  [OK] 已存在，跳过")
            continue

        # 读取英文文章
        en_path = Path(f'site/posts/{slug}.html')
        if not en_path.exists():
            print(f"  [X] 英文文章不存在")
            continue

        # 提取正文
        article_body_html = extract_article_body(en_path)
        if not article_body_html:
            print(f"  [X] 无法提取文章正文")
            continue

        # 解析HTML提取纯文本进行翻译
        soup = BeautifulSoup(article_body_html, 'html.parser')

        # 分段翻译（避免超过token限制）
        paragraphs = soup.find_all(['p', 'h2', 'h3', 'li'])
        translated_parts = []

        batch = []
        batch_text = ""

        for elem in paragraphs:
            text = elem.get_text().strip()
            if not text:
                continue

            # 如果当前批次太大，先翻译
            if len(batch_text) + len(text) > 3000:
                print(f"  翻译批次 ({len(batch)} 个元素)...")
                batch_content = "\n\n".join([f"<{e.name}>{e.get_text()}</{e.name}>" for e in batch])
                translated = translate_content(batch_content, client)
                translated_parts.append(translated)
                batch = []
                batch_text = ""

            batch.append(elem)
            batch_text += text

        # 翻译最后一批
        if batch:
            print(f"  翻译最后批次 ({len(batch)} 个元素)...")
            batch_content = "\n\n".join([f"<{e.name}>{e.get_text()}</{e.name}>" for e in batch])
            translated = translate_content(batch_content, client)
            translated_parts.append(translated)

        # 合并翻译结果
        translated_body = "\n".join(translated_parts)

        # 生成完整HTML
        html = generate_chinese_html(slug, translated_body, zh_meta, template)

        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  [OK] 完成: {output_path}")

    print("\n所有文章翻译完成！")

if __name__ == '__main__':
    main()
