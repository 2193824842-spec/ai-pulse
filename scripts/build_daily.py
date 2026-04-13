"""
build_daily.py — 每日 AI 资讯生成脚本
=======================================
功能：
  1. 从多个 RSS 源抓取当天 AI 资讯
  2. Claude 筛选出最重要的 6 条，生成中英双语标题 + 一句导读
  3. 将当天内容注入 site/daily.html 和 site/zh/daily.html 顶部

用法：
  python build_daily.py                        # 正常运行，日期=今天
  python build_daily.py --date 2026-04-11      # 补跑指定日期
  python build_daily.py --dry-run              # 只打印，不写文件
"""

from __future__ import annotations
import os, re, sys, json, argparse, textwrap, requests
import feedparser
from openai import OpenAI
from datetime import datetime, timezone, timedelta
from pathlib import Path
from json_repair import repair_json
import yaml

sys.stdout.reconfigure(encoding="utf-8")

# ── 路径 ─────────────────────────────────────────────────────────────────────
_HERE     = Path(__file__).parent
_ROOT     = _HERE.parent
# CI 中脚本在 site/scripts/，_ROOT 就是 site 根目录
# 本地脚本在 seo-farm/scripts/，_ROOT 是 seo-farm/，site 在子目录
SITE_DIR  = Path(os.environ["SITE_DIR"]) if os.environ.get("SITE_DIR") else (
    _ROOT if ((_ROOT / "daily.html").exists()) else _ROOT / "site"
)
DAILY_EN  = SITE_DIR / "daily.html"
DAILY_ZH  = SITE_DIR / "zh" / "daily.html"

# ── 读取配置 ──────────────────────────────────────────────────────────────────
_cfg_path = _HERE / "config.yaml" if (_HERE / "config.yaml").exists() else _ROOT / "config.yaml"
with open(_cfg_path, encoding="utf-8") as f:
    _cfg = yaml.safe_load(f)

API_KEY      = _cfg["api"]["api_key"]
BASE_URL     = _cfg["api"]["base_url"] + "/v1"
MODEL        = _cfg["api"]["model_fast"]
SERPER_KEY   = _cfg["serper"]["api_key"]

# ── 参数 ──────────────────────────────────────────────────────────────────────
MAX_PER_FEED = 3
MAX_RAW      = 15
MAX_NEWS     = 6
CST          = timezone(timedelta(hours=8))

# ── RSS 源 ────────────────────────────────────────────────────────────────────
FEEDS = [
    {"url": "https://www.jiqizhixin.com/rss",                              "source": "机器之心", "lang": "zh"},
    {"url": "https://www.qbitai.com/feed",                                 "source": "量子位",   "lang": "zh"},
    {"url": "https://36kr.com/feed",                                       "source": "36氪",     "lang": "zh"},
    {"url": "https://openai.com/news/rss.xml",                             "source": "OpenAI",         "lang": "en"},
    {"url": "https://www.anthropic.com/rss.xml",                           "source": "Anthropic",      "lang": "en"},
    {"url": "https://deepmind.google/blog/rss.xml",                        "source": "Google DeepMind","lang": "en"},
    {"url": "https://huggingface.co/blog/feed.xml",                        "source": "Hugging Face",   "lang": "en"},
    {"url": "https://ai.meta.com/blog/feed/",                              "source": "Meta AI",        "lang": "en"},
    {"url": "https://www.technologyreview.com/feed/",                      "source": "MIT Tech Review","lang": "en"},
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/","source": "TechCrunch AI", "lang": "en"},
    {"url": "https://venturebeat.com/category/ai/feed/",                   "source": "VentureBeat AI", "lang": "en"},
]

TAG_LABELS_ZH = {"model": "大模型", "product": "产品", "research": "研究", "industry": "行业"}
TAG_LABELS_EN = {"model": "Model",  "product": "Product", "research": "Research", "industry": "Industry"}


# ════════════════════════════════════════════════════════════════════════════
# Step 1: 抓取 RSS
# ════════════════════════════════════════════════════════════════════════════
FALLBACK_IMG = "/ai-pulse/favicon.svg"

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()

