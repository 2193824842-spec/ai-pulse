#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充中文文章缺失的部分（FAQ、参考文献、相关文章）
"""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
import anthropic

# 配置
ANTHROPIC_API_KEY = "sk-aVuKn67DUQquA9IyypAoD0Lq2tQKEp2Z9FHFmhWVhIHlQRBs"
ANTHROPIC_BASE_URL = "https://aiapi.tnt-pub.com"

def extract_missing_sections(en_html_path):
    """提取英文文章中的FAQ、参考文献、相关文章"""
    with open(en_html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    article_body = soup.find('div', class_='article-body')
    if not article_body:
        return None, None, None

    # 提取FAQ
    faq_section = article_body.find('div', class_='callout-faq')
    faq_html = str(faq_section) if faq_section else None

    # 提取参考文献
    references_html = None
    for h2 in article_body.find_all('h2'):
        if 'References' in h2.get_text():
            # 找到References标题后的ul
            next_ul = h2.find_next_sibling('ul')
            if next_ul:
                references_html = f"<h2>References</h2>\n{str(next_ul)}"
            break

    # 提取相关文章
    related_start = soup.find(string=lambda text: '<!-- RELATED_START -->' in str(text))
    related_html = None
    if related_start:
        # 找到RELATED_START和RELATED_END之间的内容
        parent = related_start.parent
        related_section = parent.find('section', class_='related-posts')
        if related_section:
            related_html = str(related_section)

    return faq_html, references_html, related_html

def translate_section(html_content, section_type, client):
    """翻译单个部分"""
    if not html_content:
        return None

    section_names = {
        'faq': 'FAQ (Frequently Asked Questions)',
        'references': 'References',
        'related': 'Related Articles'
    }

    prompt = f"""Translate this {section_names[section_type]} section from English to Chinese.

**Requirements:**
1. Preserve ALL HTML tags and attributes exactly
2. Only translate text content
3. For {section_type}:
   - FAQ: Translate questions and answers naturally
   - References: Keep URLs unchanged, translate link text if descriptive
   - Related: Translate article titles and descriptions, keep URLs
4. Keep technical terms: AI, API, etc.
5. Maintain professional Chinese

**HTML:**
{html_content}

**Output:** Return ONLY the translated HTML."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()

def append_to_chinese_article(zh_html_path, faq_html, references_html, related_html):
    """将翻译后的部分追加到中文文章"""
    with open(zh_html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    article_body = soup.find('div', class_='article-body')

    if not article_body:
        print(f"  [X] 找不到 article-body")
        return False

    # 检查是否已有这些部分
    has_faq = article_body.find('div', class_='callout-faq') is not None
    has_references = any('参考' in h2.get_text() or 'References' in h2.get_text()
                        for h2 in article_body.find_all('h2'))

    # 追加FAQ（如果没有）
    if faq_html and not has_faq:
        faq_soup = BeautifulSoup(faq_html, 'html.parser')
        article_body.append(faq_soup)
        print(f"  [+] 添加FAQ")

    # 追加参考文献（如果没有）
    if references_html and not has_references:
        ref_soup = BeautifulSoup(references_html, 'html.parser')
        article_body.append(ref_soup)
        print(f"  [+] 添加参考文献")

    # 保存修改后的HTML
    with open(zh_html_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    return True

def main():
    print("开始补充中文文章缺失部分...")

    client = anthropic.Anthropic(
        api_key=ANTHROPIC_API_KEY,
        base_url=ANTHROPIC_BASE_URL
    )

    # 获取所有文章
    posts_dir = Path('site/posts')
    articles = [f.stem for f in posts_dir.glob('*.html') if f.stem != '_template']

    print(f"找到 {len(articles)} 篇文章\n")

    for i, slug in enumerate(articles, 1):
        print(f"[{i}/{len(articles)}] 处理: {slug}")

        en_path = Path(f'site/posts/{slug}.html')
        zh_path = Path(f'site/zh/posts/{slug}.html')

        if not zh_path.exists():
            print(f"  [X] 中文文章不存在，跳过")
            continue

        # 提取英文的缺失部分
        faq_en, ref_en, related_en = extract_missing_sections(en_path)

        if not any([faq_en, ref_en, related_en]):
            print(f"  [-] 没有需要补充的内容")
            continue

        # 翻译各部分
        faq_zh = None
        ref_zh = None

        if faq_en:
            print(f"  翻译FAQ...")
            try:
                faq_zh = translate_section(faq_en, 'faq', client)
            except Exception as e:
                print(f"  [!] FAQ翻译失败: {e}")

        if ref_en:
            print(f"  翻译参考文献...")
            try:
                ref_zh = translate_section(ref_en, 'references', client)
            except Exception as e:
                print(f"  [!] 参考文献翻译失败: {e}")

        # 追加到中文文章
        if faq_zh or ref_zh:
            append_to_chinese_article(zh_path, faq_zh, ref_zh, None)
            print(f"  [OK] 完成")
        else:
            print(f"  [-] 无内容可添加")

    print("\n补充完成！")

if __name__ == '__main__':
    main()
