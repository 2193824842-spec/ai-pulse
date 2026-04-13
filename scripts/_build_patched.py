"""
Patched build_site.py with hardcoded SITE_DIR
"""
import json
import os
import re
from datetime import datetime

SITE_DIR = 'D:\\seo-farm\\site'
INDEX_JSON = os.path.join(SITE_DIR, 'posts', 'index.json')
BLOG_HTML = os.path.join(SITE_DIR, 'blog.html')
HOME_HTML = os.path.join(SITE_DIR, 'index.html')

# Chinese version paths
ZH_INDEX_JSON = os.path.join(SITE_DIR, 'zh', 'posts', 'index.json')
ZH_BLOG_HTML = os.path.join(SITE_DIR, 'zh', 'blog.html')
ZH_HOME_HTML = os.path.join(SITE_DIR, 'zh', 'index.html')


def load_posts():
    with open(INDEX_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def estimate_read_time(word_count):
    if word_count and word_count > 100:
        return max(2, min(15, round(word_count / 200)))
    return 0


def render_card(post, lang='en'):
    slug = post['slug']
    title = post.get('title', '')
    excerpt = post.get('excerpt', '')
    date_raw = post.get('date', '')
    category = post.get('category', '')
    tags = post.get('tags', [])
    view_count = post.get('view_count', 0)
    cover = post.get('cover_image', '')

    word_count = post.get('word_count', 0)
    read_min = estimate_read_time(word_count)

    try:
        dt = datetime.strptime(date_raw, '%Y-%m-%d')
        if lang == 'zh':
            date_fmt = dt.strftime('%Y年%m月%d日')
        else:
            date_fmt = dt.strftime('%b %d, %Y')
    except ValueError:
        date_fmt = date_raw

    tags_html = ''.join(
        f'<span class="tag">{t}</span>'
        for t in tags[:3]
    )

    if cover:
        img_html = f'<div class="card-cover"><img src="{cover}" alt="{title}" loading="lazy" onerror="this.dataset.error=1" /><span class="card-cat-badge">{category}</span><span class="card-date-badge">{date_fmt}</span></div>'
    else:
        img_html = f'<div class="card-cover card-cover-placeholder"><span class="card-cat-badge">{category}</span><span class="card-date-badge">{date_fmt}</span></div>'

    read_time_text = '分钟阅读' if lang == 'zh' else 'min read'
    read_time_html = f'<span class="read-time">{read_min} {read_time_text}</span>' if read_min > 0 else ''

    base_path = '/ai-pulse/zh/posts' if lang == 'zh' else '/ai-pulse/posts'
    return f'''      <a href="{base_path}/{slug}.html" class="post-card" data-cat="{category}" data-tags="{','.join(tags)}" data-date="{date_raw}" data-views="{view_count}">
        {img_html}
        <div class="post-card-body">
          <h2 class="post-title">{title}</h2>
          <p class="post-excerpt">{excerpt}</p>
          <div class="post-card-footer">
            <div class="post-tags">{tags_html}</div>
            {read_time_html}
          </div>
        </div>
      </a>'''


def build_blog_cards(posts, lang='en'):
    sorted_posts = sorted(posts, key=lambda p: p.get('date', ''), reverse=True)
    return '\n'.join(render_card(p, lang) for p in sorted_posts)


def build_home_cards(posts, lang='en'):
    sorted_posts = sorted(posts, key=lambda p: p.get('date', ''), reverse=True)
    return '\n'.join(render_card(p, lang) for p in sorted_posts[:6])


def build_tag_buttons(posts):
    tag_count = {}
    for p in posts:
        for t in p.get('tags', []):
            tag_count[t] = tag_count.get(t, 0) + 1
    top_tags = sorted(
        [(t, c) for t, c in tag_count.items() if c >= 2],
        key=lambda x: -x[1]
    )[:12]
    return ''.join(
        f'\n        <button class="filter-btn tag-btn" data-tag="{t}">{t}</button>'
        for t, _ in top_tags
    )


def inject(html_path, start_marker, end_marker, content):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    pattern = re.escape(start_marker) + r'.*?' + re.escape(end_marker)
    replacement = start_marker + '\n' + content + '\n' + end_marker
    html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)


def update_stats(html_path, posts):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    categories = set(p.get('category', '') for p in posts if p.get('category'))
    html = re.sub(
        r'(<span class="stat-number" id="stat-articles">)\d+(</span>)',
        rf'\g<1>{len(posts)}\2', html
    )
    html = re.sub(
        r'(<span class="stat-number" id="stat-categories">)\d+(</span>)',
        rf'\g<1>{len(categories)}\2', html
    )
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)