def _extract_rss_image(entry) -> str:
    """从 RSS entry 提取图片 URL"""
    # media:content
    for m in entry.get("media_content", []):
        url = m.get("url", "")
        if url and url.startswith("http"):
            return url
    # media:thumbnail
    for m in entry.get("media_thumbnail", []):
        url = m.get("url", "")
        if url and url.startswith("http"):
            return url
    # enclosure
    for enc in entry.get("enclosures", []):
        if enc.get("type", "").startswith("image/"):
            return enc.get("href", "")
    # og:image in summary HTML
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', entry.get("summary", ""))
    if m:
        return m.group(1)
    return ""
    return re.sub(r"<[^>]+>", "", text).strip()

def fetch_news() -> list[dict]:
    articles = []
    for feed_cfg in FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
            count = 0
            for entry in feed.entries:
                if count >= MAX_PER_FEED:
                    break
                title = entry.get("title", "").strip()
                if not title:
                    continue
                summary = _strip_html(entry.get("summary", entry.get("description", "")))
                articles.append({
                    "title":   title,
                    "summary": summary[:300],
                    "source":  feed_cfg["source"],
                    "link":    entry.get("link", ""),
                    "image":   _extract_rss_image(entry),
                })
                count += 1
            print(f"  ✓ {feed_cfg['source']}: {count} 条")
        except Exception as e:
            print(f"  ✗ {feed_cfg['source']} 失败: {e}")
    return articles


# ════════════════════════════════════════════════════════════════════════════
# Step 1b: Serper 按日期搜索（补跑历史日期用）
# ════════════════════════════════════════════════════════════════════════════
SERPER_QUERIES = [
    "AI artificial intelligence news",
    "大模型 AI 新闻",
    "OpenAI Anthropic Google DeepMind news",
]

def fetch_news_by_date(date_str: str) -> list[dict]:
    """用 Serper 搜索指定日期的 AI 新闻"""
    # 计算 Serper tbs 参数：cdr:1,cd_min:MM/DD/YYYY,cd_max:MM/DD/YYYY
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    date_fmt = dt.strftime("%-m/%-d/%Y") if sys.platform != "win32" else dt.strftime("%#m/%#d/%Y")
    tbs = f"cdr:1,cd_min:{date_fmt},cd_max:{date_fmt}"

    articles = []
    seen_links = set()

    for query in SERPER_QUERIES:
        try:
            resp = requests.post(
                "https://google.serper.dev/news",
                headers={"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"},
                json={"q": query, "tbs": tbs, "num": 10},
                timeout=15,
            )
            resp.raise_for_status()
            results = resp.json().get("news", [])
            for r in results:
                link = r.get("link", "")
                if not link or link in seen_links:
                    continue
                seen_links.add(link)
                articles.append({
                    "title":   r.get("title", "").strip(),
                    "summary": r.get("snippet", "")[:300],
                    "source":  r.get("source", ""),
                    "link":    link,
                    "image":   r.get("imageUrl", ""),
                })
            print(f"  ✓ Serper [{query[:20]}]: {len(results)} 条")
        except Exception as e:
            print(f"  ✗ Serper [{query[:20]}] 失败: {e}")

    return articles


# ════════════════════════════════════════════════════════════════════════════
# Step 2: 去重
# ════════════════════════════════════════════════════════════════════════════
def deduplicate(articles: list[dict]) -> list[dict]:
    seen, result = set(), []
    for a in articles:
        key = re.sub(r"[\s\W_]+", "", a["title"]).lower()
        if key not in seen:
            seen.add(key)
            result.append(a)
    return result


# ════════════════════════════════════════════════════════════════════════════
# Step 3: Claude 筛选 + 双语 title/desc
# ════════════════════════════════════════════════════════════════════════════
def _call(client, prompt: str, max_tokens: int) -> str:
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ✗ API 调用失败: {e}")
        return ""

def _parse_json_array(raw: str) -> list:
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        return []
    try:
        return json.loads(repair_json(m.group()))
    except Exception:
        return []

