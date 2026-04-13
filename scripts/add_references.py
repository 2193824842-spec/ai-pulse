#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单直接的修复脚本 - 只添加英文参考文献
"""
from pathlib import Path

# 参考文献映射
REFERENCES = {
    'best-reasoning-models-ai-2026': [
        ('OpenAI o3 Announcement', 'https://openai.com/index/early-access-to-o3/'),
        ('DeepSeek-R1 Technical Report', 'https://github.com/deepseek-ai/DeepSeek-R1'),
        ('Anthropic Extended Thinking', 'https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking'),
    ],
    'gemini-3-1-pro-vs-gpt-5-4-comparison': [
        ('Google Gemini 3.1 Pro', 'https://blog.google/technology/ai/google-gemini-ai-update/'),
        ('OpenAI GPT-5.4', 'https://openai.com/index/gpt-5-4/'),
        ('ARC-AGI Benchmark', 'https://arcprize.org/'),
    ],
    'generative-video-ai-guide-2025': [
        ('OpenAI Sora', 'https://openai.com/sora'),
        ('Runway Gen-3', 'https://runwayml.com/'),
        ('Pika 2.0', 'https://pika.art/'),
    ],
    'openai-122b-agentic-workflows-gpt54': [
        ('OpenAI Funding News', 'https://openai.com/blog/'),
        ('GPT-5.4 Documentation', 'https://platform.openai.com/docs/'),
    ],
    'sora-2-physics-accurate-ai-video-generation': [
        ('Sora 2 Release', 'https://openai.com/sora'),
        ('OpenAI Research', 'https://openai.com/research/'),
    ]
}

def add_references(slug):
    """添加参考文献到英文文章"""
    if slug not in REFERENCES:
        return False

    html_path = Path(f'site/posts/{slug}.html')
    if not html_path.exists():
        print(f'  [X] File not found: {html_path}')
        return False

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 检查是否已有
    if '<h2>References</h2>' in html:
        print(f'  [-] {slug} already has references')
        return False

    # 生成HTML
    refs_html = '<h2>References</h2>\n<ul>\n'
    for title, url in REFERENCES[slug]:
        refs_html += f'<li><a href="{url}">{title}</a></li>\n'
    refs_html += '</ul>'

    # 插入到 author-box 之前
    if '      <div class="author-box">' in html:
        html = html.replace(
            '      <div class="author-box">',
            f'{refs_html}\n\n      <div class="author-box">'
        )
    else:
        print(f'  [!] Cannot find insertion point in {slug}')
        return False

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'  [OK] Added references to {slug}')
    return True

def main():
    print('Adding references to English articles...\n')

    count = 0
    for slug in REFERENCES.keys():
        if add_references(slug):
            count += 1

    print(f'\nDone! Added references to {count} articles.')

if __name__ == '__main__':
    main()