def find_related(current_slug, posts, max_count=3):
    current = next((p for p in posts if p['slug'] == current_slug), None)
    if not current:
        return []
    cur_cat = current.get('category', '')
    cur_tags = set(current.get('tags', []))
    scored = []
    for p in posts:
        if p['slug'] == current_slug:
            continue
        score = 0
        if p.get('category') == cur_cat:
            score += 2
        score += len(cur_tags & set(p.get('tags', [])))
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: (-x[0], x[1].get('date', '')))
    return [p for _, p in scored[:max_count]]


def render_related_html(related_posts, lang='en', base_path='/ai-pulse/posts'):
    if not related_posts:
        return ''
    items = []
    title = 'Related Articles' if lang == 'en' else '相关文章'
    for p in related_posts:
        slug = p['slug']
        title_text = p.get('title', '')
        excerpt = p.get('excerpt', '')[:100]
        items.append(
            f'        <a href="{base_path}/{slug}.html" class="related-card">'
            f'<h4>{title_text}</h4><p>{excerpt}...</p></a>'
        )
    return (
        '      <section class="related-posts">\n'
        f'        <h3>{title}</h3>\n'
        '        <div class="related-grid">\n'
        + '\n'.join(items) + '\n'
        '        </div>\n'
        '      </section>'
    )


def inject_related_posts(posts, lang='en'):
    if lang == 'en':
        posts_dir = os.path.join(SITE_DIR, 'posts')
        base_path = '/ai-pulse/posts'
    else:
        posts_dir = os.path.join(SITE_DIR, 'zh', 'posts')
        base_path = '/ai-pulse/zh/posts'

    for post in posts:
        slug = post['slug']
        html_path = os.path.join(posts_dir, f'{slug}.html')
        if not os.path.isfile(html_path):
            continue
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        related = find_related(slug, posts)
        related_html = render_related_html(related, lang, base_path)
        if '<!-- RELATED_START -->' in html:
            inject(html_path, '<!-- RELATED_START -->', '<!-- RELATED_END -->', related_html)
        elif '</article>' in html and 'related-posts' not in html:
            html = html.replace(
                '</article>',
                f'\n      <!-- RELATED_START -->\n{related_html}\n      <!-- RELATED_END -->\n    </article>'
            )
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)


def main():
    posts = load_posts()
    print(f'Loaded {len(posts)} English posts')

    blog_cards = build_blog_cards(posts)
    inject(BLOG_HTML, '<!-- BLOG_CARDS_START -->', '<!-- BLOG_CARDS_END -->', blog_cards)
    print('Updated blog.html')

    tag_buttons = build_tag_buttons(posts)
    inject(BLOG_HTML, '<!-- TAGS_START -->', '<!-- TAGS_END -->', tag_buttons)
    print('Updated blog.html tag buttons')

    home_cards = build_home_cards(posts)
    inject(HOME_HTML, '<!-- HOME_CARDS_START -->', '<!-- HOME_CARDS_END -->', home_cards)
    update_stats(HOME_HTML, posts)
    print('Updated index.html')

    inject_related_posts(posts)
    print('Updated related articles in posts')

    if os.path.exists(ZH_INDEX_JSON):
        with open(ZH_INDEX_JSON, 'r', encoding='utf-8') as f:
            zh_posts_data = json.load(f)
        print(f'\nLoaded {len(zh_posts_data)} Chinese posts')

        zh_blog_cards = build_blog_cards(zh_posts_data, lang='zh')
        inject(ZH_BLOG_HTML, '<!-- BLOG_CARDS_START -->', '<!-- BLOG_CARDS_END -->', zh_blog_cards)
        print('Updated zh/blog.html')

        zh_tag_buttons = build_tag_buttons(zh_posts_data)
        inject(ZH_BLOG_HTML, '<!-- TAGS_START -->', '<!-- TAGS_END -->', zh_tag_buttons)
        print('Updated zh/blog.html tag buttons')

        zh_home_cards = build_home_cards(zh_posts_data, lang='zh')
        inject(ZH_HOME_HTML, '<!-- HOME_CARDS_START -->', '<!-- HOME_CARDS_END -->', zh_home_cards)
        update_stats(ZH_HOME_HTML, zh_posts_data)
        print('Updated zh/index.html')

        inject_related_posts(zh_posts_data, lang='zh')
        print('Updated related articles in Chinese posts')
    else:
        print('\nNo Chinese posts found, skipping Chinese version')

    print('\nDone!')


if __name__ == '__main__':
    main()