def process(articles: list[dict]) -> list[dict]:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    pool = articles[:MAX_RAW]

    # ── A: 筛选 ──────────────────────────────────────────────────────────────
    articles_text = "\n\n".join([
        f"[{i+1}] 来源:{a['source']}\n标题:{a['title']}\n摘要:{a['summary'][:150]}"
        for i, a in enumerate(pool)
    ])
    select_prompt = f"""从以下 {len(pool)} 条 AI 资讯中筛选最重要的 {MAX_NEWS} 条。
优先级：新模型发布 > 重要产品上线 > 学术突破 > 行业大事件。排除营销软文和重复事件。

输出 JSON 数组，每条只需：
[{{"index": 1, "tag": "model"}}]
tag 从 model/product/research/industry 选一个。

资讯列表：
{articles_text}"""

    print("  [A] 筛选中...")
    selected_meta = _parse_json_array(_call(client, select_prompt, 400))
    if not selected_meta:
        print("  ✗ 筛选失败")
        return []

    # 兼容嵌套数组 [[...]] 的情况
    if selected_meta and isinstance(selected_meta[0], list):
        selected_meta = selected_meta[0]

    selected = []
    for m in selected_meta:
        if not isinstance(m, dict):
            continue
        idx = m.get("index", 0)
        if 1 <= idx <= len(pool):
            a = dict(pool[idx - 1])
            a["tag"] = m.get("tag", "industry")
            selected.append(a)

    # ── B: 双语 title + desc ──────────────────────────────────────────────────
    items_text = "\n\n".join([
        f"[{i+1}] 来源:{a['source']} tag:{a['tag']}\n标题:{a['title']}\n摘要:{a['summary'][:200]}"
        for i, a in enumerate(selected)
    ])
    write_prompt = f"""为以下 {len(selected)} 条 AI 资讯生成中英双语标题和一句导读。

要求：
- title_zh：中文标题 ≤20字
- desc_zh：中文导读 30-60字，点出核心事件
- title_en：英文标题 ≤15词
- desc_en：英文导读 20-50词

输出 JSON 数组，顺序与输入一致：
[
  {{"title_zh":"...","desc_zh":"...","title_en":"...","desc_en":"..."}}
]

资讯列表：
{items_text}"""

    print("  [B] 生成双语内容...")
    written = _parse_json_array(_call(client, write_prompt, 1200))

    results = []
    for i, a in enumerate(selected):
        w = written[i] if i < len(written) else {}
        results.append({
            "tag":      a["tag"],
            "source":   a["source"],
            "url":      a["link"],
            "image":    a.get("image", ""),
            "title_zh": w.get("title_zh", a["title"]),
            "desc_zh":  w.get("desc_zh", ""),
            "title_en": w.get("title_en", a["title"]),
            "desc_en":  w.get("desc_en", ""),
        })

    return results


# ════════════════════════════════════════════════════════════════════════════
# Step 4: 生成 HTML 片段并注入
# ════════════════════════════════════════════════════════════════════════════
def _favicon_url(url: str) -> str:
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).hostname or ""
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    except Exception:
        return FALLBACK_IMG


def _item_html_en(item: dict) -> str:
    tag   = item["tag"]
    label = TAG_LABELS_EN.get(tag, tag.capitalize())
    url   = item["url"] or "#"
    img   = item.get("image") or ""
    favicon = _favicon_url(url)
    img_src  = img if img else favicon
    onerror  = f"this.src='{favicon}'"
    return textwrap.dedent(f"""\
      <div class="daily-item">
        <div class="daily-item-body">
          <div class="daily-item-meta">
            <span class="daily-tag {tag}">{label}</span>
            <span class="daily-source">{item['source']}</span>
          </div>
          <div class="daily-item-title"><a href="{url}" target="_blank" rel="noopener">{item['title_en']}</a></div>
          <div class="daily-item-desc">{item['desc_en']}</div>
        </div>
        <a href="{url}" target="_blank" rel="noopener" class="daily-item-img-wrap">
          <img src="{img_src}" alt="{item['title_en']}" loading="lazy" onerror="{onerror}" />
        </a>
      </div>""")

