"""
publish_article.py — Converts markdown article to HTML and publishes to site.
"""
import sys
sys.path.insert(0, './lib')

import json
import os
import re
from datetime import datetime

import markdown as md_lib

# ── Config ──────────────────────────────────────────────────────────────────
SLUG = "best-ai-agent-frameworks-2026"
TITLE = "Best AI Agent Frameworks 2026: CrewAI vs LangGraph vs AutoGen Compared"
EXCERPT = "Compare the top AI agent frameworks in 2026 — LangGraph, CrewAI, and OpenAI Agents SDK — with production metrics, cost analysis, and a decision guide for developers and investors."
DATE = "2026-04-10"
CATEGORY = "Model Comparison"
TAGS = ["ai-agents", "ai-tools", "llm", "enterprise-ai", "code-generation"]
LEVEL = "Intermediate"
TARGET_AUDIENCE = ["learner", "investor"]
COVER_IMAGE = f"/ai-pulse/assets/images/{SLUG}.jpg"
CANONICAL_URL = f"https://2193824842-spec.github.io/ai-pulse/posts/{SLUG}.html"
OG_TITLE = "Best AI Agent Frameworks 2026: LangGraph vs CrewAI"
OG_DESCRIPTION = "Compare LangGraph, CrewAI, OpenAI Agents SDK, and more — production metrics, cost analysis, and a decision framework for developers and investors."
OG_IMAGE = f"https://2193824842-spec.github.io/ai-pulse/assets/images/{SLUG}.jpg"

SITE_DIR = "./site"
POSTS_DIR = os.path.join(SITE_DIR, "posts")
INDEX_JSON = os.path.join(POSTS_DIR, "index.json")
TEMPLATE_PATH = os.path.join(POSTS_DIR, "_template.html")
ARTICLE_MD = f"./data/articles/{SLUG}.md"

# ── Schema JSON-LD ───────────────────────────────────────────────────────────
SCHEMA_ARTICLE = {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": TITLE,
    "description": EXCERPT,
    "datePublished": DATE,
    "dateModified": DATE,
    "image": OG_IMAGE,
    "mainEntityOfPage": {"@type": "WebPage", "@id": CANONICAL_URL},
    "author": {
        "@type": "Person",
        "name": "Avery Tong",
        "url": "https://2193824842-spec.github.io/ai-pulse/about.html"
    },
    "publisher": {
        "@type": "Organization",
        "name": "AI Pulse",
        "url": "https://2193824842-spec.github.io/ai-pulse/",
        "logo": {"@type": "ImageObject", "url": "https://2193824842-spec.github.io/ai-pulse/favicon.svg"}
    },
    "keywords": "best AI agent frameworks 2026, LangGraph vs CrewAI, AI agent framework comparison, multi-agent framework Python",
    "articleSection": CATEGORY,
    "wordCount": 1850
}

SCHEMA_FAQ = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {
            "@type": "Question",
            "name": "How do I choose the best AI agent framework?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Use these key questions: (1) Do your agents need to remember context across sessions? LangGraph's checkpointing is ideal. (2) Do you need multiple specialized agents collaborating? CrewAI excels at multi-agent orchestration. (3) What language are you using? Python dominates, but Mastra is the best option for TypeScript. (4) Do you have enterprise requirements? Security, compliance, and on-premise deployment narrow choices to CrewAI AMP, Microsoft Agent Framework, or LangGraph Platform."
            }
        },
        {
            "@type": "Question",
            "name": "What AI agent framework should I use for production in 2026?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "LangGraph is the production standard for teams shipping agents at scale, with 400+ companies running it in production including Cisco, Uber, LinkedIn, BlackRock, and JPMorgan. For multi-agent team scenarios, CrewAI is the best choice with its role-based crew model."
            }
        },
        {
            "@type": "Question",
            "name": "Is AutoGen still used for AI agent development in 2026?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "No. AutoGen is now in maintenance mode and will not receive new features or enhancements. Microsoft has officially confirmed it is community-managed going forward. New projects should use Microsoft Agent Framework instead."
            }
        }
    ]
}

SCHEMA_BREADCRUMB = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://2193824842-spec.github.io/ai-pulse/"},
        {"@type": "ListItem", "position": 2, "name": "Model Comparison", "item": "https://2193824842-spec.github.io/ai-pulse/blog.html?category=Model-Comparison"},
        {"@type": "ListItem", "position": 3, "name": TITLE}
    ]
}


def build_schema_json_ld():
    schemas = [SCHEMA_ARTICLE, SCHEMA_FAQ, SCHEMA_BREADCRUMB]
    return "\n".join(
        f'<script type="application/ld+json">\n{json.dumps(s, ensure_ascii=False, indent=2)}\n</script>'
        for s in schemas
    )


def md_to_html(md_text):
    """Convert markdown to HTML with table and fenced code support."""
    extensions = ['tables', 'fenced_code', 'nl2br', 'attr_list']
    try:
        html = md_lib.markdown(md_text, extensions=extensions)
    except Exception:
        html = md_lib.markdown(md_text, extensions=['tables', 'fenced_code'])
    return html


def build_tags_html(tags):
    return "\n".join(f'<span class="tag">{t}</span>' for t in tags)


def build_breadcrumb_nav():
    return (
        '<ol class="breadcrumb-list">'
        '<li><a href="/ai-pulse/">Home</a></li>'
        '<li><a href="/ai-pulse/blog.html?category=Model-Comparison">Model Comparison</a></li>'
        f'<li>{TITLE}</li>'
        '</ol>'
    )


def build_level_badge(level):
    return f'<span class="level-badge level-{level.lower()}">{level}</span>'


def format_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return date_str


def read_markdown_body(md_path):
    """Read markdown file and strip front-matter metadata lines."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remove the first H1 title (it's in the template)
    content = re.sub(r'^# .+\n', '', content, count=1)
    
    # Remove front-matter bold lines like **Excerpt:**, **Slug:**, etc.
    content = re.sub(r'^\*\*(Excerpt|Slug|Category|Tags|Level|Target Audience|Date):\*\*.*\n', '', content, flags=re.MULTILINE)
    
    # Remove leading/trailing horizontal rules that were separators
    content = content.strip()
    if content.startswith('---'):
        content = content[3:].strip()
    
    return content


def generate_html():
    # Read template
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Read and convert article body
    md_body = read_markdown_body(ARTICLE_MD)
    article_html = md_to_html(md_body)
    
    # Build schema
    schema_json_ld = build_schema_json_ld()
    
    # Build tags HTML
    tags_html = build_tags_html(TAGS)
    
    # Build breadcrumb
    breadcrumb_nav = build_breadcrumb_nav()
    
    # Build level badge
    level_badge = build_level_badge(LEVEL)
    
    # Format date
    date_formatted = format_date(DATE)
    
    # Replace template placeholders
    html = template
    html = html.replace("{{TITLE}}", TITLE)
    html = html.replace("{{DESCRIPTION}}", EXCERPT)
    html = html.replace("{{CANONICAL_URL}}", CANONICAL_URL)
    html = html.replace("{{SLUG}}", SLUG)
    html = html.replace("{{OG_TITLE}}", OG_TITLE)
    html = html.replace("{{OG_DESCRIPTION}}", OG_DESCRIPTION)
    html = html.replace("{{OG_IMAGE}}", OG_IMAGE)
    html = html.replace("{{DATE_ISO}}", DATE)
    html = html.replace("{{DATE}}", date_formatted)
    html = html.replace("{{TAG_LIST}}", ",".join(TAGS))
    html = html.replace("{{SCHEMA_JSON_LD}}", schema_json_ld)
    html = html.replace("{{COVER_IMAGE}}", COVER_IMAGE)
    html = html.replace("{{LEVEL_BADGE}}", level_badge)
    html = html.replace("{{TAGS}}", tags_html)
    html = html.replace("{{CONTENT}}", article_html)
    html = html.replace("{{BREADCRUMB_NAV}}", breadcrumb_nav)
    
    return html


def update_index_json():
    """Add article entry to index.json."""
    with open(INDEX_JSON, "r", encoding="utf-8") as f:
        posts = json.load(f)
    
    # Check for duplicate
    existing_slugs = [p["slug"] for p in posts]
    if SLUG in existing_slugs:
        print(f"WARNING: Slug '{SLUG}' already exists in index.json, skipping update")
        return
    
    new_entry = {
        "slug": SLUG,
        "title": TITLE,
        "excerpt": EXCERPT,
        "date": DATE,
        "category": CATEGORY,
        "level": LEVEL,
        "tags": TAGS,
        "word_count": 1850,
        "view_count": 0,
        "cover_image": COVER_IMAGE,
        "featured": False,
        "target_audience": TARGET_AUDIENCE
    }
    
    # Insert at beginning (newest first)
    posts.insert(0, new_entry)
    
    with open(INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    
    print(f"Updated index.json with '{SLUG}'")


def main():
    print(f"Publishing article: {SLUG}")
    
    # Generate HTML
    html = generate_html()
    
    # Write HTML file
    out_path = os.path.join(POSTS_DIR, f"{SLUG}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Written: {out_path}")
    
    # Update index.json
    update_index_json()
    
    print("Done!")


if __name__ == "__main__":
    main()