def _item_html_zh(item: dict) -> str:
    tag   = item["tag"]
    label = TAG_LABELS_ZH.get(tag, tag)
    url   = item["url"] or "#"
    img   = item.get("image") or ""
    favicon = _favicon_url(url)
    img_src  = img if img else favicon
    onerror  = f"this.src='{favicon}'"
    return textwrap.dedent(f"""\
      <div class="daily-item">
        <div class="daily-item-body">
          <div class="daily-item-meta">
            <span class="daily-tag {tag}">{label}</span>
            <span class="daily-source">{item['source']}</span>
          </div>
          <div class="daily-item-title"><a href="{url}" target="_blank" rel="noopener">{item['title_zh']}</a></div>
          <div class="daily-item-desc">{item['desc_zh']}</div>
        </div>
        <a href="{url}" target="_blank" rel="noopener" class="daily-item-img-wrap">
          <img src="{img_src}" alt="{item['title_zh']}" loading="lazy" onerror="{onerror}" />
        </a>
      </div>""")

def _build_day_block_en(date_str: str, items: list[dict]) -> str:
    items_html = "\n".join(_item_html_en(i) for i in items)
    return textwrap.dedent(f"""\
    <div class="daily-day" id="day-{date_str}">
      <div class="daily-day-header">
        <span class="daily-day-date">{date_str}</span>
        <div class="daily-day-line"></div>
      </div>
      <div class="daily-items">
{items_html}
      </div>
    </div>""")

def _build_day_block_zh(date_str: str, items: list[dict]) -> str:
    items_html = "\n".join(_item_html_zh(i) for i in items)
    return textwrap.dedent(f"""\
    <div class="daily-day" id="day-{date_str}">
      <div class="daily-day-header">
        <span class="daily-day-date">{date_str}</span>
        <div class="daily-day-line"></div>
      </div>
      <div class="daily-items">
{items_html}
      </div>
    </div>""")

def inject(html_path: Path, block: str, dry_run: bool = False):
    marker = "<!-- DAILY_FEED_START -->"
    content = html_path.read_text(encoding="utf-8")
    if marker not in content:
        print(f"  ✗ 未找到注入标记: {html_path}")
        return
    new_content = content.replace(marker, marker + "\n" + block)
    if dry_run:
        print(f"  [dry-run] 预览 {html_path.name}:\n{block[:400]}")
        return
    html_path.write_text(new_content, encoding="utf-8")
    print(f"  ✓ 已注入 {html_path}")


# ════════════════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--date", type=str, default=None, help="指定日期 YYYY-MM-DD，默认今天")
    args = parser.parse_args()

    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")  # 验证格式
            today = args.date
        except ValueError:
            print(f"❌ 日期格式错误，请用 YYYY-MM-DD，例如 2026-04-11")
            sys.exit(1)
    else:
        today = datetime.now(CST).strftime("%Y-%m-%d")

    print("=" * 50)
    print(f"  每日 AI 资讯  {today}")
    if args.dry_run:
        print("  [演习模式]")
    print("=" * 50)

    if args.date:
        print(f"\n📡 Step 1 · Serper 搜索 {today} 的新闻...")
        raw = fetch_news_by_date(today)
    else:
        print(f"\n📡 Step 1 · 抓取 RSS ({len(FEEDS)} 个源)...")
        raw = fetch_news()
    print(f"  → 共 {len(raw)} 条\n")

    print("🔍 Step 2 · 去重...")
    articles = deduplicate(raw)
    print(f"  → {len(articles)} 条\n")

    print("🤖 Step 3 · Claude 筛选 + 双语生成...")
    items = process(articles)
    if not items:
        print("⚠️  没有生成内容，退出")
        sys.exit(1)
    print(f"  → {len(items)} 条\n")

    print("💾 Step 4 · 注入页面...")
    block_en = _build_day_block_en(today, items)
    block_zh = _build_day_block_zh(today, items)
    inject(DAILY_EN, block_en, args.dry_run)
    inject(DAILY_ZH, block_zh, args.dry_run)

    if not args.dry_run:
        print("\n🚀 Step 5 · 推送到 GitHub Pages...")
        import subprocess
        cmds = [
            ["git", "-C", str(SITE_DIR), "add", "daily.html", "zh/daily.html"],
            ["git", "-C", str(SITE_DIR), "commit", "-m", f"daily: {today} AI news update"],
            ["git", "-C", str(SITE_DIR), "push"],
        ]
        for cmd in cmds:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  ✗ {' '.join(cmd[3:])}: {result.stderr.strip()}")
                break
            print(f"  ✓ {' '.join(cmd[3:])}")

    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
